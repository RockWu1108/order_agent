# app.py

import uuid
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from typing import List, Dict
from langgraph.checkpoint.sqlite import SqliteSaver  # 引入 SqliteSaver
from apscheduler.schedulers.background import BackgroundScheduler
from langgraph.checkpoint.mongodb import MongoDBSaver
from pymongo import MongoClient
from langchain_openai import AzureChatOpenAI
from langchain_core.utils.function_calling import convert_to_openai_tool
from graph.tools.tools_definition import tools

from config import AZURE_OPENAI_DEPLOYMENT_NAME, MONGODB_URI, MONGODB_DB_NAME, MONGODB_COLLECTION_NAME, AZURE_OPENAI_API_VERSION
from graph.graph import create_graph
from sql.models.model import init_db  # 引入初始化資料庫的函式
from graph.tools.db_tools import check_and_remind_orders, tally_and_notify_orders

# --- 初始化 ---
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# 初始化 Azure OpenAI Client
client = AzureChatOpenAI(
    azure_deployment=AZURE_OPENAI_DEPLOYMENT_NAME,
    api_version=AZURE_OPENAI_API_VERSION,
    temperature=0,
)
# 將 LangChain tool 轉換為 OpenAI 格式
tools_for_openai = [convert_to_openai_tool(tool) for tool in tools]

# 初始化資料庫
init_db()

# --- 記憶體設定 ---
# --- 記憶體設定 (替換為 MongoDB) ---
# 使用 MongoDBSaver 作為記憶體後端
mongo_client = MongoClient(MONGODB_URI)
memory = MongoDBSaver(
    mongo_client[MONGODB_DB_NAME],
    collection_name=MONGODB_COLLECTION_NAME
)

# --- LangGraph App ---
# 建立帶有記憶體配置的 Graph
app_graph = create_graph(client, tools_for_openai).with_config(checkpointer=memory)

# --- 定時任務 ---
scheduler = BackgroundScheduler()
scheduler.add_job(check_and_remind_orders, 'interval', minutes=1)
scheduler.add_job(tally_and_notify_orders, 'interval', minutes=1)
scheduler.start()


# --- API 端點 ---
@app.route('/api/agent', methods=['POST'])
def agent_endpoint():
    data = request.json
    if not data or "input" not in data:
        return jsonify({"error": "Invalid request, 'input' is required"}), 400

    user_input = data["input"]
    # 從前端接收 conversation_id，如果沒有就建立一個新的
    conversation_id = data.get("conversation_id") or str(uuid.uuid4())

    system_prompt = (
        "你是一個智慧美食揪團助理。你的工作是協助使用者搜尋餐廳、建立訂餐表單、"
        "並根據使用者的要求通知相關部門的成員。你必須使用提供的工具來完成這些任務。"
        "請用繁體中文和使用者溝通。"
    )

    input_data = {"messages": [("system", system_prompt), ("human", user_input)]}

    # 在 config 中傳入 thread_id，LangGraph 會用它來存取對應的對話紀錄
    config = {"configurable": {"thread_id": conversation_id}}

    def stream_response():
        try:
            # 使用 stream 方法來獲取即時回應
            for chunk in app_graph.stream(input_data, config=config):
                # 每個 chunk 代表圖中的一個節點的輸出
                # 我們只關心 agent 節點產生的 AI 訊息
                agent_output = chunk.get('agent', {}).get('messages', [])
                if agent_output:
                    # 假設 agent_output 的最後一則訊息是最新的回應
                    message_content = agent_output[-1].content
                    if message_content:
                        # 在 JSON streaming 格式中，每個物件後要換行
                        yield f'{{"type": "message", "content": {jsonify(message_content)}, "conversation_id": "{conversation_id}"}}\n'

            # 當 stream 結束後，可以發送一個結束信號
            yield f'{{"type": "done"}}\n'
        except Exception as e:
            yield f'{{"type": "error", "content": "{str(e)}"}}'

    return Response(stream_response(), mimetype='application/x-json-stream')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)