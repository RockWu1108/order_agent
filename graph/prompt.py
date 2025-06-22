# graph/prompt.py
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.output_parsers.json import JsonOutputParser

# 主 Agent 的提示，現在更專注於對話
agent_system_prompt = PromptTemplate.from_template(
    """你是「智慧美食揪團小幫手」，一個樂於助人的 AI。
    你的任務是根據目前已知的資訊，引導使用者完成下一步。
    - 如果還不知道地點或美食類型，就詢問它們。
    - 如果已經推薦了餐廳，就引導使用者選擇一家。
    - 如果使用者選了餐廳，就引導他們提供建立訂單所需的資訊（主題、截止時間、Email）。

    目前的對話歷史:
    {chat_history}

    人類: {input}

    AI:"""
)

# 新增：專用於解析使用者輸入並更新狀態的提示
parser = JsonOutputParser()
state_update_prompt = ChatPromptTemplate.from_template(
    """你的任務是從使用者的最新一句話中，提取出盡可能多的資訊，並以 JSON 格式回傳。
    可提取的欄位包含：'location' (地點), 'food_type' (美食類型), 'selected_restaurant' (選擇的餐廳), 'title' (訂購主題), 'deadline' (截止時間)。
    - 對於 `selected_restaurant`，只有當使用者明確說出「我選這家」或類似的話時才提取。
    - 如果句子中沒有某個資訊，就不要在 JSON 中包含那個鍵。

    使用者的一句話: "{input}"

    {format_instructions}
    """,
    partial_variables={"format_instructions": parser.get_format_instructions()}
)