from langgraph.graph import StateGraph, END
from graph.state import AgentState
from graph.nodes import agent_node, tool_node, should_continue

# --- 建立新的 LangGraph 圖 ---
workflow = StateGraph(AgentState)

# 新增代理節點和工具節點
workflow.add_node("agent", agent_node)
workflow.add_node("tools", tool_node)

# 設定進入點
workflow.set_entry_point("agent")

# 設定條件式邊緣：代理節點執行完後，根據結果決定是呼叫工具還是結束
workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "tools": "tools", # 如果需要呼叫工具，就到 'tools' 節點
        "__end__": END,  # 如果不需要，就結束
    }
)

# 設定邊緣：工具節點執行完後，回到代理節點，讓它根據新資訊繼續思考
workflow.add_edge("tools", "agent")

# 編譯成可執行的應用
app_graph = workflow.compile()




print("✅ LangGraph 流程圖已成功編譯。")
