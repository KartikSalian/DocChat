"""
DocChat — RAG-powered PDF chatbot
Streamlit front-end wired to the RAGEngine backend.
"""

import os

import streamlit as st
from dotenv import load_dotenv

from rag_engine import RAGEngine

# ── Env & page config ─────────────────────────────────────────────────────────
load_dotenv()

st.set_page_config(
    page_title="DocChat",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS (minimal, professional) ────────────────────────────────────────
st.markdown(
    """
    <style>
    /* Chat bubble base */
    .chat-bubble {
        padding: 0.75rem 1rem;
        border-radius: 0.75rem;
        margin-bottom: 0.5rem;
        max-width: 85%;
        line-height: 1.5;
        font-size: 0.95rem;
    }
    .user-bubble {
        background: #2563eb;
        color: #ffffff;
        margin-left: auto;
        border-bottom-right-radius: 0.2rem;
    }
    .assistant-bubble {
        background: #f1f5f9;
        color: #1e293b;
        border-bottom-left-radius: 0.2rem;
    }
    .source-box {
        background: #fefce8;
        border-left: 3px solid #eab308;
        padding: 0.5rem 0.75rem;
        border-radius: 0.375rem;
        font-size: 0.8rem;
        color: #713f12;
        margin-top: 0.25rem;
    }
    /* Make the sidebar upload area nicer */
    section[data-testid="stSidebar"] .stFileUploader label {
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ── Session state initialisation ──────────────────────────────────────────────
def init_session() -> None:
    if "rag" not in st.session_state:
        st.session_state.rag = RAGEngine()
    if "messages" not in st.session_state:
        st.session_state.messages = []  # list of {"role", "content", "sources"}
    if "pdf_name" not in st.session_state:
        st.session_state.pdf_name = None
    if "chunk_count" not in st.session_state:
        st.session_state.chunk_count = 0
    if "model_ready" not in st.session_state:
        st.session_state.model_ready = False


init_session()

# Pre-warm the embedding model once at startup
if not st.session_state.model_ready:
    with st.spinner("Loading AI models for the first time (once only)…"):
        _ = st.session_state.rag.embed_model  # triggers download + load
        st.session_state.model_ready = True
rag: RAGEngine = st.session_state.rag


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("📄 DocChat")
    st.caption("Ask questions about any PDF — powered by free AI.")
    st.divider()

    uploaded_file = st.file_uploader(
        "Upload a PDF",
        type=["pdf"],
        help="Upload a PDF document to start chatting with it.",
    )

    if uploaded_file is not None:
        if uploaded_file.name != st.session_state.pdf_name:
            # New file — re-ingest
            with st.spinner("Reading and indexing PDF…"):
                try:
                    file_bytes = uploaded_file.read()
                    chunk_count = rag.ingest_pdf(file_bytes)
                    st.session_state.pdf_name = uploaded_file.name
                    st.session_state.chunk_count = chunk_count
                    st.session_state.messages = []  # reset chat for new doc
                    st.success(
                        f"✅ Indexed **{uploaded_file.name}**  \n"
                        f"{chunk_count} chunks created."
                    )
                except ValueError as e:
                    st.error(f"PDF Error: {e}")
                except Exception as e:
                    st.error(f"Unexpected error while processing PDF: {e}")
        else:
            st.success(
                f"✅ **{st.session_state.pdf_name}** loaded  \n"
                f"{st.session_state.chunk_count} chunks indexed."
            )

    st.divider()

    # Clear chat button
    if st.button("🗑️ Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.divider()

    # Settings / info panel
    with st.expander("ℹ️ About", expanded=False):
        st.markdown(
            """
            **DocChat** uses a fully free stack:

            - 🧠 **LLM**: Zephyr-7B-β via HF Inference API
            - 🔍 **Embeddings**: all-MiniLM-L6-v2 (local)
            - 📦 **Vector store**: FAISS (in-memory)
            - 🦜 **Orchestration**: LangChain

            Your HF token is read from the `HUGGINGFACE_TOKEN`
            environment variable or Spaces secret.
            """
        )

    # Token check indicator
    groq_key = os.getenv("GROQ_API_KEY", "")
    if groq_key:
        st.caption("🔑 Groq key: detected")
    else:
        st.warning("⚠️ No Groq key found. Set `GROQ_API_KEY` in `.env`.")


# ── Main area ─────────────────────────────────────────────────────────────────
st.header("💬 Chat with your document")

if not rag.is_ready():
    st.info("👈 Upload a PDF in the sidebar to get started.")
    st.stop()

# ── Render message history ────────────────────────────────────────────────────
for msg in st.session_state.messages:
    role = msg["role"]
    content = msg["content"]
    sources = msg.get("sources", [])

    if role == "user":
        with st.chat_message("user"):
            st.write(content)
    else:
        with st.chat_message("assistant", avatar="📄"):
            st.write(content)
            if sources:
                with st.expander(f"📚 Sources ({len(sources)} chunks used)", expanded=False):
                    for i, src in enumerate(sources, 1):
                        st.markdown(
                            f'<div class="source-box">'
                            f'<strong>Chunk {i}:</strong> {src}'
                            f'</div>',
                            unsafe_allow_html=True,
                        )

# ── Chat input ────────────────────────────────────────────────────────────────
user_question = st.chat_input(
    "Ask a question about the document…",
    disabled=not rag.is_ready(),
)

if user_question:
    user_question = user_question.strip()

    if not user_question:
        st.warning("Please type a question before sending.")
        st.stop()

    # Append user message
    st.session_state.messages.append(
        {"role": "user", "content": user_question, "sources": []}
    )
    with st.chat_message("user"):
        st.write(user_question)

    # Generate answer
    with st.chat_message("assistant", avatar="📄"):
        with st.spinner("Thinking…"):
            try:
                result = rag.answer(user_question)
                answer = result["answer"]
                sources = result["sources"]

                st.write(answer)

                if sources:
                    with st.expander(
                        f"📚 Sources ({len(sources)} chunks used)", expanded=False
                    ):
                        for i, src in enumerate(sources, 1):
                            st.markdown(
                                f'<div class="source-box">'
                                f'<strong>Chunk {i}:</strong> {src}'
                                f'</div>',
                                unsafe_allow_html=True,
                            )

                # Persist to history
                st.session_state.messages.append(
                    {"role": "assistant", "content": answer, "sources": sources}
                )

            except ValueError as e:
                err_msg = f"⚠️ {e}"
                st.error(err_msg)
                st.session_state.messages.append(
                    {"role": "assistant", "content": err_msg, "sources": []}
                )
            except RuntimeError as e:
                err_msg = f"🔴 API Error: {e}"
                st.error(err_msg)
                st.session_state.messages.append(
                    {"role": "assistant", "content": err_msg, "sources": []}
                )
            except Exception as e:
                err_msg = f"❌ Unexpected error: {e}"
                st.error(err_msg)
                st.session_state.messages.append(
                    {"role": "assistant", "content": err_msg, "sources": []}
                )
