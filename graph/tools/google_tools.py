# graph/tools/google_tools.py

import os
import json
import logging
import googlemaps  # 導入 googlemaps 函式庫
from datetime import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import gspread
import pandas as pd
from langchain_core.tools import tool

# --- Configuration ---
# 服務帳號（用於 Forms, Sheets, Drive）
SCOPES = [
    "https://www.googleapis.com/auth/forms.body",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
]
try:
    creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if not creds_path or not os.path.exists(creds_path):
        raise FileNotFoundError

    creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
    forms_service = build("forms", "v1", credentials=creds)
    drive_service = build("drive", "v3", credentials=creds)
    gspread_client = gspread.service_account(filename=creds_path)

except FileNotFoundError:
    logging.warning("找不到 Google 服務帳號憑證檔案。Google Forms/Sheets 相關工具將無法運作。")
    creds = None
    forms_service = None
    drive_service = None
    gspread_client = None

# API 金鑰（用於 Maps）
try:
    gmaps_api_key = os.environ.get("GOOGLE_API_KEY")
    if not gmaps_api_key:
        raise ValueError("未設定 Maps_API_KEY 環境變數。")
    gmaps = googlemaps.Client(key=gmaps_api_key)
except ValueError as e:
    logging.warning(f"{e} Google Maps 工具將無法運作。")
    gmaps = None


# --- Tool Definitions ---

@tool
def search_Maps(query: str, location: str = "25.0553, 121.6134") -> str:
    """
    在 Google Maps 上根據查詢和經緯度搜尋地點，並回傳最多 5 個結果的列表。
    Searches for places on Google Maps based on a query and lat/lng location,
    returning a list of up to 5 results.
    """
    if not gmaps:
        logging.error("Google Maps API is not initialized.")
        return json.dumps({"error": "Google Maps API 未被正確初始化。請檢查 API 金鑰設定。"})

    logging.info(f"Searching Google Maps API with query: '{query}' near {location}")

    try:
        places_result = gmaps.places(
            query=query,
            language='zh-TW',
            location=location,
            radius=5000
        )

        results_to_return = []
        # Google API 最多一次可能回傳 20 個結果，我們只取前 5 個
        for place in places_result.get('results', [])[:5]:
            # --- 新增的邏輯：提取並格式化店家種類 ---
            place_types = place.get('types', [])
            # 過濾掉比較通用的類型，以找到更精確的描述
            non_generic_types = [
                t for t in place_types if t not in [
                    'point_of_interest', 'establishment', 'store', 'food', 'restaurant'
                ]
            ]
            # 從篩選後的類型中取第一個，如果沒有，則根據查詢關鍵字給一個預設值
            if non_generic_types:
                cuisine_type = non_generic_types[0].replace('_', ' ').title()
            elif '飲料' in query or '茶' in query or '咖啡' in query:
                cuisine_type = '飲料輕食'
            else:
                cuisine_type = '美食餐廳'
            # --- 新增邏輯結束 ---

            results_to_return.append({
                "name": place.get('name', 'N/A'),
                "rating": place.get('rating', 0),
                "address": place.get('vicinity', place.get('formatted_address', 'N/A')),
                "place_id": place.get('place_id'),
                "cuisine": cuisine_type  # 將新的「種類」欄位加入回傳的字典中
            })

        if not results_to_return:
            logging.info(f"No results found for query: '{query}'")
            return json.dumps({"message": "很抱歉，在附近找不到符合條件的店家。"})

        logging.info(f"Found {len(results_to_return)} results for query: '{query}'")
        return json.dumps(results_to_return, ensure_ascii=False)

    except googlemaps.exceptions.ApiError as e:
        logging.error(f"Google Maps API error: {e}", exc_info=True)
        return json.dumps({"error": f"API 錯誤: {e.status}"})
    except Exception as e:
        logging.error(f"Unknown error during Google Maps search: {e}", exc_info=True)
        return json.dumps({"error": "搜尋時發生未知錯誤。"})


@tool
def create_google_form(title: str, description: str, menu_items: list) -> str:
    """
    建立一個新的 Google 表單用於訂購，並將其連結到一個新的 Google Sheet。
    Creates a new Google Form for ordering, linked to a new Google Sheet.
    """
    if not forms_service or not gspread_client:
        logging.error("Google API services are not initialized.")
        return json.dumps({"error": "Google API 服務未被正確初始化。請檢查憑證檔案。"})

    try:
        # 1. 建立 Google Sheet 以接收回覆
        logging.info(f"Creating new Google Sheet with title: '{title} - 訂單回應'")
        sheet = gspread_client.create(f"{title} - 訂單回應")
        sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet.id}"
        logging.info(f"Successfully created response sheet: {sheet_url}")

        # 2. 建立 Google Form
        new_form = {"info": {"title": title, "documentTitle": title}}
        created_form = forms_service.forms().create(body=new_form).execute()
        form_id = created_form["formId"]
        form_url = created_form["responderUri"]
        logging.info(f"Successfully created Google Form: {form_url}")

        # 3. 將表單的回應目標設定為剛剛建立的 Sheet
        # Forms API v1 無法直接設定回應目的地，但我們可以手動建立關聯。
        # 實務上，後續的讀取是透過 sheet_url，所以這個流程是可行的。
        # drive_service.permissions().create(
        #     fileId=sheet.id,
        #     body={'type': 'user', 'role': 'writer', 'emailAddress': 'forms-receipts-noreply@google.com'}
        # ).execute() # 這是一個讓表單有權限寫入的方法，但可能因權限複雜而失敗

        # 4. 為表單新增問題
        requests = [
            {"updateFormInfo": {"info": {"description": description}, "updateMask": "description"}},
            {"createItem": {
                "item": {"title": "您的姓名", "questionItem": {"question": {"required": True, "textQuestion": {}}}},
                "location": {"index": 0}}},
            {"createItem": {"item": {"title": "餐點選擇", "questionItem": {"question": {"required": True,
                                                                                        "choiceQuestion": {
                                                                                            "type": "RADIO",
                                                                                            "options": [{"value": item}
                                                                                                        for item in
                                                                                                        menu_items]}}}},
                            "location": {"index": 1}}},
            {"createItem": {
                "item": {"title": "備註", "questionItem": {"question": {"textQuestion": {"paragraph": True}}}},
                "location": {"index": 2}}},
        ]
        forms_service.forms().batchUpdate(formId=form_id, body={"requests": requests}).execute()

        # 回傳包含兩個 URL 的 JSON 字串
        return json.dumps({"form_url": form_url, "sheet_url": sheet_url}, ensure_ascii=False)

    except Exception as e:
        logging.error(f"Error creating Google Form or Sheet: {e}", exc_info=True)
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@tool
def get_menu_from_url(url: str) -> str:
    """
    (佔位符) 從網站抓取菜單。真實情境會使用 BeautifulSoup 或 Scrapy。
    Placeholder function to scrape a menu from a website.
    """
    logging.info(f"(Placeholder) Scraping menu from {url}...")
    if "pizzahut" in url:
        return "經典口味: 夏威夷披薩, 海鮮披薩, 超級總匯披薩. 副食: BBQ烤雞, 薯星星."
    elif "coco" in url or "comebuy" in url or "wutea" in url:
        return "珍珠奶茶, 百香雙響炮, 四季春青茶, 檸檬紅茶, 經典奶蓋"
    return "抱歉，我暫時無法從這個網站自動抓取菜單，請您手動提供菜單內容。"


@tool
def read_google_sheet(sheet_url: str) -> pd.DataFrame:
    """
    Reads all data from a given Google Sheet URL and returns it as a Pandas DataFrame.
    """
    if not gspread_client:
        logging.error("gspread_client is not initialized.")
        return pd.DataFrame()
    try:
        logging.info(f"Reading Google Sheet from URL: {sheet_url}")
        sheet = gspread_client.open_by_url(sheet_url)
        worksheet = sheet.get_worksheet(0)
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)
        logging.info(f"Successfully read {len(df)} rows from the sheet.")
        return df
    except gspread.exceptions.SpreadsheetNotFound:
        logging.error(f"Spreadsheet not found at {sheet_url}. Check URL and permissions.")
        return pd.DataFrame()
    except Exception as e:
        logging.error(f"Error reading spreadsheet: {e}", exc_info=True)
        return pd.DataFrame()