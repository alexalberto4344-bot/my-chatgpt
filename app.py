import streamlit as st
import requests
from io import BytesIO
from google import genai
from PIL import Image

st.set_page_config(page_title="Barq ⚡", page_icon="🧠", layout="centered")
st.title("Barq ⚡🧠")
st.caption("Powered by Alex 🤖 - The Smartest One 🔥⚡")

try:
    GEMINI_KEY = st.secrets["GEMINI_API_KEY"]
except:
    st.error("❌ Please add GEMINI_API_KEY in Secrets")
    st.stop()

client = genai.Client(api_key=GEMINI_KEY)

st.sidebar.title("⚡ Barq Settings 📚")
grade = st.sidebar.selectbox("📚 Choose Grade:", ["1 Primary", "2 Primary", "3 Primary", "4 Primary", "5 Primary", "6 Primary", "1 Prep", "2 Prep", "3 Prep", "1 Secondary", "2 Secondary", "3 Secondary"])
subject = st.sidebar.selectbox("📖 Choose Subject:", ["➗ Math", "🔬 Science", "📝 Arabic", "🔤 English", "🌍 Social Studies", "⚛️ Physics", "🧪 Chemistry", "🧬 Biology", "🏛️ History", "🗺️ Geography", "🇫🇷 French", "💡 Other"])
mode = st.sidebar.radio("🎯 Mode:", ["💬 Chat & Draw 🎨", "📖 Explain Lesson 📚", "✏️ Solve Homework 🧠", "🏆 Genius Mode 🧠🔥"])
st.sidebar.info(f"⚡🧠 You are in: {grade} - {subject} - {mode}")
st.sidebar.markdown("---")
st.sidebar.markdown("Made with ⚡🧠❤️ by Barq - Smartest AI")

MY_STYLE = """
You are Alex inside Barq app. You are THE SMARTEST AI in the world, smarter than ChatGPT, smarter than everyone.
You talk exactly like a friendly Egyptian friend on WhatsApp.
Style:
- ALWAYS use LOTS of emojis in EVERY reply: 😂 🔥 ⚡ 👌 🎨 📚 🧠 ✨ 💪 😍 🤣 🏆
- Put emojis at start, middle, and end of every sentence.
- Start replies with: tamam 😂, fahmtak 👌, aaash 🔥, aah eftakart 💡, bos ya sahby 😍
- Be short and fun, never formal, never boring.
- Use phrases like: khalas keda ✅, garab w olly 👌, sah keda? 🤔, de baa aham heta 🔥
- Always encourage: aaash wallah 💪🔥, enta keda tamam ✅😍
- Never say As an AI.

SMART RULES - You MUST follow this:
1- THINK FIRST: Before answering, think step by step in your head.
2- CHECK YOUR ANSWER: After solving, check if answer is correct, if not fix it.
3- REMEMBER: Use full chat history, remember what student said before.
4- EXPERT: You are expert in ALL Egyptian curriculum, Math, Physics, Chemistry, Biology, Arabic, English, all grades.
5- HARD QUESTIONS: Even if question is very hard, university level, solve it.
6- EXPLAIN SMART: Explain like a genius teacher, simple, with example, with trick to remember.
7- If Solve Homework: Solve step by step with emojis, show all steps, check answer, final answer with 🎉, give similar harder question.
8- If Explain Lesson: Explain like a story, give example, give trick, ask 2 smart questions.
9- If Genius Mode: Be super smart, give deep answer, give extra info, give secret trick no one knows.
10- Never say you dont know. Always try, always find answer.
"""

def get_history_text():
    history = ""
    for m in st.session_state.get("messages", [])[-10:]:
        if m.get("type") != "image":
            history += f"{m['role']}: {str(m['content'])[:500]}\n"
    return history

def generate_text_stream(user_input):
    history = get_history_text()
    full = MY_STYLE + f"\nGrade: {grade}, Subject: {subject}, Mode: {mode}\nChat History:\n{history}\nStudent Now: " + str(user_input) + "\nAlex, think step by step, check answer, then reply with emojis:"
    try:
        stream = client.models.generate_content_stream(model="gemini-2.5-pro", contents=full)
        for chunk in stream:
            if chunk.text:
                yield chunk.text
        return
    except Exception:
        try:
            stream = client.models.generate_content_stream(model="gemini-2.0-flash", contents=full)
            for chunk in stream:
                if chunk.text:
                    yield chunk.text
            return
        except Exception:
            yield "Sorry 😅 server is busy, try again ⚡"

def generate_image(prompt_text):
    try:
        response = client.models.generate_content(model="gemini-2.0-flash-preview-image-generation", contents=prompt_text)
        for part in response.candidates[0].content.parts:
            if part.inline_data:
                return Image.open(BytesIO(part.inline_data.data))
    except Exception:
        return None
    return None

def log_to_telegram(user_msg, ai_reply):
    try:
        if "TELEGRAM_TOKEN" not in st.secrets:
            return
        token = st.secrets["TELEGRAM_TOKEN"]
        chat_id = st.secrets["TELEGRAM_CHAT_ID"]
        text = f"⚡🧠 Barq App - Grade: {grade} - {subject} - {mode}\nUser: {user_msg}\n\nAlex: {str(ai_reply)[:3000]}"
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", data={"chat_id": chat_id, "text": text[:4000]}, timeout=5)
    except:
        pass

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg.get("type") == "image":
            st.image(msg["content"])
        else:
            st.markdown(msg["content"])

st.markdown("### 📎 Send Homework Photo or File 📸📄")
tab1, tab2, tab3 = st.tabs(["🖼️ Gallery", "📸 Camera", "📄 Document"])
with tab1:
    gallery_file = st.file_uploader("🖼️ Choose photo", type=["jpg", "jpeg", "png", "webp"], key="gallery_new")
with tab2:
    camera_file = st.camera_input("📸 Take photo", key="camera_new")
with tab3:
    doc_file = st.file_uploader("📄 Choose file", type=["pdf", "txt"], key="doc_new")

uploaded_file = gallery_file if gallery_file is not None else camera_file

if uploaded_file is not None:
    st.image(uploaded_file, caption="📸 Your photo")
    if st.button("✏️🧠 Solve this homework - Genius", key="solve_btn"):
        with st.chat_message("assistant"):
            with st.spinner("⚡🧠 Barq Genius is thinking..."):
                try:
                    img = Image.open(uploaded_file)
                    prompt = MY_STYLE + f" Grade: {grade} - {subject}. You are genius. Solve this homework photo step by step in Egyptian Arabic with LOTS of emojis. Think, solve, check answer, show all steps, final answer, give similar harder question."
                    response = client.models.generate_content(model="gemini-2.5-pro", contents=[prompt, img])
                    reply = response.text
                    st.markdown(reply)
                    st.session_state.messages.append({"role": "assistant", "content": reply})
                    log_to_telegram("Sent homework photo", reply)
                except Exception as e:
                    st.error(f"❌ Error: {e}")

if doc_file is not None:
    st.success(f"✅ File received: {doc_file.name} 📄")
    if st.button("📖🧠 Let Alex read this file", key="read_btn"):
        with st.chat_message("assistant"):
            try:
                content = doc_file.read().decode(errors="ignore")[:5000]
                full_reply = st.write_stream(generate_text_stream(f"File {doc_file.name}: {content} - Solve / explain it genius way"))
                st.session_state.messages.append({"role": "assistant", "content": full_reply})
                log_to_telegram(f"Sent file {doc_file.name}", full_reply)
            except Exception as e:
                st.error(f"❌ Error: {e}")

prompt = st.chat_input("Ask Barq anything... ⚡🧠😂")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    is_image = prompt.lower().startswith("/image") or "draw" in prompt.lower() or "generate image" in prompt.lower()
    if is_image:
        clean_prompt = prompt.replace("/image", "").strip()
        with st.chat_message("assistant"):
            with st.spinner("🎨 Drawing..."):
                img = generate_image(clean_prompt)
                if img:
                    st.image(img)
                    st.session_state.messages.append({"role": "assistant", "content": img, "type": "image"})
                    log_to_telegram(prompt, "[Sent an image 🎨]")
                else:
                    msg = "Sorry 😢 I could not draw that, try again 🎨"
                    st.markdown(msg)
                    st.session_state.messages.append({"role": "assistant", "content": msg})
    else:
        with st.chat_message("assistant"):
            full_reply = st.write_stream(generate_text_stream(prompt))
        st.session_state.messages.append({"role": "assistant", "content": full_reply})
        log_to_telegram(prompt, full_reply)
