from langgraph.graph import StateGraph, END
from .state import AgentState
from .nodes import create_agent_node, tool_node, should_continue

def create_graph(client, tools_for_openai):
    """建立 LangGraph 應用"""
    workflow = StateGraph(AgentState)

    # 建立帶有 client 和 tools 的 agent_node
    agent_node = create_agent_node(client, tools_for_openai)

    # 新增代理節點和工具節點
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tool_node)

    # 設定進入點
    workflow.set_entry_point("agent")

    # 設定條件式邊緣
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "__end__": END,
        }
    )

    # 新增從工具節點到代理節點的邊緣
    workflow.add_edge("tools", "agent")

    # 編譯圖
    app_graph = workflow.compile()
    print("✅ LangGraph 流程圖已成功編譯。")
    return app_graph
