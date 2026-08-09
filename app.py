import os
import tempfile

import streamlit as st
from dotenv import load_dotenv

from utils.audio_processor import process_input
from core.transcriber import transcribe_all
from core.summarize import summarize, generate_title
from core.extractor import extract_action_items, extract_key_decisions, extract_questions
from core.rag_engine import build_rag_chain, ask_question

load_dotenv()

st.set_page_config(page_title="AI Video Assistant", page_icon="🎬", layout="wide")

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
if "result" not in st.session_state:
    st.session_state.result = None
if "messages" not in st.session_state:
    st.session_state.messages = []  
if "processing" not in st.session_state:
    st.session_state.processing = False


def reset_session():
    st.session_state.result = None
    st.session_state.messages = []




def run_pipeline(source: str, language: str = "english", status=None) -> dict:
    def log(msg):
        if status is not None:
            status.write(msg)

    log("🎧 Processing audio/video input…")
    chunks = process_input(source)

    log("📝 Transcribing…")
    transcript = transcribe_all(chunks, language=language)

    log("🏷️ Generating title…")
    title = generate_title(transcript)

    log("📋 Summarizing…")
    summary = summarize(transcript)

    log("✅ Extracting action items…")
    action_items = extract_action_items(transcript)

    log("🔑 Extracting key decisions…")
    decisions = extract_key_decisions(transcript)

    log("❓ Extracting open questions…")
    questions = extract_questions(transcript)

    log("🔗 Building RAG chain for chat…")
    rag_chain = build_rag_chain(transcript)

    return {
        "title": title,
        "transcript": transcript,
        "summary": summary,
        "action_items": action_items,
        "key_decisions": decisions,
        "open_questions": questions,
        "rag_chain": rag_chain,
    }



with st.sidebar:
    st.title("🎬 AI Video Assistant")
    st.caption("Summarize, extract insights, and chat with any meeting or video.")

    st.divider()

    input_mode = st.radio("Source type", ["YouTube URL", "Upload a file"], horizontal=False)

    source = None
    if input_mode == "YouTube URL":
        source = st.text_input("YouTube URL", placeholder="https://youtube.com/watch?v=...")
    else:
        uploaded_file = st.file_uploader(
            "Upload audio/video file",
            type=["mp3", "wav", "m4a", "mp4", "mov", "mkv", "webm"],
        )
        if uploaded_file is not None:
            tmp_dir = tempfile.mkdtemp()
            tmp_path = os.path.join(tmp_dir, uploaded_file.name)
            with open(tmp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            source = tmp_path

    language = st.selectbox("Language", ["english", "hinglish"], index=0)

    st.divider()

    run_clicked = st.button("🚀 Run Analysis", type="primary", use_container_width=True, disabled=not source)
    clear_clicked = st.button("🗑️ Clear session", use_container_width=True)

    if clear_clicked:
        reset_session()
        st.rerun()

    if st.session_state.result:
        st.divider()
        st.success("Analysis ready ✅")

    st.write("Made by Sahil Omanwar🙂 ")


if run_clicked and source:
    reset_session()
    with st.status("Running pipeline…", expanded=True) as status:
        try:
            st.session_state.result = run_pipeline(source, language, status=status)
            status.update(label="Done!", state="complete", expanded=False)
        except Exception as e:
            status.update(label="Failed", state="error", expanded=True)
            st.error(f"Something went wrong: {e}")


result = st.session_state.result

if not result:
    st.title("🎬 AI Video Assistant")
    st.info("👈 Add a YouTube URL or upload a file in the sidebar, then click **Run Analysis** to get started.")
else:
    st.title(f"📌 {result['title']}")

    tab_summary, tab_actions, tab_decisions, tab_questions, tab_transcript, tab_chat = st.tabs(
        ["📋 Summary", "✅ Action Items", "🔑 Key Decisions", "❓ Open Questions", "📄 Transcript", "💬 Chat"]
    )

    with tab_summary:
        st.markdown(result["summary"])

    with tab_actions:
        st.markdown(result["action_items"])

    with tab_decisions:
        st.markdown(result["key_decisions"])

    with tab_questions:
        st.markdown(result["open_questions"])

    with tab_transcript:
        st.text_area("Full transcript", result["transcript"], height=500)
        st.download_button(
            "⬇️ Download transcript",
            result["transcript"],
            file_name="transcript.txt",
            mime="text/plain",
        )

    with tab_chat:
        st.caption("Ask questions about the video/meeting content.")

        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        question = st.chat_input("Ask something about this video…")
        if question:
            st.session_state.messages.append({"role": "user", "content": question})
            with st.chat_message("user"):
                st.markdown(question)

            with st.chat_message("assistant"):
                with st.spinner("Thinking…"):
                    try:
                        answer = ask_question(result["rag_chain"], question)
                    except Exception as e:
                        answer = f"⚠️ Error answering question: {e}"
                    st.markdown(answer)

            st.session_state.messages.append({"role": "assistant", "content": answer})


