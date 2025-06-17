import os
from dotenv import load_dotenv
from openai import AzureOpenAI
# (已更新) 從最新的 tools_definition 導入，它現在包含所有工具
from graph.tools.tools_definition import tools

# --- 環境設定 ---
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")
LINE_NOTIFY_TOKEN = os.getenv("LINE_NOTIFY_TOKEN") # 新增 Line Token 讀取

client = None
tools_for_openai = []

# 設定 Azure OpenAI 客戶端
try:
    if not all([AZURE_OPENAI_API_KEY, AZURE_OPENAI_API_VERSION, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_DEPLOYMENT_NAME]):
        raise ValueError("缺少 Azure OpenAI 的環境變數設定。")

    client = AzureOpenAI(
        api_key=AZURE_OPENAI_API_KEY,
        api_version=AZURE_OPENAI_API_VERSION,
        azure_endpoint=AZURE_OPENAI_ENDPOINT
    )
    print("✅ Azure OpenAI API (多工具模式) 已成功設定。")

    # 將所有註冊的工具轉換為 OpenAI 可用的格式
    tools_for_openai = [
        {"type": "function", "function": {"name": t.name, "description": t.description, "parameters": t.args}}
        for t in tools
    ]
except Exception as e:
    print(f"⚠️ 未能設定 Azure OpenAI API: {e}")

