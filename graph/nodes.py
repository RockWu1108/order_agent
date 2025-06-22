# graph/nodes.py

from langchain_core.messages import ToolMessage, HumanMessage, AIMessage
from graph.state import AgentState
from graph.tools.tools_definition import tool_node, tools
from graph.prompt import agent_system_prompt, state_update_prompt, parser
from utils.llm_config import llm
import json
from celery_worker import tally_and_notify_task
import dateparser
import logging


def format_chat_history(chat_history: list) -> str:
    """輔助函式，格式化對話歷史。"""
    history_str = ""
    for msg in chat_history:
        if isinstance(msg, HumanMessage):
            history_str += f"人類: {msg.content}\n"
        elif isinstance(msg, AIMessage):
            history_str += f"AI: {msg.content}\n"
    return history_str


def update_state_node(state: AgentState) -> dict:
    """在每次使用者輸入後，呼叫 LLM 解析並更新狀態。"""
    logging.info("---NODE: update_state_node---")
    if not state["messages"]:
        return {}

    user_input = state["messages"][-1].content
    chain = state_update_prompt | llm | parser

    # 從使用者輸入中提取資訊
    extracted_data = chain.invoke({"input": user_input})
    # 過濾掉值為 None 或空字串的鍵
    update_data = {k: v for k, v in extracted_data.items() if v}

    if update_data:
        logging.info(f"從使用者輸入中提取並更新狀態: {update_data}")
        return update_data

    return {}


def call_model(state: AgentState):
    """AI Agent 節點，專注於在資訊不足時向使用者提問。"""
    logging.info("---NODE: call_model---")
    chat_history = format_chat_history(state["messages"][:-1])
    user_input = state["messages"][-1].content

    prompt_str = agent_system_prompt.format(
        chat_history=chat_history,
        input=user_input
    )
    response = llm.invoke(prompt_str)
    return {"messages": [response]}


def provide_recommendations(state: AgentState):
    """主動從 state 中獲取資訊來執行餐廳搜尋工具。"""
    logging.info("---NODE: provide_recommendations---")
    location = state.get("location")
    food_type = state.get("food_type")

    if not location or not food_type:
        return {"messages": [AIMessage(content="我需要知道地點和美食類型才能為您推薦喔。")]}

    query = f"{location}的{food_type}"
    logging.info(f"從 state 建構 query: {query}")

    tool_call_id = "manual_search_call"
    # 直接呼叫工具節點
    tool_output = tool_node.invoke(
        {"messages": [
            AIMessage(content="", tool_calls=[{"name": "search_Maps", "args": {"query": query}, "id": tool_call_id}])]}
    )

    raw_tool_result = tool_output["messages"][-1].content
    logging.info(f"Raw tool result (first 150 chars): {raw_tool_result[:150]}")

    # ✨ 變更：強化JSON解析和錯誤處理
    try:
        restaurants_data = json.loads(raw_tool_result)
        if "error" in restaurants_data:
            raise ValueError(restaurants_data["error"])
    except (json.JSONDecodeError, ValueError) as e:
        logging.error(f"解析餐廳推薦結果時出錯: {e}. Raw result: {raw_tool_result}")
        error_message = f"搜尋時發生錯誤，無法解析結果: {e}"
        return {"messages": [AIMessage(content=error_message)]}

    # 準備給前端的結構化資料
    frontend_response = {"type": "restaurant_list", "data": restaurants_data}
    logging.info("已準備好給前端的結構化餐廳列表。")

    return {
        "messages": [
            ToolMessage(content=raw_tool_result, tool_call_id=tool_call_id),
            AIMessage(content=json.dumps(frontend_response, ensure_ascii=False))
        ],
        "recommendations": restaurants_data
    }


def create_order_form(state: AgentState):
    """主動從 state 獲取資訊來建立Google表單。"""
    logging.info("---NODE: create_order_form---")
    title = state.get("title")
    selected_restaurant = state.get("selected_restaurant")
    deadline = state.get("deadline")

    menu_items = ["紅茶", "綠茶", "奶茶", "烏龍茶"]
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
        if "error" in form_result:
            raise ValueError(form_result["error"])
        form_url = form_result.get("form_url")
        sheet_url = form_result.get("sheet_url")
        if not form_url or not sheet_url:
            raise ValueError("回傳的 JSON 中缺少 form_url 或 sheet_url")
    except (json.JSONDecodeError, ValueError) as e:
        error_message = f"建立Google表單失敗: {e}。收到的內容：{form_result_str}"
        logging.error(error_message)
        return {"messages": [AIMessage(content=error_message)]}

    # 準備給前端的訊息，其中包含了引導加入官方帳號的文字
    invitation_message = (
        f"您的訂單「{title}」已成功建立！\n\n"
        f"請分享此訂單連結給同事：\n{form_url}\n\n"
        f"為了接收後續的成團與餐點到貨通知，請務必先加入我們的 LINE 官方帳號！\n"
        f"[請在此貼上您的官方帳號加入連結或QR Code]"
    )

    # ✨ 變更：這裡不再直接發送 LINE 通知給管理者。
    # 而是將邀請訊息回傳給前端，讓管理者複製轉發。
    # 後續的通知將由 celery_worker 透過 broadcast_line_message 統一發送。
    logging.info("表單建立成功，準備將邀請訊息回傳給前端。")

    # 將最終的邀請訊息和結構化資料一起傳給前端
    final_message_content = {
        "type": "form_created_with_invitation",
        "data": {
            "form_url": form_url,
            "sheet_url": sheet_url,
            "message": invitation_message
        }
    }

    return {
        "messages": [
            ToolMessage(content=form_result_str, tool_call_id=tool_call_id),
            AIMessage(content=json.dumps(final_message_content, ensure_ascii=False))
        ],
        "form_url": form_url,
        "sheet_url": sheet_url
    }


def schedule_summary_task(state: AgentState):
    """✨ 變更：新增節點，用於安排 Celery 背景任務。"""
    logging.info("---NODE: schedule_summary_task---")
    deadline_str = state.get('deadline')
    sheet_url = state.get('sheet_url')
    title = state.get('title')
    organizer_email = state.get('organizer_email')

    if not all([deadline_str, sheet_url, title, organizer_email]):
        missing = [k for k, v in
                   {"截止時間": deadline_str, "統計表單": sheet_url, "標題": title, "Email": organizer_email}.items() if
                   not v]
        message = f"排程失敗，缺少以下資訊：{', '.join(missing)}。"
        logging.warning(message)
        return {"messages": [AIMessage(content=message)]}

    # 使用 dateparser 來解析多樣的時間格式
    deadline_dt = dateparser.parse(deadline_str, settings={'PREFER_DATES_FROM': 'future', 'TIMEZONE': 'Asia/Taipei'})
    if not deadline_dt:
        message = f"無法解析您提供的時間 '{deadline_str}'，請提供更明確的時間（例如：今天下午5點）。"
        return {"messages": [AIMessage(content=message)]}

    # 準備通知渠道
    notification_channels = {"emails": [organizer_email]}

    # 使用 apply_async 來設定 ETA (Estimated Time of Arrival)
    tally_and_notify_task.apply_async(
        args=[sheet_url, title, notification_channels],
        eta=deadline_dt
    )

    message = f"好的！我已經設定在 {deadline_dt.strftime('%Y-%m-%d %H:%M')} 為您統計「{title}」訂單，並會將結果寄到您的信箱。訂單連結已產生，您可以分享給同事了。"
    logging.info(message)
    return {"messages": [AIMessage(content=message)]}


def finish_node(state: AgentState):
    """提供最終完成訊息的節點。"""
    logging.info("---NODE: finish_node---")
    return {"messages": [AIMessage(content="流程已全部完成，感謝您的使用！如果您需要發起新的訂購，請隨時告訴我。")]}