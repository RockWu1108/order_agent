# graph/conditional_edges.py
from typing import Literal
from graph.state import AgentState
import logging


def master_router(state: AgentState) -> Literal["provide_recommendations", "create_order_form", "call_model", "finish"]:
    """
    根據 AgentState 中的資訊完整度來決定下一個節點。
    """
    logging.info("---EDGE: master_router---")

    # 檢查是否已滿足建立表單的條件
    # ✨ 變更：現在檢查 title, selected_restaurant, deadline, 和 organizer_email
    has_form_info = all([
        state.get("title"),
        state.get("selected_restaurant"),
        state.get("deadline"),
        state.get("organizer_email")
    ])
    is_form_created = bool(state.get("form_url"))

    if has_form_info and not is_form_created:
        logging.info("條件滿足：建立訂單。路由至 create_order_form。")
        return "create_order_form"

    # 檢查是否已滿足搜尋餐廳的條件
    has_search_info = bool(state.get("location") and state.get("food_type"))
    has_recommendations = bool(state.get("recommendations"))

    if has_search_info and not has_recommendations:
        logging.info("條件滿足：搜尋餐廳。路由至 provide_recommendations。")
        return "provide_recommendations"

    # 如果有表單且有截止時間，流程在此router中視為完成，後續由新路由處理
    if is_form_created:
        logging.info("表單已建立，主要流程結束。")
        return "finish"

    # 如果以上條件都不滿足，則讓 AI 出面與使用者對話
    logging.info("資訊不完整，讓 AI 詢問使用者。路由至 call_model。")
    return "call_model"


def route_after_form_creation(state: AgentState) -> Literal["schedule_task", "finish"]:
    """
    ✨ 變更：新的路由函式。在建立表單後，決定是否要安排摘要任務。
    """
    logging.info("---EDGE: route_after_form_creation---")
    if state.get("form_url") and state.get("deadline") and state.get("organizer_email"):
        logging.info("表單已建立且資訊完整，路由至 schedule_task。")
        return "schedule_task"
    else:
        logging.info("表單已建立但資訊不全，無法安排任務，結束流程。")
        return "finish"