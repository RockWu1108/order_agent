# graph/graph.py

from langgraph.graph import StateGraph, END
from .state import AgentState
from .nodes import (
    update_state_node,
    call_model,
    provide_recommendations,
    create_order_form,
    finish_node,
)
from .conditional_edges import master_router

# 建立圖
workflow = StateGraph(AgentState)

# 1. 定義所有節點
workflow.add_node("update_state", update_state_node)
workflow.add_node("agent", call_model)
workflow.add_node("recommend_restaurants", provide_recommendations)
workflow.add_node("create_order_form", create_order_form)
workflow.add_node("finish", finish_node)

# 2. 設定圖的進入點
workflow.set_entry_point("update_state")

# 3. 定義條件路由
# 關鍵修正：將路由的起始點從一個不存在的 "router" 節點，修正為 "update_state" 節點。
# 這表示在 update_state 完成後，會呼叫 master_router 函式來決定下一步去向。
workflow.add_conditional_edges(
    "update_state",
    master_router,
    {
        "provide_recommendations": "recommend_restaurants",
        "create_order_form": "create_order_form",
        "call_model": "agent",
        "finish": "finish" # 將 "finish" 導向我們定義的 finish_node
    }
)

# 4. 定義常規的邊（節點之間的固定路徑）
# 在我們的設計中，大部分節點執行完畢後，流程就結束了，等待下一次使用者輸入。
# 下一次輸入會再次觸發進入點 "update_state"，形成一個完整的對話循環。
workflow.add_edge("agent", END)
workflow.add_edge("recommend_restaurants", END)
workflow.add_edge("create_order_form", END)
workflow.add_edge("finish", END)

# 5. 編譯圖，使其成為可執行的物件
graph = workflow.compile()