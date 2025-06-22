# graph/state.py
from typing import TypedDict, Annotated, Any, List
import operator

class AgentState(TypedDict):
    """
    定義了整個對話流程中需要追蹤的所有狀態。
    """
    # 對話歷史紀錄
    messages: Annotated[list[Any], operator.add]

    # 使用者意圖相關資訊
    location: str | None
    food_type: str | None
    title: str | None
    deadline: str | None
    organizer_email: str | None # ✨ 變更：新增此欄位來儲存使用者Email

    # 流程中間產物
    recommendations: list[dict] | None
    selected_restaurant: str | None

    # 流程最終產物
    form_url: str | None
    sheet_url: str | None