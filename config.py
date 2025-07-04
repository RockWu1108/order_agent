import os
from dotenv import load_dotenv

load_dotenv()

# --- 環境設定 ---
DATABASE_URL = os.getenv("DATABASE_URL")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")
LINE_NOTIFY_TOKEN = os.getenv("LINE_NOTIFY_TOKEN") # 新增 Line Token 讀取

# (新增) 讀取 Google 金鑰和範本
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_SHEET_TEMPLATE_URL = os.getenv("GOOGLE_SHEET_TEMPLATE_URL")

# (新增) 讀取表單擁有者的 Email
OWNER_EMAIL = os.getenv("OWNER_EMAIL")

# (新增) 讀取 SMTP 設定
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = os.getenv("SMTP_PORT")
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")


# (新增) 讀取 MongoDB 設定
MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME")
MONGODB_COLLECTION_NAME = os.getenv("MONGODB_COLLECTION_NAME")


# (新增) LINE Messaging API 設定
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
# 接收通知的使用者 ID 或群組 ID
LINE_TARGET_ID = os.getenv("LINE_TARGET_ID")
