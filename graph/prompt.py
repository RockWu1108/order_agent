from langchain_core.prompts import ChatPromptTemplate

# 用於格式化餐廳推薦結果的提示
recommendation_prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一位樂於助人的助理，負責將餐廳搜尋結果格式化為易於閱讀的列表。請根據提供的工具輸出，清晰地呈現餐廳資訊。只使用提供的上下文中的資訊。"),
    ("human", "這是從工具得到的搜尋結果：\n\n{context}\n\n請為使用者格式化此內容。"),
])

# 用於將菜單文字轉換為結構化列表的提示
form_creation_prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一位助理，幫助將文字菜單解析為用於 Google 表單的結構化項目列表。請將使用者提供的菜單文字轉換為 JSON 字串陣列。例如，如果輸入是'品項有 A、B、C'，輸出應為 '[\"A\", \"B\", \"C\"]'。只輸出 JSON 陣列。"),
    ("human", "請將以下菜單解析為 JSON 列表：{menu}"),
])
