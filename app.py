import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler
from langchain_core.messages import HumanMessage

# --- Local Imports ---
# 確保 Azure client 在 graph 之前被初始化
from config import client as azure_client
# 由於工具需要存取 scheduler，我們在此處初始化
# 備註：這會形成一個可接受的循環導入 (circular import)，在 Flask 應用中是常見模式。
app = Flask(__name__)
scheduler = BackgroundScheduler()

# 從新的 db_tools 導入背景任務函式
# 注意：這些導入必須在 app 和 scheduler 初始化之後
from graph.tools.db_tools import check_and_remind_tool, tally_and_notify_tool

# 現在再導入 graph，它內部會用到已設定好的工具
from graph.graph import app_graph

# --- Flask App 設定 ---
CORS(app)
scheduler.start()

# ==============================================================================
#  Flask API 端點
# ==============================================================================
@app.route('/api/agent', methods=['POST'])
def agent_endpoint():
    if not azure_client:
        return jsonify({"error": "Azure OpenAI client not configured. Please check server logs and .env variables."}), 500

    data = request.json
    if not data or "query" not in data:
        return jsonify({"error": "無效的請求，缺少 'query' 欄位。"}), 400

    query = data["query"]
    # 建立一個包含系統訊息的初始狀態，給予 Agent 更明確的角色和指示
    system_message = """
    你是一位智慧美食揪團助理。你的任務是協助使用者完成以下流程：
    1.  根據需求搜尋餐廳 (`search_restaurants_tool`)。
    2.  為選定的餐廳建立揪團表單 (`create_group_order_tool`)。
    3.  將表單通知給指定部門的成員，這會自動設定提醒與統計排程 (`notify_department_and_schedule_tasks_tool`)。
    請根據對話歷史和使用者最新的請求，有條理地呼叫工具來完成任務。在呼叫工具前，請先確認是否已具備所有必要資訊 (例如，通知部門前必須先有表單連結)。
    """
    initial_state = {"messages": [
        HumanMessage(content=system_message), # 用系統訊息指導 Agent
        HumanMessage(content=query)
    ]}

    try:
        # 執行代理圖
        final_state = app_graph.invoke(initial_state)
        last_message_obj = final_state['messages'][-1]
        final_message_content = ""

        if hasattr(last_message_obj, 'content') and isinstance(last_message_obj.content, str):
            final_message_content = last_message_obj.content
        else:
            final_message_content = "任務已執行，但沒有文字回覆。"

        return jsonify({"result": final_message_content})
    except Exception as e:
        import traceback
        print(f"❌ [Graph執行錯誤] {e}\n{traceback.format_exc()}")
        return jsonify({"error": f"Agent 執行時發生內部錯誤: {str(e)}"}), 500


if __name__ == '__main__':
    port = int(os.getenv("PORT", 5001))
    app.run(debug=True, port=port)

