# graph/graph.py
from langgraph.graph import StateGraph, END
from .state import AgentState
from .nodes import (
    update_state_node,
    call_model,
    provide_recommendations,
    create_order_form,
    schedule_summary_task, # ✨ 變更：導入新節點
    finish_node,
)
from .conditional_edges import master_router, route_after_form_creation # ✨ 變更：導入新路由

# 建立圖
workflow = StateGraph(AgentState)

# 1. 定義所有節點
workflow.add_node("update_state", update_state_node)
workflow.add_node("agent", call_model)
workflow.add_node("recommend_restaurants", provide_recommendations)
workflow.add_node("create_order_form", create_order_form)
workflow.add_node("schedule_task", schedule_summary_task) # ✨ 變更：新增節點
workflow.add_node("finish", finish_node)

# 2. 設定圖的進入點
workflow.set_entry_point("update_state")

# 3. 定義主要的條件路由 (從 update_state 出發)
workflow.add_conditional_edges(
    "update_state",
    master_router,
    {
        "provide_recommendations": "recommend_restaurants",
        "create_order_form": "create_order_form",
        "call_model": "agent",
        "finish": "finish"
    }
)

# 4. ✨ 變更：定義表單建立後的條件路由
workflow.add_conditional_edges(
    "create_order_form",
    route_after_form_creation,
    {
        "schedule_task": "schedule_task",
        "finish": "finish"
    }
)


# 5. 定義常規的邊 (節點之間的固定路徑)
workflow.add_edge("agent", END)
workflow.add_edge("recommend_restaurants", END)
workflow.add_edge("schedule_task", END) # ✨ 變更：新節點完成後結束
workflow.add_edge("finish", END)

# 6. 編譯圖
graph = workflow.compile()