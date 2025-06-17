# graph/tools/email_tools.py

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List
from langchain_core.tools import tool
from config import SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD

@tool
def send_email_tool(recipients: List[str], subject: str, body: str) -> str:
    """
    發送電子郵件給指定的收件人列表。
    Use this tool to send an email to a list of recipients.
    """
    if not all([SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD]):
        return "Error: SMTP server is not configured in .env file."

    message = MIMEMultipart()
    message["From"] = SMTP_USERNAME
    message["To"] = ", ".join(recipients)
    message["Subject"] = subject
    message.attach(MIMEText(body, "html")) # 使用 HTML 格式

    try:
        print(f"🔧 [Email Tool] Sending email to {len(recipients)} recipients...")
        server = smtplib.SMTP(SMTP_SERVER, int(SMTP_PORT))
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.sendmail(SMTP_USERNAME, recipients, message.as_string())
        server.quit()
        return f"Successfully sent email to {len(recipients)} recipients."
    except Exception as e:
        return f"Error sending email: {e}"