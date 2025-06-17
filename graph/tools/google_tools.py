from typing import List, Dict
from langchain_core.tools import tool

@tool
def search_restaurants_tool(query: str) -> List[Dict]:
    """
    當使用者想要尋找餐廳時使用此工具。提供詳細的餐廳資訊。
    Use this tool when a user wants to search for restaurants. Provides detailed information.
    """
    print(f"🔧 [Google 工具] 模擬搜尋: '{query}'")
    # 這裡應放置實際的 Google Places API 呼叫邏輯
    return [
        {"id": "ChIJN1t_tDeuEmsRUsoyG83frY4", "name": "鼎泰豐", "rating": 4.5, "address": "信義路二段194號", "open_now": True},
        {"id": "ChIJxWJ_tDeuEmsR_t2fG83frY4", "name": "高記", "rating": 4.2, "address": "永康街1號", "open_now": False},
    ]

@tool
def create_group_order_tool(restaurant_name: str, deadline: str) -> Dict:
    """
    為指定的餐廳建立一個揪團 Google 表單，並設定截止時間。
    Use this tool to create a Google Form for a group order for a specific restaurant and set a deadline.
    """
    print(f"🔧 [Google 工具] 模擬為 '{restaurant_name}' 建立表單，截止於 {deadline}...")
    # 這裡應放置實際的 Google Forms/Sheets API 呼叫邏輯
    return {"form_url": "https://docs.google.com/forms/d/e/...", "sheet_id": "1aBcDe..."}

