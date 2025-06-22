import os
from celery import Celery
from celery.schedules import crontab
import datetime
import json
from graph.tools.google_tools import read_google_sheet
from graph.tools.line_tools import send_line_message
from graph.tools.email_tools import send_email_tool

# --- Celery Configuration ---
# It's crucial that the broker and backend URLs are correctly configured,
# especially in a containerized environment. 'redis' is the service name
# from docker-compose.yml.
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://redis:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://redis:6379/0')

celery = Celery(
    'tasks',
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND
)

celery.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Taipei',
    enable_utc=True,
)


# --- Celery Tasks ---

@celery.task(name="tally_and_notify_task")
def tally_and_notify_task(sheet_url: str, title: str, notification_channels: dict):
    """
    A Celery task to read Google Sheet responses, tally them up,
    and send a summary notification to LINE and/or Email.

    Args:
        sheet_url (str): The URL of the Google Sheet containing order responses.
        title (str): The title of the group order for the notification message.
        notification_channels (dict): A dictionary containing 'line_token' and/or 'emails'.
    """
    print(f"Executing task for '{title}' with sheet: {sheet_url}")

    try:
        # 1. Read data from Google Sheet
        orders_df = read_google_sheet(sheet_url)

        if orders_df.empty:
            summary = f"【{title} 訂單統計】\n\n本次揪團沒有人訂餐喔！"
        else:
            # 2. Tally the orders
            # Ensure the column names match your Google Form questions exactly.
            # We assume columns like '您的姓名', '餐點選擇', '備註' exist.
            # Adjust these column names if they are different in your form.
            if '餐點選擇' not in orders_df.columns:
                return f"Error: '餐點選擇' column not found in the sheet. Available columns: {orders_df.columns.tolist()}"

            order_counts = orders_df['餐點選擇'].value_counts().reset_index()
            order_counts.columns = ['item', 'count']

            # Create a detailed summary string
            summary_lines = [f"【{title} 訂單統計 - 總計 {len(orders_df)} 份】"]

            for _, row in order_counts.iterrows():
                # Find who ordered each item
                patrons = orders_df[orders_df['餐點選擇'] == row['item']]['您的姓名'].tolist()
                summary_lines.append(f"- {row['item']} x {row['count']} ({', '.join(patrons)})")

            summary = "\n".join(summary_lines)

        print("Generated Summary:\n", summary)

        # 3. Send notifications
        line_token = notification_channels.get("line_token")
        emails = notification_channels.get("emails")

        if line_token:
            print(f"Sending notification to LINE with token: {line_token}")
            send_line_message(line_token, summary)

        if emails and isinstance(emails, list):
            print(f"Sending notification to emails: {emails}")
            email_subject = f"訂單統計結果: {title}"
            send_email_tool(emails, email_subject, summary)

        return f"Task completed successfully for '{title}'. Summary sent."

    except Exception as e:
        print(f"An error occurred in tally_and_notify_task: {e}")
        # You might want to add more robust error handling/retry logic here
        return f"Task failed for '{title}'. Error: {str(e)}"

# Example of how to call this task with a delay/ETA
# from celery_worker import tally_and_notify_task
# from datetime import datetime, timedelta
#
# deadline = datetime.utcnow() + timedelta(minutes=5)
# sheet_url = "https://docs.google.com/spreadsheets/d/your_sheet_id/edit"
# title = "週五下午茶"
# channels = {"line_token": "your_token", "emails": ["test@example.com"]}
#
# tally_and_notify_task.apply_async(
#     args=[sheet_url, title, channels],
#     eta=deadline
# )
