# graph/conditional_edges.py

from typing import Literal
from graph.state import AgentState
import logging

# graph/conditional_edges.py
from typing import Literal
from graph.state import AgentState
import logging


def master_router(state: AgentState) -> Literal["provide_recommendations", "create_order_form", "call_model", "finish"]:
    """
    根據 AgentState 中的資訊完整度來決定下一個節點，實現程式主導的流程。
    """
    logging.info("---EDGE: master_router---")

    # 檢查是否已滿足搜尋餐廳的條件
    has_search_info = bool(state.get("location") and state.get("food_type"))
    has_recommendations = bool(state.get("recommendations"))

    if has_search_info and not has_recommendations:
        logging.info("條件滿足：搜尋餐廳。路由至 provide_recommendations。")
        return "provide_recommendations"

    # 檢查是否已滿足建立表單的條件
    has_form_info = bool(state.get("selected_restaurant") and state.get("title") and state.get("deadline"))
    is_form_created = bool(state.get("form_url"))

    if has_form_info and not is_form_created:
        logging.info("條件滿足：建立訂單。路由至 create_order_form。")
        return "create_order_form"

    # 如果有表單且有截止時間，可以增加路由到 schedule_task 的邏輯
    if is_form_created and state.get("deadline"):
        # 在這裡可以添加 "schedule_task" 的返回，並在 graph.py 中定義
        # 為簡化，我們先讓它結束流程
        logging.info("流程完成。")
        return "finish"

    # 如果以上條件都不滿足，則讓 AI 出面與使用者對話
    logging.info("資訊不完整，讓 AI 詢問使用者。路由至 call_model。")
    return "call_model"

def route_to_recommendations(state: AgentState) -> Literal["get_menu", "human"]:
    """
    這個函式在提供推薦後，用來決定下一步。
    (在目前的簡化流程中未使用，但予以保留)
    """
    last_human_message = ""
    for message in reversed(state['messages']):
        if message.type == 'human':
            last_human_message = message.content
            break

    if "menu" in last_human_message.lower() or "菜單" in last_human_message:
        return "get_menu"
    return "human"


def route_after_form_creation(state: AgentState) -> Literal["schedule_task", "end"]:
    """
    在建立表單後，決定是否要安排摘要任務。
    """
    if state.get("form_url") and state.get("deadline"):
        return "schedule_task"
    else:
        return "end"