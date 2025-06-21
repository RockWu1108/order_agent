# graph/nodes.py

from langchain_core.messages import ToolMessage, HumanMessage, AIMessage
from graph.state import AgentState
from graph.tools.tools_definition import tool_node
from graph.prompt import agent_system_prompt  # 導入我們新的 Agent "大腦"
from utils.llm_config import llm
import json
from celery_worker import tally_and_notify_task
import dateparser
import re


# --- Node Functions ---

def call_model(state: AgentState):
    """
    主要的大腦節點。根據新的 System Prompt 和對話歷史來決定下一步行動。
    """
    # 使用我們在 prompt.py 中定義的新 Agent Prompt
    prompt = agent_system_prompt.invoke({"messages": state["messages"]})
    response = llm.invoke(prompt)
    # 將 LLM 的回應加入到 messages 列表，以便 LangGraph 繼續處理
    return {"messages": [response]}


def call_tool(state: AgentState):
    """
    通用的工具執行節點。
    注意：在我們的圖中，許多工具會被更專業的節點（如 provide_recommendations）處理，
    這個節點主要用於處理那些沒有專門節點的工具呼叫。
    """
    return tool_node(state)  # 我們直接使用 tools_definition.py 中定義的 ToolNode


def human_input_node(state: AgentState):
    """等待人類輸入的節點。圖會在此暫停。"""
    return {}


def finish_node(state: AgentState):
    """提供最終完成訊息的節點。"""
    last_message = state['messages'][-1].content
    ai_message = AIMessage(content=f"流程已完成！{last_message}")
    return {"messages": [ai_message]}


def provide_recommendations(state: AgentState):
    """
    專門用於搜尋餐廳並將結果以結構化 JSON 格式回傳給前端的節點。
    """
    last_message = state["messages"][-1]
    if not last_message.tool_calls:
        # 如果沒有工具呼叫，可能表示 LLM 判斷資訊不足，直接將其判斷回傳
        return {"messages": [AIMessage(content="我需要更多資訊才能為您搜尋，例如美食類型。")]}

    # 執行 search_Maps 工具
    tool_call = last_message.tool_calls[0]
    raw_tool_result = call_tool(state)["messages"][0].content

    # 將字串結果轉換為 Python 物件
    try:
        restaurants_data = json.loads(raw_tool_result)
    except json.JSONDecodeError:
        return {"messages": [AIMessage(content=f"搜尋時發生錯誤，無法解析結果：{raw_tool_result}")]}

    # 建立前端期望的結構化 JSON
    frontend_response = {
        "type": "restaurant_list",
        "data": restaurants_data
    }

    # 我們需要發送一個 ToolMessage 來記錄工具執行的原始結果，
    # 然後再發送一個包含結構化 JSON 的 AIMessage 讓前端解析。
    # AIMessage 的 content 本身就是一個 JSON 字串。
    updated_messages = [
        ToolMessage(content=raw_tool_result, tool_call_id=tool_call["id"]),
        AIMessage(content=json.dumps(frontend_response))
    ]

    return {"messages": updated_messages, "restaurants": restaurants_data}


def create_order_form(state: AgentState):
    """
    根據使用者選擇的餐廳和提供的資訊建立 Google 表單。
    """
    last_message = state["messages"][-1]
    user_input = last_message.content  # e.g., "我要訂xxx飲料店，下午2點截止填單"

    # --- 從使用者輸入中提取資訊 ---
    # 1. 提取餐廳名稱 (這部分也可以讓LLM做，但正則表達式更穩定)
    restaurant_match = re.search(r"(?:我要訂|我選這家:?)\s*([^，,]+)", user_input)
    selected_restaurant = restaurant_match.group(1).strip() if restaurant_match else state.get("selected_restaurant",
                                                                                               "未指定餐廳")

    # 2. 提取截止時間
    deadline_match = re.search(r"([今明後天]?\s*[上下中午晚]*\s*\d+[點時:]\d*[分]?半?)", user_input)
    deadline_str = deadline_match.group(1).strip() if deadline_match else "未指定時間"

    # 3. 提取菜單 (此處假設 Agent 已透過前一步骤獲取)
    # 在真實情境中，Agent 會先問「好的，請提供菜單」
    # 為了簡化模擬，我們假設使用者會在下句話提供，或我們使用預設值
    menu_items = state.get("menu", ["經典紅茶", "珍珠奶茶", "水果茶"])
    title = f"{selected_restaurant} 訂購單"

    # --- 呼叫 Google Form 工具 ---
    # 我們需要模擬一個 ToolCall 來呼叫 'create_google_form'
    tool_input = {
        "title": title,
        "description": f"訂購 '{selected_restaurant}' 的美味餐點！截止時間：{deadline_str}",
        "menu_items": menu_items
    }

    # 手動模擬一個 ToolNode 的呼叫
    action = {"messages": [
        AIMessage(content="", tool_calls=[{"name": "create_google_form", "args": tool_input, "id": "form_call"}])]}
    form_result_str = call_tool(action)["messages"][0].content

    try:
        form_result = json.loads(form_result_str)
        form_url = form_result.get("form_url")
        sheet_url = form_result.get("sheet_url")

        if not form_url:
            raise ValueError("回傳的 JSON 中缺少 form_url")

    except (json.JSONDecodeError, ValueError) as e:
        error_message = f"建立Google表單失敗: {e}。收到的內容：{form_result_str}"
        return {"messages": [AIMessage(content=error_message)]}

    # --- 準備給前端的結構化回應 ---
    frontend_response = {
        "type": "form_created",
        "data": {
            "form_url": form_url,
            "sheet_url": sheet_url,
            "message": f"我已經為您在 '{selected_restaurant}' 建立訂購表單！請分享以下連結給您的同事朋友們。"
        }
    }

    # 更新狀態並回傳
    return {
        "messages": [
            ToolMessage(content=form_result_str, tool_call_id="form_call"),
            AIMessage(content=json.dumps(frontend_response))
        ],
        "form_url": form_url,
        "sheet_url": sheet_url,
        "deadline": deadline_str,  # 將解析出的截止時間存入 state
        "title": title  # 將標題也存入 state
    }


def schedule_summary_task(state: AgentState):
    """
    排程 Celery 背景任務，以便在截止時間到時進行統計。
    """
    deadline_str = state.get('deadline')
    sheet_url = state.get('sheet_url')
    title = state.get('title')
    # 假設通知渠道來自設定檔或使用者輸入
    notification_channels = state.get('notification_channels', {"line_token": "YOUR_TOKEN", "emails": []})

    if not all([deadline_str, sheet_url, title]):
        return {"messages": [AIMessage(content="排程失敗，缺少截止時間、統計表單或標題。")]}

    # 使用 dateparser 將自然語言時間（如「今天下午5點」）轉換為 datetime 物件
    deadline_dt = dateparser.parse(deadline_str, settings={'PREFER_DATES_FROM': 'future', 'TIMEZONE': 'Asia/Taipei'})

    if not deadline_dt:
        return {"messages": [AIMessage(
            content=f"無法解析您提供的時間 '{deadline_str}'，請提供更明確的時間，例如 '今天下午5點' 或 '2025-06-22 17:00'。")]}

    # 使用 Celery 的 'eta' 參數來排程任務在指定時間執行
    tally_and_notify_task.apply_async(
        args=[sheet_url, title, notification_channels],
        eta=deadline_dt
    )

    message = f"好的！我已經設定在 {deadline_dt.strftime('%Y-%m-%d %H:%M')} 為您統計訂單，並將結果發送到指定的頻道。"
    return {"messages": [AIMessage(content=message)]}