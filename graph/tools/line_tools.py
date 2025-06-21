import os
from langchain_core.tools import tool
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
    PushMessageRequest,
)

# --- LINE API Configuration ---
# Load the channel access token from environment variables
configuration = Configuration(access_token=os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "YOUR_TOKEN"))


@tool
def send_line_message(line_token: str, message: str) -> str:
    """
    Sends a push message to a specified LINE user or group using a long-lived channel access token
    or a specific group/user ID as the token.

    Args:
        line_token: The user ID, group ID, or room ID to send the message to.
        message: The text message to send.
    """
    if not line_token or line_token == "YOUR_TOKEN":
        return "LINE token not provided. Skipping notification."

    try:
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.push_message_with_http_info(
                PushMessageRequest(
                    to=line_token,
                    messages=[TextMessage(text=message)]
                )
            )
        return "Successfully sent LINE message."
    except Exception as e:
        return f"Failed to send LINE message. Error: {e}"
