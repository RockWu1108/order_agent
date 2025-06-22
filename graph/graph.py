from langgraph.graph import StateGraph, END
from graph.state import AgentState
from graph.nodes import (
    call_model,
    call_tool,
    human_input_node,
    provide_recommendations,
    create_order_form,
    schedule_summary_task,
    finish_node,
)
from .conditional_edges import (
    master_router,  # 引用新的中央路由器
    route_after_form_creation
)

# --- Graph Definition ---
# This is where we wire up the nodes and edges to create the application logic.

builder = StateGraph(AgentState)

# 1. Define the Nodes
builder.add_node("agent", call_model)
builder.add_node("action", call_tool)
builder.add_node("human", human_input_node) # 讓流程暫停，等待使用者輸入的節點
builder.add_node("recommend_restaurants", provide_recommendations)
builder.add_node("create_order_form", create_order_form)
builder.add_node("schedule_summary_task", schedule_summary_task)
builder.add_node("finish", finish_node)

# 2. Set the Entry Point
builder.set_entry_point("agent")

# 3. Define the Edges

# 從 agent 節點出發，只使用 master_router 這一個統一的條件判斷
builder.add_conditional_edges(
    "agent",
    master_router,
    {
        "action": "action",
        "recommend": "recommend_restaurants",
        "create_form": "create_order_form",
        "human": "human",  # 當需要使用者輸入時，流程會導向 human 節點並暫停
        "end": END,
    },
)

# 執行工具後，回到 agent 重新思考
builder.add_edge("action", "agent")

# 提供推薦後，流程應暫停，等待使用者從列表中選擇
builder.add_edge("recommend_restaurants", "human")

# 建立訂單後，進行下一步判斷 (安排摘要任務或結束)
builder.add_conditional_edges(
    "create_order_form",
    route_after_form_creation,
    {
        "schedule_task": "schedule_summary_task",
        "end": "finish"
    }
)

# 安排任務後，結束流程
builder.add_edge("schedule_summary_task", "finish")
