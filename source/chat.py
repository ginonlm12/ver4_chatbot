from langchain.memory import ConversationBufferWindowMemory
from source.retriever import get_context
from configs.load_config import LoadConfig
from source.utils.base_model import GradeReWrite, SeachingDecision
from source.utils.prompt import PROMPT_HISTORY, PROMPT_HEADER, PROMPT_ELS_OR_TEXT
from rag_architecture.few_shot_sentence import classify_intent
from rag_architecture.retrieval import search_db


APP_CFG = LoadConfig()
memories = {}
def get_memory(session_id):
    if session_id not in memories:
        memories[session_id] = ConversationBufferWindowMemory(k = 3,
                                                              return_messages=True)
        memories[session_id].memory_key = session_id
    return memories[session_id]

# def get_history():
#     history = memory.load_memory_variables({})
#     return history['chat_history']

def rewrite_query(query: str, history: str) -> str: 
    """
    Arg:
        query: câu hỏi của người dùng
        history: lịch sử của người dùng
        Sử dụng LLM để viết lại câu hỏi của người dùng thành 1 câu mới.
    Return:
        trả về câu hỏi được viết lại.
    """
    llm_with_output = APP_CFG.load_rewrite_model().with_structured_output(GradeReWrite)
    query_rewrite = llm_with_output.invoke(PROMPT_HISTORY.format(question=query, chat_history=history)).rewrite
    return query_rewrite

def decision_search_type(query: str) -> str: 
    """
    Arg:
        query: câu hỏi của người dùng
        history: lịch sử của người dùng
        Sử dụng LLM để viết lại câu hỏi của người dùng thành 1 câu mới.
    Return:
        trả về câu hỏi được viết lại.
    """
    llm_with_output = APP_CFG.load_rewrite_model().with_structured_output(SeachingDecision)
    type = llm_with_output.invoke(PROMPT_ELS_OR_TEXT.format(query=query)).type
    return type


import os
import json

# Hàm để lưu lịch sử cuộc trò chuyện
def save_conversation(user_id: str, session_id: str, history: list):
    user_dir = os.path.join("./logs/user_logs", user_id)
    if not os.path.exists(user_dir):
        os.makedirs(user_dir)
    
    session_file = os.path.join(user_dir, f"{session_id}.json")
    
    with open(session_file, 'w') as f:
        json.dump(history, f, indent=4, ensure_ascii=False)

# Hàm để tải lịch sử cuộc trò chuyện
def load_conversation(user_id: str, session_id: str) -> list:
    session_file = os.path.join("./logs/user_logs", user_id, f"{session_id}.json")
    
    if os.path.exists(session_file):
        with open(session_file, 'r') as f:
            return json.load(f)
    else:
        return []

# Sử dụng trong chat_with_history
def chat_with_history(query: str, user_id: str, session_id: str):
    print("-Start-")
    # user_id = "235434534"
    # session_id = "45345345"
    history_conversation = load_conversation(user_id, session_id)
    # print(history_conversation)
    print("-" * 20)
    
    query_rewrite = rewrite_query(query=query, history=history_conversation)
    print(query_rewrite)
    print("-" * 30)
    
    type = decision_search_type(query_rewrite)
    print(type)
    
    if "ELS" in type:
        demands = classify_intent(query_rewrite)
        print("= = = = result few short = = = =:", demands)
        try:
            if len(demands['object']) >= 1:
                response_elastic, products, ok = search_db(demands)
                save_outtext = response_elastic
            else: 
                ok = 0
                save_outtext = "Anh/chị vui lòng cho em biết thêm thông tin để em có thể tư vấn chính xác hơn ạ!"
            prompt_final = PROMPT_HEADER.format(question=query_rewrite, context=save_outtext)
        except Exception as e:
            context = get_context(query=query_rewrite)
            prompt_final = PROMPT_HEADER.format(question=query_rewrite, context=context)

    else:
        context = get_context(query=query_rewrite)
        prompt_final = PROMPT_HEADER.format(question=query_rewrite, context=context)

    response = APP_CFG.load_rag_model().invoke(prompt_final).content
    
    print(response)
    print("-Finish-")
    memory = get_memory(session_id)
    memory.chat_memory.add_user_message(query)
    memory.chat_memory.add_ai_message(response)

    # Cập nhật lịch sử
    if isinstance(history_conversation, list):
        history_conversation.append((query, response))
    
    # Lưu lịch sử cuộc trò chuyện
    save_conversation(user_id, session_id, history_conversation)

    return "", history_conversation