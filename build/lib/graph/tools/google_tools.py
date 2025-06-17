# graph/tools/google_tools.py

import googlemaps
from langchain_core.tools import tool
from typing import List, Dict

# (新增) 引入 Google API Client 相關函式庫
from google.oauth2 import service_account
from googleapiclient.discovery import build

from config import GOOGLE_API_KEY, OWNER_EMAIL

# --- search_restaurants_tool 維持不變 ---

if not GOOGLE_API_KEY:
    print("⚠️ GOOGLE_API_KEY not found. `search_restaurants_tool` will not work.")
    gmaps = None
else:
    gmaps = googlemaps.Client(key=GOOGLE_API_KEY)


@tool
def search_restaurants_tool(query: str, location: str = "25.0330,121.5654") -> List[Dict]:
    """
    當使用者想要尋找餐廳時使用此工具。提供詳細的餐廳資訊。
    需要提供搜尋關鍵字(query)和一個經緯度 "緯度,經度" (location) 來指定搜尋中心。
    """
    if not gmaps:
        return {"error": "Google Maps API client is not initialized. Check GOOGLE_API_KEY."}
    print(f"🔧 [Google Places API] 搜尋: '{query}' 在地點: {location}")
    try:
        places_result = gmaps.places(query=query, location=location, radius=2000, language='zh-TW')
        results = []
        for place in places_result.get('results', [])[:5]:
            results.append({
                "id": place.get('place_id'),
                "name": place.get('name'),
                "rating": place.get('rating', 'N/A'),
                "address": place.get('vicinity', 'No address provided'),
                "open_now": place.get('opening_hours', {}).get('open_now', 'Unknown')
            })
        return results
    except Exception as e:
        return f"Error calling Google Places API: {e}"


# --- 重寫 create_group_order_tool ---

# 定義需要的 API 權限範圍
SCOPES = [
    "https://www.googleapis.com/auth/forms.body",
    "https://www.googleapis.com/auth/drive"  # 需要 drive 權限來分享檔案
]

# 載入服務帳號憑證
try:
    creds = service_account.Credentials.from_service_account_file(
        'google_credentials.json', scopes=SCOPES)
except FileNotFoundError:
    creds = None
    print("⚠️ 'google_credentials.json' not found. `create_group_order_tool` will not work.")


@tool
def create_group_order_tool(restaurant_name: str, deadline: str) -> Dict:
    """
    為指定的餐廳建立一個揪團 Google Form 表單，並設定截止時間。
    Use this tool to create a Google Form for a group order for a specific restaurant and set a deadline.
    """
    if not creds:
        return {"error": "Google API credentials not loaded. Check 'google_credentials.json'."}
    if not OWNER_EMAIL:
        return {"error": "OWNER_EMAIL not set in .env file. Cannot share the form."}

    print(f"🔧 [Google Forms API] 為 '{restaurant_name}' 建立表單...")

    # 建立 Forms 和 Drive 的 API 服務物件
    forms_service = build('forms', 'v1', credentials=creds)
    drive_service = build('drive', 'v3', credentials=creds)

    # 1. 建立一個空白表單
    form_title = f"{restaurant_name} 訂餐揪團"
    form_description = f"訂餐截止時間：{deadline}。請填寫以下資訊，謝謝！"

    new_form = {
        "info": {
            "title": form_title,
            "documentTitle": form_title,
        }
    }

    try:
        # 1. 建立空白表單
        # ...
        created_form = forms_service.forms().create(body=new_form).execute()
        form_id = created_form['formId']
        form_url = created_form['responderUri']

        # 2. (新增) 建立一個 Google Sheet 來接收回覆
        sheets_service = build('sheets', 'v4', credentials=creds)
        sheet_body = {
            'properties': {'title': f'{form_title} (Responses)'}
        }
        response_sheet = sheets_service.spreadsheets().create(body=sheet_body).execute()
        response_sheet_id = response_sheet['spreadsheetId']

        # 3. 將表單連結到這個 Sheet
        link_request = {"requests": [{"createSheetsChart": {"spreadsheetId": response_sheet_id}}]}
        # 這個 API endpoint 是虛構的，真實的連結需要在表單設定中手動或用更複雜的腳本完成
        # 此處我們先記錄 sheet_id，並假設已連結
        print(f"📄 Manually link this sheet for responses: https://docs.google.com/spreadsheets/d/{response_sheet_id}")

        # 4. 轉移擁有權
        # ... (此部分邏輯不變)

        # 5. 為表單新增問題 (新增 Email 欄位)
        update_request = {"requests": [
            # ... (表單描述)
            {"createItem": {
                "item": {"title": "您的 Email", "questionItem": {"question": {"required": True, "shortAnswer": {}}}},
                "location": {"index": 0}}},
            {"createItem": {
                "item": {"title": "您的姓名", "questionItem": {"question": {"required": True, "shortAnswer": {}}}},
                "location": {"index": 1}}},
            # ... (其他問題)
        ]}
        forms_service.forms().batchUpdate(formId=form_id, body=update_request).execute()

        # ...
        return {"form_url": form_url, "form_id": form_id, "response_sheet_id": response_sheet_id}

    except Exception as e:
        return f"Error creating Google Form: {e}"