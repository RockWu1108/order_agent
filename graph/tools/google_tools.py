# graph/tools/google_tools.py

import os
import json
import logging
import googlemaps
from datetime import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import gspread
import pandas as pd
from langchain_core.tools import tool
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# --- Configuration ---
SCOPES = [
    "https://www.googleapis.com/auth/forms.body",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
]
try:
    creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if not creds_path or not os.path.exists(creds_path):
        raise FileNotFoundError("Google 服務帳號憑證檔案路徑未設定或檔案不存在。")

    creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
    forms_service = build("forms", "v1", credentials=creds)
    drive_service = build("drive", "v3", credentials=creds)
    gspread_client = gspread.service_account(filename=creds_path)
    logging.info("Google Forms, Drive, and Sheets services initialized successfully.")

except Exception as e:
    logging.warning(f"Google服務初始化失敗: {e}。相關工具將無法運C作。")
    creds = None
    forms_service = None
    drive_service = None
    gspread_client = None

gmaps = None

def get_gmaps_client():
    """Lazily initialize the Google Maps client."""
    global gmaps
    if gmaps is None:
        try:
            gmaps_api_key = os.getenv("GOOGLE_API_KEY")
            if not gmaps_api_key:
                raise ValueError("未設定 GOOGLE_API_KEY 環境變數。")
            gmaps = googlemaps.Client(key=gmaps_api_key)
            logging.info("Google Maps service initialized successfully.")
        except Exception as e:
            logging.warning(f"初始化 Google Maps client 失敗: {e}。Google Maps 工具將無法運作。")
            gmaps = None  # Ensure gmaps is None if initialization fails
    return gmaps


# --- Tool Definitions ---

@tool
def search_Maps(query: str, location: str = "25.0553, 121.6134") -> str:
    """
    在 Google Maps 上根據查詢和經緯度搜尋地點，並回傳最多 8 個結果的列表。
    """
    client = get_gmaps_client()
    if not client:
        return json.dumps({"error": "Google Maps API 未被正確初始化。請檢查 API 金鑰設定。"}, ensure_ascii=False)

    logging.info(f"Searching Google Maps API with query: '{query}' near {location}")
    try:
        places_result = client.places(
            query=query,
            language='zh-TW',
            location=location,
            radius=5000  # 搜尋半徑 5 公里
        )

        results_to_return = []
        # ✨ 變更：將結果數量從 5 增加到 8
        for place in places_result.get('results', [])[:8]:
            place_types = place.get('types', [])
            non_generic_types = [t for t in place_types if
                                 t not in ['point_of_interest', 'establishment', 'store', 'food', 'restaurant']]

            if non_generic_types:
                cuisine_type = non_generic_types[0].replace('_', ' ').title()
            elif any(keyword in query for keyword in ['飲料', '茶', '咖啡', '手搖']):
                cuisine_type = '飲料輕食'
            else:
                cuisine_type = '美食餐廳'

            results_to_return.append({
                "name": place.get('name', 'N/A'),
                "rating": place.get('rating', 0),
                "address": place.get('vicinity', place.get('formatted_address', 'N/A')),
                "place_id": place.get('place_id'),
                "cuisine": cuisine_type
            })

        if not results_to_return:
            logging.info(f"No results found for query: '{query}'")
            return json.dumps({"message": "很抱歉，在附近找不到符合條件的店家。"}, ensure_ascii=False)

        logging.info(f"Found {len(results_to_return)} results for query: '{query}'")
        result_json = json.dumps(results_to_return, ensure_ascii=False)
        logging.info(f"search_Maps result: {result_json}")
        return result_json

    except googlemaps.exceptions.ApiError as e:
        logging.error(f"Google Maps API error: {e}", exc_info=True)
        return json.dumps({"error": f"API 錯誤: {e.status}"}, ensure_ascii=False)
    except Exception as e:
        logging.error(f"Unknown error during Google Maps search: {e}", exc_info=True)
        return json.dumps({"error": "搜尋時發生未知錯誤。"}, ensure_ascii=False)


@tool
def create_google_form(title: str, description: str, menu_items: list) -> str:
    """
    建立一個新的 Google 表單用於訂購，並將其連結到一個新的 Google Sheet。
    """
    if not all([forms_service, drive_service, gspread_client]):
        return json.dumps({"error": "Google API 服務未被正確初始化。請檢查憑證檔案。"}, ensure_ascii=False)

    try:
        logging.info(f"Creating new Google Sheet with title: '{title} - 訂單回應'")
        sheet = gspread_client.create(f"{title} - 訂單回應")
        sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet.id}"
        logging.info(f"Successfully created response sheet: {sheet_url}")

        new_form = {"info": {"title": title, "documentTitle": title}}
        created_form = forms_service.forms().create(body=new_form).execute()
        form_id = created_form["formId"]
        form_url = created_form["responderUri"]
        logging.info(f"Successfully created Google Form: {form_url}")

        # 設定表單回覆連結到試算表
        # 注意：這一步驟在 v1 API 中沒有直接的方法，但建立的 sheet_url 可用於後續讀取

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

        result_json = json.dumps({"form_url": form_url, "sheet_url": sheet_url}, ensure_ascii=False)
        logging.info(f"create_google_form result: {result_json}")
        return result_json

    except Exception as e:
        logging.error(f"Error creating Google Form or Sheet: {e}", exc_info=True)
        return json.dumps({"error": f"建立Google資源時發生錯誤: {str(e)}"}, ensure_ascii=False)


# ... (get_menu_from_url 和 read_google_sheet 保持不變)
@tool
def get_menu_from_url(url: str) -> str:
    """
    (佔位符) 從網站抓取菜單。真實情境會使用 BeautifulSoup 或 Scrapy。
    """
    logging.info(f"(Placeholder) Scraping menu from {url}...")
    menu = ""
    if "pizzahut" in url:
        menu = "經典口味: 夏威夷披薩, 海鮮披薩, 超級總匯披薩. 副食: BBQ烤雞, 薯星星."
    elif "coco" in url or "comebuy" in url or "wutea" in url or "50lan" in url:
        menu = "珍珠奶茶, 百香雙響炮, 四季春青茶, 檸檬紅茶, 經典奶蓋"
    else:
        menu = "抱歉，我暫時無法從這個網站自動抓取菜單，請您手動提供菜單內容。"
    logging.info(f"get_menu_from_url result: {menu}")
    return menu


@tool
def read_google_sheet(sheet_url: str) -> pd.DataFrame:
    """
    從指定的 Google Sheet URL 讀取所有資料並回傳為 Pandas DataFrame。
    """
    if not gspread_client:
        logging.error("gspread_client is not initialized.")
        return pd.DataFrame()
    try:
        logging.info(f"Reading Google Sheet from URL: {sheet_url}")
        sheet = gspread_client.open_by_url(sheet_url)
        worksheet = sheet.get_worksheet(0)  # 讀取第一個工作表
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