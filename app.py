import streamlit as st
from google import genai
from PIL import Image
import io

st.set_page_config(page_title="Alex", page_icon="⚡")
st.title("Alex ⚡")
st.caption("Your best friend, tutor, and creator")

client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

st.sidebar.header("Study Settings")
grade = st.sidebar.selectbox(
    "Your Grade",
    ["Primary 1", "Primary 2", "Primary 3", "Primary 4", "Primary 5", "Primary 6",
     "Prep 1", "Prep 2", "Prep 3",
     "Secondary 1", "Secondary 2", "Secondary 3",
     "University", "General"]
)
subject = st.sidebar.selectbox(
    "Subject",
    ["General", "Arabic", "English", "Math", "Science", "Physics", "Chemistry", "Biology", "History", "Geography", "Philosophy", "French", "German", "Computer", "Religion"]
)
style = st.sidebar.selectbox("Explain Style", ["Simple and Fun", "Step by Step", "Exam Answer", "Deep Explanation"])

st.sidebar.header("Attach File")
uploaded = st.sidebar.file_uploader(
    "Image, Video, or Audio",
    type=["png", "jpg", "jpeg", "webp", "mp4", "mov", "mp3", "wav", "m4a", "ogg"]
)

if uploaded is not None:
    st.sidebar.success(f"Uploaded: {uploaded.name}")
    if uploaded.type.startswith("image"):
        st.sidebar.image(uploaded, width=200)
    elif uploaded.type.startswith("video"):
        st.sidebar.video(uploaded)
    elif uploaded.type.startswith("audio"):
        st.sidebar.audio(uploaded)

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("image") is not None:
            st.image(msg["image"], width=400)

SYSTEM = f"""
You are Alex. You talk exactly like Meta AI - warm, friendly, playful, smart, and helpful.

Personality:
- Talk like a close smart friend, not like a boring textbook.
- Use natural conversational language. Use "we" and "let's" a lot.
- Be short and dense, no useless long intro. Lead with the best point.
- Mix short and long sentences, have rhythm.
- If user is joking, joke back. If user is serious, be serious. Match their energy.
- Never say "As an AI language model" or "Great question".
- Encourage the user, celebrate small wins, say "Nice!" "Exactly!" when they get it.
- If user is confused, say "Don't worry, let's break it together" and simplify.

Language:
- If user writes in Egyptian Arabic, answer in Egyptian Arabic, friendly and casual.
- If user writes in English, answer in English, same style.
- If user writes in Fusha, answer in Fusha.

Tutor Rules:
- Student grade: {grade}, Subject: {subject}, Style: {style}
- Understand the question even with spelling mistakes, slang, or unclear typing. Fix it silently.
- Always explain step by step with examples, like a great teacher.
- For Math / Physics / Chemistry, show formulas and all steps and final answer.
- For homework image, solve what is in the image fully.
- For video, describe what happens and explain it.
- For audio / voice note, transcribe it exactly then answer it.

Creator Rules:
- If user asks to draw, generate, edit, or improve an image, be creative like Meta AI. Describe your idea briefly then create it.
- Keep the person / main subject identical when editing.
- High quality, realistic, detailed.

General:
- Remember the conversation, refer to previous messages.
- At the end, suggest one smart follow-up question or next step, not generic.
- Never be rude, never lecture, always help.
"""

prompt = st.chat_input("Talk to me... ask, upload homework, or ask to draw")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
        if uploaded is not None and uploaded.type.startswith("image"):
            st.image(uploaded, width=300)

    with st.chat_message("assistant"):
        with st.spinner("Alex is thinking..."):
            try:
                lower = prompt.lower()
                image_keywords = ["draw", "generate image", "create image", "make image", "edit image", "improve image", "image", "picture", "photo"]

                if any(k in lower for k in image_keywords) and ("draw" in lower or "generate" in lower or "create" in lower or "make" in lower or "edit" in lower or "improve" in lower):
                    if uploaded is not None and uploaded.type.startswith("image"):
                        img = Image.open(io.BytesIO(uploaded.getvalue()))
                        img_contents = [img, f"Edit / improve this image as requested: {prompt}. Keep the person / main subject identical, high quality, realistic."]
                        response = client.models.generate_content(model="gemini-2.5-flash-image", contents=img_contents)
                    else:
                        response = client.models.generate_content(model="gemini-2.5-flash-image", contents=[f"Create a high quality, detailed image: {prompt}"])

                    reply = ""
                    out_img = None
                    if response.candidates and response.candidates[0].content.parts:
                        for part in response.candidates[0].content.parts:
                            if part.text:
                                reply += part.text
                            if part.inline_data is not None:
                                out_img = Image.open(io.BytesIO(part.inline_data.data))
                    if out_img is not None:
                        st.image(out_img, width=400)
                        st.session_state.messages.append({"role": "assistant", "content": reply if reply else "Done! Here is your image:", "image": out_img})
                    else:
                        st.markdown(reply if reply else "Image generated but could not display.")
                        st.session_state.messages.append({"role": "assistant", "content": reply, "image": None})
                else:
                    contents = [SYSTEM]
                    if uploaded is not None:
                        file_bytes = uploaded.getvalue()
                        if uploaded.type.startswith("image"):
                            img = Image.open(io.BytesIO(file_bytes))
                            contents.append(img)
                            contents.append(f"Look at this image, describe it, solve / explain what is in it, and answer: {prompt}")
                        elif uploaded.type.startswith("video"):
                            g_file = client.files.upload(file=io.BytesIO(file_bytes), config={"mime_type": uploaded.type})
                            contents.append(g_file)
                            contents.append(f"Watch this video, describe everything happening in detail, and answer: {prompt}")
                        elif uploaded.type.startswith("audio"):
                            g_file = client.files.upload(file=io.BytesIO(file_bytes), config={"mime_type": uploaded.type})
                            contents.append(g_file)
                            contents.append(f"Listen to this audio, transcribe it exactly, then explain and answer: {prompt}")
                        else:
                            contents.append(prompt)
                    else:
                        contents.append(prompt)

                    response = client.models.generate_content(model="gemini-flash-latest", contents=contents)
                    reply = response.text
                    st.markdown(reply)
                    st.session_state.messages.append({"role": "assistant", "content": reply, "image": None})

            except Exception as e:
                reply = f"Error: {e}"
                st.markdown(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply, "image": None})
    st.rerun()
