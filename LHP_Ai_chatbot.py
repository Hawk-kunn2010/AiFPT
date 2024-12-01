import streamlit as st
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage
from PyPDF2 import PdfReader
import pandas as pd
from io import StringIO
import docx
import os
import json

# API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# File lưu dữ liệu cục bộ
SAVED_FILES_PATH = "saved_files.json"

# Cấu hình giao diện Streamlit
st.set_page_config(
    page_title="LHP AI Chatbot",
    page_icon="new_icon.png",
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
    return df.to_string(index=False)

# Hàm lưu file vào bộ nhớ cục bộ
def save_files_locally(data):
    with open(SAVED_FILES_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# Hàm tải file từ bộ nhớ cục bộ
def load_files_locally():
    if os.path.exists(SAVED_FILES_PATH):
        with open(SAVED_FILES_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

# Lấy nội dung file đã lưu
saved_files = load_files_locally()

# Hiển thị file đã lưu (nếu có)
if saved_files:
    st.subheader("Saved Files:")
    for file in saved_files:
        st.write(f"**{file['name']}**")
        with st.expander("Show content"):
            st.text(file["content"])

# Tải file mới
uploaded_files = st.file_uploader(
    "Optional: Upload files (PDF, TXT, DOCX, Excel supported) for context",
    type=["pdf", "txt", "docx", "xlsx", "xls"],
    accept_multiple_files=True
)

# Đọc nội dung file tải lên
new_files = []
if uploaded_files:
    for uploaded_file in uploaded_files:
        if uploaded_file.name.endswith(".pdf"):
            content = read_pdf(uploaded_file)
        elif uploaded_file.name.endswith(".txt"):
            content = read_txt(uploaded_file)
        elif uploaded_file.name.endswith(".docx"):
            content = read_docx(uploaded_file)
        elif uploaded_file.name.endswith((".xlsx", ".xls")):
            content = read_excel(uploaded_file)
        else:
            content = None

        if content:
            new_files.append({"name": uploaded_file.name, "content": content})

    st.success("Files uploaded successfully!")

# Hiển thị file mới tải lên
if new_files:
    st.subheader("Newly Uploaded Files:")
    for i, file in enumerate(new_files):
        st.write(f"**{file['name']}**")
        with st.expander("Show content"):
            st.text(file["content"])

        # Nút lưu file
        if st.button(f"Save {file['name']} for later", key=f"save_{i}"):
            saved_files.append(file)
            save_files_locally(saved_files)
            st.success(f"File '{file['name']}' saved for later!")

# Đặt câu hỏi
user_question = st.text_input("Type your question here:")

# Kết hợp nội dung từ cả file lưu và file mới vào câu hỏi
if st.button("Submit"):
    if user_question.strip():
        # Nội dung từ file đã lưu
        saved_content = "\n".join(file["content"] for file in saved_files)

        # Nội dung từ file mới tải lên (nếu có)
        new_content = "\n".join(file["content"] for file in new_files)

        # Kết hợp nội dung
        combined_text = f"{saved_content}\n{new_content}"
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

# Hiển thị câu trả lời
if st.session_state.get("response"):
    st.subheader("Answer:")
    st.write(st.session_state["response"])
