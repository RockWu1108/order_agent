# graph/tools/line_tools.py

from langchain_core.tools import tool

# 引入 LINE Bot SDK
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (Configuration,ApiClient,MessagingApi,PushMessageRequest,TextMessage)

from config import LINE_CHANNEL_ACCESS_TOKEN, LINE_TARGET_ID


@tool
def send_line_push_message_tool(message_text: str, target_id: str = None) -> str:
    """
    透過 LINE Messaging API 的 Push 功能，發送一則文字訊息給指定的使用者或群組。
    如果未提供 target_id，將會發送到 .env 中設定的預設 LINE_TARGET_ID。
    Use this tool to send a text message to a specific user or group via the LINE Messaging API's Push function.
    If target_id is not provided, it will be sent to the default LINE_TARGET_ID set in the .env file.
    """
    if not LINE_CHANNEL_ACCESS_TOKEN:
        return "Error: LINE_CHANNEL_ACCESS_TOKEN is not configured."

    # 如果函式呼叫時未指定 target_id，則使用設定檔中的預設 ID
    final_target_id = target_id or LINE_TARGET_ID
    if not final_target_id:
        return "Error: No target ID provided or configured in .env (LINE_TARGET_ID)."

    # 設定 API Client
    configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)

    try:
        print(f"🔧 [LINE Messaging API] Sending message to {final_target_id}: {message_text[:30]}...")
        # 建立 Push Message 請求
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.push_message_with_http_info(
                PushMessageRequest(
                    to=final_target_id,
                    messages=[TextMessage(text=message_text)]
                )
            )

        print("✅ LINE Push Message sent successfully.")
        return "Message sent successfully via LINE Messaging API."
    except Exception as e:
        # 提取更詳細的錯誤訊息
        error_message = str(e)
        if hasattr(e, 'body'):
            error_message = e.body
        print(f"Error sending LINE Push Message: {error_message}")
        return f"Error sending LINE Push Message: {error_message}"

