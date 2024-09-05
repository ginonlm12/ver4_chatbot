import gradio as gr
import os
import json
from configs.load_config import LoadConfig
from source.chat import chat_with_history

# APP_CFG = LoadConfig()

# def recommend_text(text, chatbot, history):
#     updated_chatbot, response = chat_with_history(text, history)
#     return gr.update(value=text), response

def log_feedback(modify_text, human_feedback, ai_feedback, user_id, session_id):
    feedback = {
        'human': human_feedback,
        'ai': ai_feedback,
        'modify': modify_text
    }
    
    file_dir = os.path.join("./logs/feedback", user_id)
    if not os.path.exists(file_dir):
        os.makedirs(file_dir)

    file_path = os.path.join(file_dir, f"{session_id}.json")
    feedback_entry = []

    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            feedback_entry = json.load(f)
    
    feedback_entry.append(feedback)
    
    with open(file_path, 'w') as f:
        json.dump(feedback_entry, f, indent=4, ensure_ascii=False)
    
    return None, None, None

import time

def generate_session_id():
    return str(int(time.time() % 100000000)).zfill(8)

def reset_conversation():
    global session_id 
    session_id = generate_session_id()
    return [("", "")], []

# session_id = generate_session_id()

# Giao diện Gradio
with gr.Blocks(css="""
    #chatbot { 
        height: 100%; 
        overflow-y: auto; 
        border: 1px solid #ddd; 
        border-radius: 20px; 
        padding: 30px;
        background-color: #f7f7f7;
    }
    #chatbot .bot { 
        background-color: #F0F8FF; 
        color: black;
        float: left;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    #chat-header {
        text-align: center;
        padding: 20px;
        background-color: #FF6347;
        color: white;
        border-radius: 15px 15px 0 0;
        margin-bottom: 20px;
    }

""") as demo:
    
    gr.HTML("""
    <div id="chat-header">
        <h1 style="color: #000000">💬 Chatbot hỗ trợ bán hàng điều hòa</h1>
        <p style="color: #000000">Hãy đặt câu hỏi, tôi sẽ cố gắng trả lời bạn!</p>
    </div>
    """)
    
    with gr.Row():
        user_id = gr.Textbox(
            label="User ID",
            placeholder="Nhập user VD: huydq46",
            elem_id="user-id-box"
        )
    err_message = gr.Markdown("", visible=True)

    global session_id
    session_id = generate_session_id()

    chatbot = gr.Chatbot(
        # [("", "")],
        elem_id="chatbot",
        bubble_full_width=False,
        # avatar_images=("images/avt_vcc.png", "images/avt_bot.png"),
    )

    history = []  # Initialize the history list

    with gr.Row():
        txt = gr.Textbox(
            show_label=False,
            placeholder="Nhập tin nhắn của bạn ở đây...",
            elem_id="msg-box"
        )
        submit_btn = gr.Button("Gửi", elem_id="send-btn")
    
    
    # Hàm để gửi tin nhắn và xử lý cuộc trò chuyện
    def handle_chat(text, user_id):
        if not user_id:
            return '', [('', '**Lỗi: Hãy nhập user id trước khi gửi tin nhắn.**')]
        response = chat_with_history(text, user_id, session_id)
        return response

    # Xử lý khi nhấn nút gửi
    submit_btn.click(handle_chat, [txt, user_id], [txt, chatbot])
    # submit_btn.submit(handle_chat, [txt, user_id], [txt, chatbot])
    with gr.Row(elem_classes="button-row"):
        modify_txt = gr.Textbox(
             show_label=False,
            placeholder="Góp ý chỉnh sửa câu trả lời của bot...",
            elem_id="modify-box"
        )
        submit_feedback = gr.Button("Lưu góp ý")


    # Hàm để tải lịch sử cuộc trò chuyện từ tệp cục bộ
    def load_conversation(user_id: str, session_id: str) -> list:
        session_file = os.path.join("./logs/user_logs", user_id, f"{session_id}.json")
        
        if os.path.exists(session_file):
            with open(session_file, 'r') as f:
                return json.load(f)
        else:
            return ''

    def handle_feedback(modify_text, user_id):
        # session_id = generate_session_id
        print(' user_id, session_id',  user_id, session_id)
        # Tải lịch sử cuộc trò chuyện từ tệp cục bộ
        history = load_conversation(user_id, session_id)
        
        # Lấy đoạn chat gần nhất
        human_feedback = history[-1][0] if history else ""
        ai_feedback = history[-1][1] if history else ""
        # result = log_feedback(modify_text, human_feedback, ai_feedback, user_id, session_id)
        log_feedback(modify_text, human_feedback, ai_feedback, user_id, session_id)
        
        # Trả về giá trị rỗng để xóa nội dung Textbox
        return ''

    submit_feedback.click(handle_feedback, [modify_txt, user_id], [modify_txt])

    with gr.Row(elem_classes="button-row"):
        clear = gr.Button("Xóa tin nhắn", elem_id="clear-btn")
        reset = gr.Button("Reset cuộc trò chuyện", elem_id="reset-btn")

    clear.click(lambda: None, None, chatbot, queue=False)
    reset.click(reset_conversation, outputs=[chatbot, txt])

demo.launch(server_name="0.0.0.0", server_port=3333, share = True)
