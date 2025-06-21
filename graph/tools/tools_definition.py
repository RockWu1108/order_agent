# graph/tools/tools_definition.py

# 移除這一行，因為它不存在
# from langchain_core.tools import ToolExecutor

from graph.tools.google_tools import search_restaurants_tool, create_group_order_tool
from graph.tools.db_tools import get_department_emails_tool, notify_department_and_schedule_tasks_tool
from graph.tools.email_tools import send_email_tool

# 您的工具列表保持不變
tools = [
    search_restaurants_tool,
    create_group_order_tool,
    get_department_emails_tool,
    notify_department_and_schedule_tasks_tool,
    send_email_tool,
]

# 【新增】建立一個從工具名稱到工具物件的映射字典
# 這是替代 ToolExecutor 的核心
tool_map = {tool.name: tool for tool in tools}

# 我們不再需要 tool_executor 物件
# tool_executor = ToolExecutor(tools)