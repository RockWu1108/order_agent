from langchain_core.messages import ToolMessage, HumanMessage, AIMessage
from graph.state import AgentState
# 修正 1：tool_executor 現在可以從修正後的 tools_definition.py 中正確導入
from graph.tools.tools_definition import tool_node as tool_executor
# 修正 2：從新建立的 prompts.py 中導入提示模板
from graph.prompt import recommendation_prompt, form_creation_prompt
# 修正 3：從新建立的 llm_config.py 中導入 llm 實例
from utils.llm_config import llm
import json
from celery_worker import tally_and_notify_task
from datetime import datetime
import dateparser


# --- Node Functions ---
# Each function represents a state or action in our graph.

def call_model(state: AgentState):
    """Invokes the large language model to decide the next action."""
    messages = state["messages"]
    response = llm.invoke(messages)
    return {"messages": [response]}


def call_tool(state: AgentState):
    """Executes a tool call and returns the output."""
    last_message = state["messages"][-1]
    tool_call = last_message.tool_calls[0]
    action = ToolMessage(
        content=tool_executor.invoke(tool_call),
        tool_call_id=tool_call["id"],
    )
    return {"messages": [action]}


def human_input_node(state: AgentState):
    """A placeholder node for when the graph needs to wait for human input."""
    # The graph pauses at this state. The next HumanMessage will resume the flow.
    return {}


def finish_node(state: AgentState):
    """A final node to provide a concluding message."""
    last_message = state['messages'][-1].content
    ai_message = AIMessage(content=f"流程已完成！{last_message}")
    return {"messages": [ai_message]}


def provide_recommendations(state: AgentState):
    """
    Calls the Google Maps tool and formats the results for the user.
    This node is a combination of a tool call and a model call.
    """
    # Get parameters from state
    location = state.get('location')
    food_type = state.get('food_type')

    if not location or not food_type:
        return {"messages": [AIMessage(content="我需要知道地點和美食類型才能幫您推薦喔。")]}

    # 1. Call the search tool directly
    search_query = f"{location} 的 {food_type}"
    tool_result = tool_executor.invoke({
        "tool": "search_Maps",
        "tool_input": {"query": search_query}
    })

    # 2. Use LLM to format the result nicely
    prompt = recommendation_prompt.format(context=tool_result)
    response = llm.invoke(prompt)

    # 3. Update state
    # We add the raw tool result and the formatted AI message to the history
    updated_messages = [
        ToolMessage(content=str(tool_result), tool_call_id="internal_search"),
        response
    ]

    # The response content itself should be a JSON string for the frontend
    return {"messages": updated_messages, "restaurants": tool_result}


def create_order_form(state: AgentState):
    """
    Creates a Google Form based on the selected restaurant and menu.
    """
    selected_restaurant = state.get('selected_restaurant')
    menu = state.get('menu')  # Assume menu is a simple text string for now
    title = state.get('title')

    if not all([selected_restaurant, menu, title]):
        return {"messages": [AIMessage(content="建立表單失敗，缺少餐廳、菜單或揪團標題。")]}

    # Use LLM to parse menu and create a structured list
    prompt = form_creation_prompt.format(menu=menu)
    llm_response = llm.invoke(prompt)

    try:
        # The LLM should return a JSON string representing the menu items
        menu_items = json.loads(llm_response.content)
    except json.JSONDecodeError:
        return {"messages": [AIMessage(content=f"無法解析菜單，請檢查格式。收到的內容：{llm_response.content}")]}

    # Call the Google Form creation tool
    form_result_str = tool_executor.invoke({
        "tool": "create_google_form",
        "tool_input": {
            "title": title,
            "description": f"訂購 '{selected_restaurant}' 的美味餐點！",
            "menu_items": menu_items
        }
    })

    # The tool returns a JSON string with "form_url" and "sheet_url"
    form_result = json.loads(form_result_str)
    form_url = form_result.get("form_url")
    sheet_url = form_result.get("sheet_url")

    if not form_url:
        return {"messages": [AIMessage(content=f"建立Google表單失敗: {form_result_str}")]}

    # Prepare a structured response for the frontend
    frontend_response = {
        "type": "form_created",
        "data": {
            "form_url": form_url,
            "sheet_url": sheet_url,
            "message": f"我已經為您在 '{selected_restaurant}' 建立訂購表單！請分享以下連結給您的朋友：\n{form_url}"
        }
    }

    # Update state
    return {
        "messages": [AIMessage(content=json.dumps(frontend_response))],
        "form_url": form_url,
        "sheet_url": sheet_url
    }


def schedule_summary_task(state: AgentState):
    """
    Schedules the Celery task to tally and notify at the deadline.
    """
    deadline_str = state.get('deadline')
    sheet_url = state.get('sheet_url')
    title = state.get('title')
    notification_channels = state.get('notification_channels', {})  # e.g., {"line_token": "...", "emails": ["..."]}

    if not all([deadline_str, sheet_url, title]):
        return {"messages": [AIMessage(content="排程失敗，缺少截止時間、統計表單或標題。")]}

    # Parse the deadline string into a datetime object
    # dateparser is very flexible with formats like "今天下午5點", "tomorrow 10am", "2025-06-21 17:00"
    deadline_dt = dateparser.parse(deadline_str, settings={'PREFER_DATES_FROM': 'future', 'TIMEZONE': 'Asia/Taipei'})

    if not deadline_dt:
        return {"messages": [AIMessage(content=f"無法解析您提供的時間 '{deadline_str}'，請提供更明確的時間。")]}

    # Schedule the task using Celery's 'eta' argument
    tally_and_notify_task.apply_async(
        args=[sheet_url, title, notification_channels],
        eta=deadline_dt
    )

    message = f"好的！我已經設定在 {deadline_dt.strftime('%Y-%m-%d %H:%M')} 為您統計訂單，並發送結果到指定的頻道。"
    return {"messages": [AIMessage(content=message)]}
