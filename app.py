import streamlit as st
from google import genai
from PIL import Image
import io
import fitz
import docx

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

# LIKE WHATSAPP MENU - Gallery / Camera / Document / AI Studio / Voice
st.sidebar.header("Attach - Like WhatsApp")
menu = st.sidebar.radio(
    "Choose",
    ["Gallery", "Camera", "Document", "AI Studio", "Voice"],
    horizontal=True
)

active_bytes = None
active_type = None
active_text = ""
ai_style = "Realistic"

if menu == "Gallery":
    up = st.sidebar.file_uploader("Gallery - Photo / Video", type=["png", "jpg", "jpeg", "webp", "mp4", "mov"])
    if up is not None:
        active_bytes = up.getvalue()
        active_type = up.type
        st.sidebar.success(f"Gallery: {up.name}")
        if up.type.startswith("image"):
            st.sidebar.image(up, width=200)
        else:
            st.sidebar.video(up)

elif menu == "Camera":
    cam = st.sidebar.camera_input("Camera - Take photo now")
    if cam is not None:
        active_bytes = cam.getvalue()
        active_type = "image"
        st.sidebar.success("Photo taken!")
        st.sidebar.image(cam, width=200)

elif menu == "Document":
    doc = st.sidebar.file_uploader("Document - PDF / Word / Text", type=["pdf", "docx", "txt"])
    if doc is not None:
        st.sidebar.success(f"Document: {doc.name}")
        try:
            if doc.name.endswith(".pdf"):
                pdf = fitz.open(stream=doc.getvalue(), filetype="pdf")
                for page in pdf:
                    active_text += page.get_text() + "\n"
            elif doc.name.endswith(".docx"):
                d = docx.Document(io.BytesIO(doc.getvalue()))
                for p in d.paragraphs:
                    active_text += p.text + "\n"
            else:
                active_text = doc.getvalue().decode("utf-8", errors="ignore")
            st.sidebar.text_area("Document text", active_text[:2000], height=150)
        except Exception as e:
            st.sidebar.error(f"Could not read document: {e}")

elif menu == "AI Studio":
    st.sidebar.info("AI Studio - Create / Edit Images")
    ai_style = st.sidebar.selectbox("Image Style", ["Realistic", "Anime", "3D Cartoon", "Oil Painting", "Cyberpunk", "Logo Style", "Poster"])
    ai_size = st.sidebar.selectbox("Size", ["Square", "Portrait", "Landscape"])
    st.sidebar.caption("Write in chat: draw a ... and Alex will create it in this style")

elif menu == "Voice":
    voice = st.sidebar.audio_input("Voice - Record your question")
    if voice is not None:
        active_bytes = voice.getvalue()
        active_type = "audio"
        st.sidebar.success("Voice recorded!")
        st.sidebar.audio(voice)
    up_audio = st.sidebar.file_uploader("Or upload audio", type=["mp3", "wav", "m4a", "ogg"])
    if up_audio is not None:
        active_bytes = up_audio.getvalue()
        active_type = up_audio.type
        st.sidebar.audio(up_audio)

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("image") is not None:
            st.image(msg["image"], width=400)

SYSTEM = f"""
You are Alex. You talk exactly like Meta AI - warm, friendly, playful, smart, and helpful.
Personality: Talk like a close smart friend, not like a boring textbook. Use "we" and "let's" a lot. Be short and dense, no useless long intro. Lead with the best point. If user is joking, joke back. Match their energy.
Language: If user writes in Egyptian Arabic, answer in Egyptian Arabic, friendly and casual. If English, answer in English.
Tutor Rules: Student grade: {grade}, Subject: {subject}, Style: {style}
Understand question even with spelling mistakes or slang. Explain step by step with examples.
For Math / Physics / Chemistry, show formulas and all steps and final answer.
For homework image, solve what is in the image fully.
For video, describe what happens and explain it.
For audio / voice, transcribe it exactly then answer it.
For document text, summarize, explain, and answer questions about it.
Creator Rules: If user asks to draw, generate, edit, or improve an image, be creative. Keep the person / main subject identical when editing. Style: {ai_style}
"""

prompt = st.chat_input("Talk to me... ask, attach, or ask to draw")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
        if active_bytes is not None and active_type == "image":
            st.image(active_bytes, width=300)

    with st.chat_message("assistant"):
        with st.spinner("Alex is thinking..."):
            try:
                lower = prompt.lower()
                is_image_req = any(k in lower for k in ["draw", "generate", "create", "make", "edit", "improve", "picture", "photo", "image", "poster", "logo"])

                if is_image_req and ("draw" in lower or "generate" in lower or "create" in lower or "make" in lower or "edit" in lower or "improve" in lower or "poster" in lower or "logo" in lower):
                    if active_bytes is not None and active_type == "image":
                        img = Image.open(io.BytesIO(active_bytes))
                        img_contents = [img, f"Edit / improve this image: {prompt}. Style: {ai_style}. Keep the person / main subject identical, high quality."]
                        response = client.models.generate_content(model="gemini-2.5-flash-image", contents=img_contents)
                    else:
                        response = client.models.generate_content(model="gemini-2.5-flash-image", contents=[f"Create a high quality image, Style: {ai_style}: {prompt}"])

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
                    if active_text:
                        contents.append(f"Document content:\n{active_text}\n\nQuestion: {prompt}")
                    elif active_bytes is not None:
                        if active_type == "image" or (isinstance(active_type, str) and active_type.startswith("image")):
                            img = Image.open(io.BytesIO(active_bytes))
                            contents.append(img)
                            contents.append(f"Look at this photo, solve / explain what is in it, and answer: {prompt}")
                        elif isinstance(active_type, str) and active_type.startswith("video"):
                            g_file = client.files.upload(file=io.BytesIO(active_bytes), config={"mime_type": active_type})
                            contents.append(g_file)
                            contents.append(f"Watch this video, describe everything happening, and answer: {prompt}")
                        elif active_type == "audio" or (isinstance(active_type, str) and active_type.startswith("audio")):
                            mime = "audio/wav" if active_type == "audio" else active_type
                            g_file = client.files.upload(file=io.BytesIO(active_bytes), config={"mime_type": mime})
                            contents.append(g_file)
                            contents.append(f"Listen to this voice, transcribe it exactly, then explain and answer: {prompt}")
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
