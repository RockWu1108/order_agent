from typing import TypedDict, List, Annotated
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    """
    代理的狀態機，用一個訊息列表來追蹤整個對話和工具執行的歷史。

    Attributes:
        messages: 一個不斷累積的訊息列表。
                  使用 Annotated 和 lambda 來定義列表的合併方式是 `+` (相加)。
    """
    messages: Annotated[List[BaseMessage], lambda x, y: x + y]
