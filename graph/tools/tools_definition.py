from langgraph.prebuilt import ToolNode
from graph.tools.google_tools import search_google_maps, create_google_form, read_google_sheet, get_menu_from_url
from graph.tools.line_tools import send_line_message
from graph.tools.email_tools import send_email_tool
# 如果您有其他工具，也請在此處導入

# 將所有工具彙總到一個列表中
tools = [
    search_google_maps,
    create_google_form,
    read_google_sheet,
    get_menu_from_url,
    send_line_message,
    send_email_tool,
]

# 修正：建立並導出 tool_node 實例
tool_node = ToolNode(tools)
