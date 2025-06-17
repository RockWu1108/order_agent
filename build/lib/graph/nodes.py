import json
from typing import Literal
from langchain_core.messages import AIMessage, ToolCall
from langgraph.prebuilt import ToolNode

from config import client, AZURE_DEPLOYMENT_NAME, tools_for_openai
from graph.tools.tools_definition import tool_executor # (已更新) 使用 tool_executor
from .state import AgentState

# 定義代理節點 (Agent Node)
def agent_node(state: AgentState):
    """
    代理的核心節點，決定下一步是呼叫工具還是回覆使用者。
    """
    if not client or not AZURE_DEPLOYMENT_NAME:
        raise ValueError("Azure OpenAI client 或 AZURE_DEPLOYMENT_NAME 未設定。")

    # 將 LangChain 的訊息格式轉換為 OpenAI API 需要的字典格式
    api_messages = [msg.dict(exclude_none=True) for msg in state['messages']]

    # 呼叫 Azure OpenAI API
    response = client.chat.completions.create(
        model=AZURE_DEPLOYMENT_NAME,
        messages=api_messages,
        tools=tools_for_openai,
        tool_choice="auto"
    )
    response_message = response.choices[0].message

    # 將 OpenAI 的回覆轉換為 LangChain 的 AIMessage 格式，以便 LangGraph 處理
    tool_calls = []
    if response_message.tool_calls:
        for tc in response_message.tool_calls:
            try:
                tool_calls.append(
                    ToolCall(
                        name=tc.function.name,
                        args=json.loads(tc.function.arguments),
                        id=tc.id
                    )
                )
            except json.JSONDecodeError:
                # 如果 LLM 產生的參數不是有效的 JSON，則跳過
                pass

    return {"messages": [AIMessage(content=response_message.content or "", tool_calls=tool_calls)]}


# (已更新) 定義工具節點，使用從 tools_definition 導入的 tool_executor
tool_node = ToolNode(tool_executor)


# 定義路由邏輯 (Routing Logic)
def should_continue(state: AgentState) -> Literal["tools", "__end__"]:
    """
    決定在代理節點之後的走向。
    如果最後一則訊息是 AI 發出的且包含工具呼叫，則走向工具節點。
    否則，結束流程。
    """
    last_message = state['messages'][-1]
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tools"
    return "__end__"

