import streamlit as st
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.schema import HumanMessage
from PyPDF2 import PdfReader
import pandas as pd
from io import StringIO
import docx
import os

# API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Cấu hình giao diện Streamlit
st.set_page_config(
    page_title="LHP AI Chatbot",
    page_icon="new_icon.png",  # File icon tùy chỉnh
    layout="wide"
)

# Giao diện chính
st.title("LHP AI Chatbot")
st.write("Ask questions directly, or upload files for additional context.")

# Hàm đọc nội dung file
def read_pdf(file):
    pdf_reader = PdfReader(file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def read_txt(file):
    stringio = StringIO(file.getvalue().decode("utf-8"))
    return stringio.read()

def read_docx(file):
    doc = docx.Document(file)
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    return text

def read_excel(file):
    """Đọc nội dung từ file Excel."""
    df = pd.read_excel(file)
    return df.to_string(index=False)  # Chuyển nội dung Excel thành chuỗi văn bản

# Tạo mô hình nhúng
embeddings_model = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)

# Lưu trạng thái phản hồi
if "response" not in st.session_state:
    st.session_state["response"] = ""

# đặt câu hỏi
user_question = st.text_input("Type your question here:")

# Tải lên file
uploaded_files = st.file_uploader(
    "Optional: Upload files (PDF, TXT, DOCX, Excel supported) for context", 
    type=["pdf", "txt", "docx", "xlsx", "xls"], 
    accept_multiple_files=True
)

# Đọc và kết hợp nội dung từ các file đã tải lên (nếu có)
file_contents = []
if uploaded_files:
    for uploaded_file in uploaded_files:
        if uploaded_file.name.endswith(".pdf"):
            file_contents.append(read_pdf(uploaded_file))
        elif uploaded_file.name.endswith(".txt"):
            file_contents.append(read_txt(uploaded_file))
        elif uploaded_file.name.endswith(".docx"):
            file_contents.append(read_docx(uploaded_file))
        elif uploaded_file.name.endswith((".xlsx", ".xls")):
            file_contents.append(read_excel(uploaded_file))

# Hiển thị thông báo khi xử lý file xong
if file_contents:
    st.success("Files uploaded and processed successfully!")

# Kết hợp nội dung file vào câu hỏi nếu có
if st.button("Submit"):
    if user_question.strip():
        if file_contents:
            combined_text = "\n".join(file_contents)
            user_question = f"Based on the uploaded documents:\n{combined_text}\n\n{user_question}"

        # Tạo mô hình GPT
        llm = ChatOpenAI(
            openai_api_key=OPENAI_API_KEY,
            temperature=0.7,
            max_tokens=1000,
            model_name="gpt-3.5-turbo",
        )

        # Gửi câu hỏi tới GPT
        input_message = HumanMessage(content=user_question)
        response = llm([input_message])
        st.session_state["response"] = response.content

# Hiển thị kết quả trả lời
if st.session_state["response"]:
    st.subheader("Answer:")
    st.write(st.session_state["response"])
