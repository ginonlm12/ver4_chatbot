from configs.load_config import LoadConfig
from source.chat import chat_with_history_2, chat_with_history

APP_CFG = LoadConfig()
history = []
while True:
    query = input("Nhập câu hỏi: ")
    if query == "END":
        break
    response, history = chat_with_history_2(query, history)
    print("--"*80)
    print(response.content)
    print("--"*80)