from typing import Literal
from graph.state import AgentState

def master_router(state: AgentState) -> Literal["action", "recommend", "create_form", "human", "end"]:
    """
    一個統一的路由器，作為 agent 節點之後唯一的決策點。
    """
    # 獲取模型最新的回應
    last_message = state["messages"][-1]

    # 情況一：如果模型決定呼叫工具
    if last_message.tool_calls:
        # 如果是建立訂單的工具
        if any(call.name == "create_order_form" for call in last_message.tool_calls):
            return "create_form"
        # 如果是其他工具 (例如 google_search)
        return "action"

    # 情況二：如果模型沒有呼叫工具，而是回覆文字
    else:
        # 檢查是否已收集到足夠資訊可以推薦餐廳
        # 並且尚未給出推薦
        if state.get("location") and state.get("food_type") and not state.get("recommendations"):
            return "recommend"

        # 在所有其他情況下，模型都是在向使用者提問
        # 因此我們應該暫停，等待使用者輸入
        return "human"


def route_to_recommendations(state: AgentState) -> Literal["get_menu", "human"]:
    """
    這個函式在提供推薦後，用來決定下一步。
    (在新的簡化流程中，這個函式目前不會被使用，但予以保留)
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
    if state.get("order_form_url"):
        return "schedule_task"
    else:
        # 如果表單URL不存在，說明建立失敗，直接結束
        return "end"

