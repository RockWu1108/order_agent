import json
from typing import Literal, List

from langchain_core.messages import AIMessage, ToolCall, BaseMessage, ToolMessage

from config import AZURE_OPENAI_DEPLOYMENT_NAME
from graph.tools.tools_definition import tool_map
from .state import AgentState


def create_agent_node(client, tools_for_openai):
    """建立一個代理節點，該節點封裝了與 Azure OpenAI 的互動邏輯。"""
    def agent_node(state: AgentState):
        """
        代理的核心節點，決定下一步是呼叫工具還是回覆使用者。
        """
        if not client or not AZURE_OPENAI_DEPLOYMENT_NAME:
            raise ValueError("Azure OpenAI client 或 AZURE_DEPLOYMENT_NAME 未設定。")

        # 將 LangChain 的訊息格式轉換為 OpenAI API 需要的字典格式
        api_messages = [msg.dict(exclude_none=True) for msg in state['messages']]

        # 呼叫 Azure OpenAI API
        response = client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT_NAME,
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
    return agent_node


# 【修改】將原本的 ToolNode 物件替換為一個功能完全相同的自訂函式節點
def tool_node(state: AgentState) -> dict:
    """
    這是一個自訂的工具執行節點。
    它會檢查最新的訊息是否包含工具呼叫，並使用 tool_map 來執行它們。
    """
    last_message = state['messages'][-1]

    # 確保最後一則訊息是 AIMessage 且有工具呼叫
    if not isinstance(last_message, AIMessage) or not last_message.tool_calls:
        return {}

    tool_invocations = last_message.tool_calls
    tool_outputs: List[BaseMessage] = []

    # 遍歷所有的工具呼叫請求
    for tool_call in tool_invocations:
        tool_name = tool_call['name']

        # 使用 tool_map 來查找對應的工具
        if tool_name in tool_map:
            tool_to_call = tool_map[tool_name]

            try:
                # 執行工具，並傳入參數
                output = tool_to_call.invoke(tool_call['args'])
                # 將結果格式化為 ToolMessage
                tool_outputs.append(ToolMessage(
                    content=str(output),
                    tool_call_id=tool_call['id']
                ))
            except Exception as e:
                # 如果工具執行出錯，也回傳錯誤訊息
                tool_outputs.append(ToolMessage(
                    content=f"Error executing tool {tool_name}: {e}",
                    tool_call_id=tool_call['id']
                ))
        else:
            # 如果找不到工具
            tool_outputs.append(ToolMessage(
                content=f"Tool '{tool_name}' not found.",
                tool_call_id=tool_call['id']
            ))

    # 將工具執行的結果回傳，以便加入到對話歷史中
    return {"messages": tool_outputs}


# 定義路由邏輯 (Routing Logic) - 這個函式維持原樣，不需修改
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