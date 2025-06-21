# graph/tools/db_tools.py

import requests
from datetime import datetime, timedelta
from typing import List

# 引入 LangChain 工具裝飾器
from langchain_core.tools import tool

# 引入 gspread 來讀取 Google Sheet
import gspread

# 引入資料庫 Session 和模型
from sqlalchemy.orm import Session
from sql.models.model import SessionLocal, GroupOrder, Department, User # MODIFIED
# 引入設定
from config import LINE_NOTIFY_TOKEN, OWNER_EMAIL

# 引入新建立的 Email 和 LINE 工具
from graph.tools.email_tools import send_email_tool
from graph.tools.line_tools import send_line_message


@tool
def get_department_emails_tool(department_name: str) -> List[str] | str:
    """
    根據部門名稱，從資料庫取得該部門所有成員的 Email 列表。
    Use this tool to get a list of all member emails for a given department name from the database.
    """
    print(f"🔧 [DB Tool] Fetching emails for department: {department_name}")
    db: Session = SessionLocal()
    try:
        department = db.query(Department).filter(Department.name == department_name).first()
        if not department:
            return f"Error: Department '{department_name}' not found."
        if not department.users:
            return f"Info: Department '{department_name}' has no members."

        emails = [user.email for user in department.users]
        return emails
    finally:
        db.close()


@tool
def notify_department_and_schedule_tasks_tool(
        restaurant_name: str,
        form_url: str,
        response_sheet_id: str,
        deadline: str,
        department_name: str
) -> str:
    """
    儲存訂單資訊到資料庫，發送 Email 通知給指定部門，並設定截止時的統計任務。
    Saves order information to the database, sends an email notification to the specified department,
    and schedules a task to tally the results at the deadline.
    """
    print(f"🔧 [DB Tool] Notifying {department_name} for order '{restaurant_name}'")
    db: Session = SessionLocal()
    try:
        # 1. 解析截止時間
        deadline_dt = datetime.fromisoformat(deadline)

        # 2. 將訂單資訊存入資料庫
        new_order = GroupOrder(
            id=f"{restaurant_name}-{deadline}",
            restaurant_name=restaurant_name,
            form_url=form_url,
            response_sheet_id=response_sheet_id,
            deadline=deadline_dt,
            status='open',
            department_name=department_name
        )
        db.add(new_order)
        db.commit()

        # 3. 取得部門成員 Email 並發送通知信
        emails = get_department_emails_tool.invoke({"department_name": department_name})
        if isinstance(emails, list) and emails:
            subject = f"【訂餐通知】{restaurant_name} 開團囉！"
            body = f"""
            <h3>大家好，</h3>
            <p>"{restaurant_name}" 的訂餐團已經開始了！</p>
            <p><b>截止時間：{deadline_dt.strftime('%Y-%m-%d %H:%M')}</b></p>
            <p>請點擊以下連結填寫您的餐點：</p>
            <p><a href="{form_url}" style="font-size: 16px; font-weight: bold;">點我訂餐</a></p>
            <br>
            <p>祝您用餐愉快！</p>
            """
            send_email_tool.invoke({"recipients": emails, "subject": subject, "body": body})

            # 4. 使用新的 Messaging API 工具發送確認訊息給預設的管理員
            line_message = f"✅ 訂單建立成功\n餐廳：{restaurant_name}\n通知部門：{department_name}"
            send_line_message.invoke({"message_text": line_message})

            return f"Successfully scheduled task, sent email to {len(emails)} members, and sent a LINE confirmation."
        else:
            return f"Scheduled task, but failed to send email notifications. Reason: {emails}"

    except Exception as e:
        db.rollback()
        return f"An error occurred: {e}"
    finally:
        db.close()


def check_and_remind_orders():
    """
    一個由 APScheduler 定時執行的背景函式，用於檢查即將到期的訂單並發送提醒。
    A background function executed by APScheduler to check for expiring orders and send reminders.
    """
    db: Session = SessionLocal()
    try:
        now = datetime.now()
        reminder_window = now + timedelta(hours=1)
        upcoming_orders = db.query(GroupOrder).filter(
            GroupOrder.status == 'open',
            GroupOrder.deadline > now,
            GroupOrder.deadline <= reminder_window
        ).all()

        for order in upcoming_orders:
            # 此處可以加入發送 LINE 或 Email 提醒的邏輯
            print(f"🔔 [Reminder] Order '{order.restaurant_name}' is due at {order.deadline}.")
            reminder_message = f"🔔 訂餐提醒\n餐廳「{order.restaurant_name}」的訂單將在一小時後截止，還沒填單的同仁請盡快處理喔！"
            send_line_message.invoke({"message_text": reminder_message})

    finally:
        db.close()


def tally_and_notify_orders():
    """
    一個由 APScheduler 定時執行的背景函式。
    它會找出所有已過期但狀態仍為 'open' 的訂單，從 Google Sheet 抓取回覆、
    統計結果，並透過 Email 和 LINE 發送給相關人員。
    """
    db: Session = SessionLocal()
    now = datetime.now()
    expired_orders = db.query(GroupOrder).filter(
        GroupOrder.status == 'open',
        GroupOrder.deadline <= now
    ).all()

    if not expired_orders:
        return

    print(f"📊 [Tallying] Found {len(expired_orders)} expired orders to process.")

    try:
        gc = gspread.service_account(filename='google_credentials.json')
    except Exception as e:
        print(f"Error initializing gspread: {e}")
        db.close() #<-- Added this line
        return

    for order in expired_orders:
        try:
            print(f"Processing order: {order.restaurant_name}")
            # 1. 從 Google Sheet 讀取回覆
            sheet = gc.open_by_key(order.response_sheet_id)
            worksheet = sheet.sheet1
            responses = worksheet.get_all_records()

            # 2. 準備 Email 和 LINE 的統計結果訊息
            email_summary_html = f"<h3>【訂餐統計結果】</h3><h4>餐廳：{order.restaurant_name}</h4>"
            line_summary_text = f"📊 訂單統計完成\n餐廳：{order.restaurant_name}\n----------\n"

            if not responses:
                email_summary_html += "<p>本次訂餐無人填寫。</p>"
                line_summary_text += "本次訂餐無人填寫。"
                participant_emails = []
            else:
                participant_emails = [resp.get('您的 Email', '').strip() for resp in responses if
                                      resp.get('您的 Email')]
                meal_counts = {}
                for resp in responses:
                    meal = resp.get('您要點的餐點', '未填寫')
                    meal_counts[meal] = meal_counts.get(meal, 0) + 1

                email_summary_html += "<table border='1' cellpadding='5' cellspacing='0'><tr><th>餐點</th><th>數量</th></tr>"
                for meal, count in sorted(meal_counts.items()):
                    email_summary_html += f"<tr><td>{meal}</td><td>{count}</td></tr>"
                    line_summary_text += f"▪️ {meal}: {count} 份\n"
                email_summary_html += "</table>"

            # 3. 發送統計結果給開團者 (Email + LINE)
            send_email_tool.invoke({
                "recipients": [OWNER_EMAIL],
                "subject": f"訂餐統計完成 - {order.restaurant_name}",
                "body": email_summary_html
            })
            send_line_message.invoke({"message_text": line_summary_text})
            print(f"Sent tally summary to {OWNER_EMAIL} and LINE.")

            # 4. 發送確認信給所有填寫者
            if participant_emails:
                unique_participant_emails = list(set(filter(None, participant_emails)))
                confirmation_subject = f"【訂餐完成確認】您已成功預訂 {order.restaurant_name}"
                confirmation_body = f"""
                <p>您好，</p>
                <p>您參與的 <b>{order.restaurant_name}</b> 訂餐已截止，您的訂單已為您處理。</p>
                <p>感謝您的參與！</p>
                """
                send_email_tool.invoke({
                    "recipients": unique_participant_emails,
                    "subject": confirmation_subject,
                    "body": confirmation_body
                })
                print(f"Sent confirmation to {len(unique_participant_emails)} participants.")

            # 5. 更新訂單狀態
            order.status = 'closed'
            db.commit()

        except Exception as e:
            print(f"Error processing order {order.id}: {e}")
            db.rollback()
            continue

    db.close()