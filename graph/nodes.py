# graph/nodes.py

from langchain_core.messages import ToolMessage, HumanMessage, AIMessage
from graph.state import AgentState
from graph.tools.tools_definition import tool_node, tools
from graph.prompt import agent_system_prompt, state_update_prompt,parser
from utils.llm_config import llm
import json
from celery_worker import tally_and_notify_task
import dateparser
import re
import logging


def format_chat_history(chat_history: list) -> str:
    """
    一個輔助函式，將 LangChain 的 message 物件列表格式化為單一的字串。
    """
    history_str = ""
    for msg in chat_history:
        if isinstance(msg, HumanMessage):
            history_str += f"人類: {msg.content}\n"
        elif isinstance(msg, AIMessage):
            history_str += f"AI: {msg.content}\n"
    return history_str


def update_state_node(state: AgentState) -> dict:
    """
    (新節點) 在每次使用者輸入後，呼叫 LLM 解析並更新狀態。
    """
    logging.info("---NODE: update_state_node---")
    user_input = state["messages"][-1].content

    chain = state_update_prompt | llm | parser
    extracted_data = chain.invoke({"input": user_input})

    update_data = {k: v for k, v in extracted_data.items() if v}

    if update_data:
        logging.info(f"從使用者輸入中提取並更新狀態: {update_data}")
        return update_data

    return {}
# --- Node Functions ---

def call_model(state: AgentState):
    """
    (已簡化) AI Agent 節點，現在只專注於在資訊不足時向使用者提問。
    """
    logging.info("---NODE: call_model---")
    chat_history = format_chat_history(state["messages"][:-1])
    user_input = state["messages"][-1].content

    prompt_str = agent_system_prompt.format(
        chat_history=chat_history,
        input=user_input
    )
    response = llm.invoke(prompt_str)
    return {"messages": [response]}

def call_tool(state: AgentState):
    """通用的工具執行節點。"""
    logging.info("---NODE: call_tool---")
    return tool_node.invoke(state)


def human_input_node(state: AgentState):
    """等待人類輸入的節點。圖會在此暫停。"""
    logging.info("---NODE: human_input_node (Pausing for input)---")
    return {}


def finish_node(state: AgentState):
    """提供最終完成訊息的節點。"""
    logging.info("---NODE: finish_node---")
    return {"messages": [AIMessage(content="流程已全部完成，感謝您的使用！")]}

def provide_recommendations(state: AgentState):
    """
    (已修改) 不再依賴 AI 的工具呼叫，而是主動從 state 中獲取資訊來執行工具。
    """
    logging.info("---NODE: provide_recommendations---")
    location = state.get("location")
    food_type = state.get("food_type")
    query = f"{location}的{food_type}"
    logging.info(f"從 state 建構 query: {query}")

    tool_call_id = "manual_search_call"
    tool_output = tool_node.invoke(
        {"messages": [
            AIMessage(content="", tool_calls=[{"name": "search_Maps", "args": {"query": query}, "id": tool_call_id}])]}
    )
    raw_tool_result = tool_output["messages"][-1].content
    logging.info(f"Raw tool result (first 100 chars): {raw_tool_result[:100]}")

    try:
        restaurants_data = json.loads(raw_tool_result)
    except json.JSONDecodeError:
        logging.error(f"Failed to parse JSON from tool result: {raw_tool_result}")
        return {"messages": [AIMessage(content="搜尋時發生錯誤，無法解析結果。")]}

    frontend_response = {"type": "restaurant_list", "data": restaurants_data}
    logging.info(f"Prepared structured response for frontend.")

    return {
        "messages": [
            # --- ✨ 關鍵修正 ✨ ---
            # 使用我們自己定義的 `tool_call_id` 變數
            ToolMessage(content=raw_tool_result, tool_call_id=tool_call_id),
            AIMessage(content=json.dumps(frontend_response, ensure_ascii=False))
        ],
        "recommendations": restaurants_data
    }

# (create_order_form 和 schedule_summary_task 函式維持不變，此處省略以保持簡潔)
def create_order_form(state: AgentState):
    """
    (已修改) 同樣改為主動從 state 獲取資訊來建立表單。
    """
    logging.info("---NODE: create_order_form---")
    title = state.get("title")
    selected_restaurant = state.get("selected_restaurant")
    deadline = state.get("deadline")
    menu_items = ["紅茶", "綠茶", "奶茶"]
    description = f"訂購 '{selected_restaurant}' 的美味餐點！截止時間：{deadline}"
    logging.info(f"從 state 建構表單資訊: Title={title}, Restaurant={selected_restaurant}, Deadline={deadline}")

    tool_call_id = "manual_form_call"
    tool_output = tool_node.invoke(
        {"messages": [AIMessage(content="", tool_calls=[{"name": "create_google_form",
                                                         "args": {"title": title, "description": description,
                                                                  "menu_items": menu_items}, "id": tool_call_id}])]}
    )
    form_result_str = tool_output["messages"][-1].content

    try:
        form_result = json.loads(form_result_str)
        form_url = form_result.get("form_url")
        sheet_url = form_result.get("sheet_url")
        if not form_url: raise ValueError("回傳的 JSON 中缺少 form_url")
    except (json.JSONDecodeError, ValueError) as e:
        error_message = f"建立Google表單失敗: {e}。收到的內容：{form_result_str}"
        logging.error(error_message)
        return {"messages": [AIMessage(content=error_message)]}

    frontend_response = {"type": "form_created",
                         "data": {"form_url": form_url, "sheet_url": sheet_url, "message": f"訂單已建立！"}}
    logging.info(f"Form created successfully.")

    return {
        "messages": [
            # --- ✨ 關鍵修正 ✨ ---
            # 使用我們自己定義的 `tool_call_id` 變數
            ToolMessage(content=form_result_str, tool_call_id=tool_call_id),
            AIMessage(content=json.dumps(frontend_response, ensure_ascii=False))
        ],
        "form_url": form_url, "sheet_url": sheet_url
    }

def schedule_summary_task(state: AgentState):
    logging.info("---NODE: schedule_summary_task---")
    deadline_str = state.get('deadline')
    sheet_url = state.get('sheet_url')
    title = state.get('title')
    notification_channels = state.get('notification_channels', {"line_token": None, "emails": []})
    if not all([deadline_str, sheet_url, title]):
        logging.warning("Scheduling failed, missing deadline, sheet_url, or title.")
        return {"messages": [AIMessage(content="排程失敗，缺少截止時間、統計表單或標題。")]}
    deadline_dt = dateparser.parse(deadline_str, settings={'PREFER_DATES_FROM': 'future', 'TIMEZONE': 'Asia/Taipei'})
    if not deadline_dt:
        return {"messages": [AIMessage(content=f"無法解析您提供的時間 '{deadline_str}'。")]}
    tally_and_notify_task.apply_async(args=[sheet_url, title, notification_channels], eta=deadline_dt)
    message = f"好的！我已經設定在 {deadline_dt.strftime('%Y-%m-%d %H:%M')} 為您統計訂單。"
    logging.info(message)
    return {"messages": [AIMessage(content=message)]}