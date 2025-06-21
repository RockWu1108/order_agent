from flask.cli import load_dotenv
from langchain_openai import ChatOpenAI, AzureChatOpenAI
import os

# 為了安全起見，強烈建議將您的 API 金鑰設定為環境變數
# 例如: os.environ["OPENAI_API_KEY"] = "sk-..."

load_dotenv()
# 確保已經設定了 OPENAI_API_KEY 環境變數
if "AZURE_OPENAI_API_KEY" not in os.environ:
    raise ValueError("請設定 AZURE_OPENAI_API_KEY 環境變數以使用 OpenAI API。")

# .env讀取

api_key = os.environ.get("AZURE_OPENAI_API_KEY")

# 初始化您選擇的大型語言模型
llm = AzureChatOpenAI(
    api_version="2024-07-01-preview",
    model_name="gpt-4o-mini"  # 使用的模型名稱，可以根據你的部署進行替換
)
