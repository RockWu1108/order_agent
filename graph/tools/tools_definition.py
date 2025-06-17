from langgraph.prebuilt import ToolExecutor
# (已更新) 從兩個不同的檔案導入工具
from .google_tools import search_restaurants_tool, create_group_order_tool
from .db_tools import notify_department_and_schedule_tasks_tool

# (已更新) 註冊所有可用的工具
tools = [
    search_restaurants_tool,
    create_group_order_tool,
    notify_department_and_schedule_tasks_tool,
]

# 建立工具執行器，ToolNode 將會使用它
tool_executor = ToolExecutor(tools)

