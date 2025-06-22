# graph/state.py
from typing import TypedDict, Annotated, Any
import operator

class AgentState(TypedDict):
    messages: Annotated[list[Any], operator.add]
    location: str | None
    food_type: str | None
    recommendations: list[dict] | None
    selected_restaurant: str | None  # 新增
    title: str | None
    deadline: str | None
    form_url: str | None
    sheet_url: str | None