# graph/tools/tools_definition.py
from langchain_core.tools import ToolExecutor  # type: ignore
from .google_tools import search_restaurants_tool, create_group_order_tool
from .db_tools import get_department_emails_tool, notify_department_and_schedule_tasks_tool
from .email_tools import send_email_tool

tools = [
    search_restaurants_tool,
    create_group_order_tool,
    get_department_emails_tool,
    notify_department_and_schedule_tasks_tool,
    send_email_tool,
]

tool_executor = ToolExecutor(tools)