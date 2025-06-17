import psycopg2
import requests
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
from typing import Dict
from langchain_core.tools import tool

# (重要) 從主應用導入 app 和 scheduler
# 這會建立一個循環導入，但在 Flask 中是管理全域物件的常見作法
from app import app, scheduler
from config import DATABASE_URL, LINE_NOTIFY_TOKEN


def get_db_connection():
    """建立並回傳一個資料庫連線。"""
    conn = psycopg2.connect(DATABASE_URL)
    return conn


@tool
def notify_department_and_schedule_tasks_tool(department: str, form_url: str, restaurant_name: str,
                                              deadline: str) -> str:
    """
    通知指定部門所有成員關於一個新的揪團活動，並自動設定提醒與統計的排程。
    Notifies all members of a specified department about a new group order, and automatically schedules reminders and tallying tasks.
    """
    print(f"🔧 [DB 工具] 準備通知 '{department}'，揪團餐廳: {restaurant_name}")
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("SELECT email FROM employees WHERE department = %s", (department,))
        employees = cursor.fetchall()
        if not employees:
            return f"資料庫中找不到 '{department}' 的任何成員。"

        invitee_emails = [emp['email'] for emp in employees]
        deadline_dt = datetime.fromisoformat(deadline)

        cursor.execute(
            "INSERT INTO group_orders (restaurant_name, form_url, deadline, is_active) VALUES (%s, %s, %s, %s) RETURNING id",
            (restaurant_name, form_url, deadline_dt, True)
        )
        order_id = cursor.fetchone()['id']

        for email in invitee_emails:
            cursor.execute(
                "INSERT INTO order_invitees (order_id, invitee_email) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                (order_id, email)
            )

        conn.commit()

        # 模擬寄送 Email
        print(f"✉️  [模擬] 寄送邀請函至: {invitee_emails}")

        # 設定排程任務
        reminder_time = deadline_dt - timedelta(hours=1)
        if reminder_time > datetime.now():
            scheduler.add_job(check_and_remind_tool, 'date', run_date=reminder_time, args=[order_id],
                              id=f"reminder_{order_id}")
            print(f"📅 [排程] 已設定提醒任務於 {reminder_time.strftime('%Y-%m-%d %H:%M:%S')}")

        scheduler.add_job(tally_and_notify_tool, 'date', run_date=deadline_dt, args=[order_id], id=f"tally_{order_id}")
        print(f"📅 [排程] 已設定統計任務於 {deadline_dt.strftime('%Y-%m-%d %H:%M:%S')}")

        cursor.close()
        conn.close()
        return f"成功發送揪團邀請給 '{department}' 的 {len(invitee_emails)} 位成員！並已設定好相關排程。"

    except Exception as e:
        print(f"❌ [DB工具錯誤] {e}")
        return f"處理部門通知時發生錯誤: {e}"


# --- 以下為背景任務，不由 LLM 直接呼叫 ---

def check_and_remind_tool(order_id: int):
    """(由排程觸發) 檢查未回覆者並寄送提醒。"""
    with app.app_context():  # 在 Flask app context 中執行，確保能存取設定
        print(f"⏰ [背景任務] 檢查並提醒 Order ID: {order_id}")
        try:
            conn = get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            cursor.execute("SELECT invitee_email FROM order_invitees WHERE order_id = %s", (order_id,))
            all_invitees = {row['invitee_email'] for row in cursor.fetchall()}

            # 模擬從 Google Sheet 取得已回覆名單
            print("📝 [模擬] 讀取 Google Sheet 的已回覆名單...")
            responded_users = {"user1@example.com", "user4@example.com"}

            unresponded_users = all_invitees - responded_users

            if unresponded_users:
                print(f"✉️  [模擬] 寄送提醒信至: {list(unresponded_users)}")
            else:
                print("👍 所有人都已回覆，不需提醒。")

            cursor.close()
            conn.close()
        except Exception as e:
            print(f"❌ [提醒任務錯誤] {e}")


def tally_and_notify_tool(order_id: int):
    """(由排程觸發) 統計結果並透過 LINE 通知。"""
    with app.app_context():
        print(f"🏁 [背景任務] 最終統計 Order ID: {order_id}")
        try:
            # 模擬讀取 Google Sheet 統計結果
            summary = f"--- 揪團 {order_id} 統計結果 ---\n- 小籠包 x 5\n- 蝦仁炒飯 x 3"

            if LINE_NOTIFY_TOKEN:
                url = "https://notify-api.line.me/api/notify"
                headers = {"Authorization": f"Bearer {LINE_NOTIFY_TOKEN}"}
                payload = {"message": summary}
                requests.post(url, headers=headers, data=payload)
                print(f"📱 已發送 LINE Notify 通知。")
            else:
                print("⚠️ 未設定 LINE_NOTIFY_TOKEN，無法發送通知。")

            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE group_orders SET is_active = FALSE WHERE id = %s", (order_id,))
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"❌ [統計任務錯誤] {e}")
