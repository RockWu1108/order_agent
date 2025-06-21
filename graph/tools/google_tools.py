import os
import json
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import gspread
import pandas as pd
from langchain_core.tools import tool

# --- Configuration ---
# IMPORTANT: Ensure your service account has permissions for:
# - Google Drive API (to create and manage files)
# - Google Forms API
# - Google Sheets API
# Also, you must SHARE any created Google Sheet/Form with the service account's email address.
SCOPES = [
    "https://www.googleapis.com/auth/forms.body",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
]
# Load credentials from the environment variable set in docker-compose.yml
try:
    creds = Credentials.from_service_account_file(
        os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"), scopes=SCOPES
    )
    forms_service = build("forms", "v1", credentials=creds)
    drive_service = build("drive", "v3", credentials=creds)
    gspread_client = gspread.service_account(
        filename=os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    )
except FileNotFoundError:
    print("WARNING: Google credentials file not found. Google Tools will not work.")
    creds = None
    forms_service = None
    drive_service = None
    gspread_client = None


# --- Tool Definitions ---

@tool
def search_google_maps(query: str) -> str:
    """
    Searches for places on Google Maps and returns a list of results.
    NOTE: This is a placeholder. A real implementation would use the 
    Google Maps Platform Places API, which requires billing to be enabled.
    """
    print(f"Searching Google Maps for: {query}")
    # This is mock data. Replace with a real Google Places API call.
    mock_results = [
        {"name": "MushaMusha 越南法國麵包", "rating": 4.6, "address": "114台北市內湖區內湖路一段411巷2號"},
        {"name": "Pizza Hut 必勝客", "rating": 3.9, "address": "114台北市內湖區內湖路一段385號"},
        {"name": "Burger King 漢堡王", "rating": 4.1, "address": "114台北市內湖區內湖路一段321號"},
        {"name": "Wara Sushi", "rating": 4.3, "address": "114台北市內湖區內湖路一段369號"}
    ]
    # Return as a JSON string
    return json.dumps(mock_results)


@tool
def create_google_form(title: str, description: str, menu_items: list) -> str:
    """
    Creates a new Google Form for ordering, linked to a new Google Sheet.

    Args:
        title: The title of the form.
        description: A description for the form.
        menu_items: A list of strings for the multiple-choice food options.
    """
    if not forms_service:
        return json.dumps({"error": "Google Forms API not initialized."})

    # 1. Create the Google Sheet first to get its ID
    sheet = gspread_client.create(f"{title} - 訂單統計")
    sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet.id}"

    # IMPORTANT: Share the sheet with your personal Google account to view it
    # sheet.share('your-email@gmail.com', perm_type='user', role='writer')

    # 2. Create the Form
    new_form = {
        "info": {"title": title}
    }
    created_form = forms_service.forms().create(body=new_form).execute()
    form_id = created_form["formId"]
    form_url = created_form["responderUri"]

    # 3. Link Form to the created Sheet
    link_request = {"requests": [{"createSheetsChart": {"spreadsheetId": sheet.id}}]}
    # The Forms API does not directly support linking to a sheet. This is a common workaround pattern.
    # The most reliable way is often manual or using App Scripts.
    # For this agent, we will simply provide both URLs. The responses will need to be manually linked
    # or an Apps Script trigger set up in the Form.
    # Let's assume for now that when a form is created, its responses are automatically collected
    # in a new sheet linked to it. We will try to find this sheet.

    # 4. Add questions to the form
    requests = [
        # Set description
        {"updateFormInfo": {"info": {"description": description}, "updateMask": "description"}},
        # Add "Name" question
        {"createItem": {
            "item": {"title": "您的姓名", "questionItem": {"question": {"required": True, "textQuestion": {}}}},
            "location": {"index": 0}}},
        # Add "Department" question
        {"createItem": {"item": {"title": "部門/單位", "questionItem": {"question": {"textQuestion": {}}}},
                        "location": {"index": 1}}},
        # Add "Menu" question
        {"createItem": {"item": {"title": "餐點選擇", "questionItem": {"question": {"required": True,
                                                                                    "choiceQuestion": {"type": "RADIO",
                                                                                                       "options": [{
                                                                                                                       "value": item}
                                                                                                                   for
                                                                                                                   item
                                                                                                                   in
                                                                                                                   menu_items]}}}},
                        "location": {"index": 2}}},
        # Add "Notes" question
        {"createItem": {"item": {"title": "備註", "questionItem": {"question": {"textQuestion": {"paragraph": True}}}},
                        "location": {"index": 3}}},
    ]

    forms_service.forms().batchUpdate(formId=form_id, body={"requests": requests}).execute()

    return json.dumps({"form_url": form_url, "sheet_url": sheet_url})


@tool
def read_google_sheet(sheet_url: str) -> pd.DataFrame:
    """
    Reads all data from a given Google Sheet URL and returns it as a Pandas DataFrame.
    """
    if not gspread_client:
        return pd.DataFrame()

    try:
        sheet = gspread_client.open_by_url(sheet_url)
        worksheet = sheet.get_worksheet(0)  # Get the first sheet
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)
        return df
    except gspread.exceptions.SpreadsheetNotFound:
        print(
            f"Error: Spreadsheet not found at {sheet_url}. Make sure the URL is correct and the service account has access.")
        return pd.DataFrame()
    except Exception as e:
        print(f"An error occurred while reading the sheet: {e}")
        return pd.DataFrame()


@tool
def get_menu_from_url(url: str) -> str:
    """
    Placeholder function to scrape a menu from a website.
    A real implementation would use libraries like BeautifulSoup or Scrapy.
    """
    print(f"Scraping menu from: {url}")
    # Mocking a simple menu for demonstration
    if "pizzahut" in url:
        return "經典口味: 夏威夷披薩, 海鮮披薩, 超級總匯披薩. 副食: BBQ烤雞, 薯星星."
    return "抱歉，我暫時無法從這個網站自動抓取菜單，請您手動提供菜單內容。"
