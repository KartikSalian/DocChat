"""
DocChat — RAG-powered PDF chatbot
Streamlit front-end wired to the RAGEngine backend.
"""

import os

import streamlit as st
from dotenv import load_dotenv

from rag_engine import RAGEngine

load_dotenv()

st.set_page_config(
    page_title="DocChat",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* ── CSS Variables for light / dark ── */
:root {
    --ruby:       #C0392B;
    --ruby-light: #E74C3C;
    --ruby-dim:   #922B21;
    --bg:         #ffffff;
    --bg2:        #f7f7f8;
    --bg3:        #efefef;
    --border:     #e0e0e0;
    --text:       #111111;
    --text2:      #555555;
    --text3:      #888888;
    --card:       #f9f9f9;
    --shadow:     0 2px 12px rgba(0,0,0,0.07);
}

@media (prefers-color-scheme: dark) {
    :root {
        --bg:     #0d0d0d;
        --bg2:    #141414;
        --bg3:    #1c1c1c;
        --border: #2a2a2a;
        --text:   #f0f0f0;
        --text2:  #aaaaaa;
        --text3:  #555555;
        --card:   #161616;
        --shadow: 0 2px 12px rgba(0,0,0,0.4);
    }
}

/* ── Base ── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
    background: var(--bg) !important;
    color: var(--text) !important;
}

#MainMenu, footer, header { visibility: hidden; }

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: var(--bg2) !important;
    border-right: 1px solid var(--border) !important;
    padding-top: 1rem;
}
section[data-testid="stSidebar"] * {
    color: var(--text) !important;
}

/* ── Logo ── */
.dc-logo {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    margin-bottom: 0.25rem;
}
.dc-logo-icon {
    width: 36px;
    height: 36px;
    background: linear-gradient(135deg, var(--ruby), var(--ruby-light));
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.1rem;
    box-shadow: 0 2px 8px rgba(192,57,43,0.4);
    flex-shrink: 0;
}
.dc-logo-text {
    font-size: 1.2rem;
    font-weight: 700;
    color: var(--text) !important;
    letter-spacing: -0.3px;
}
.dc-logo-text span {
    color: var(--ruby) !important;
}
.dc-tagline {
    font-size: 0.75rem;
    color: var(--text3) !important;
    margin-bottom: 1.5rem;
    margin-top: 0.1rem;
    padding-left: 0.25rem;
}

/* ── Upload zone ── */
[data-testid="stFileUploader"] {
    background: var(--bg3) !important;
    border: 1.5px dashed var(--border) !important;
    border-radius: 12px !important;
    padding: 0.25rem !important;
    transition: border-color 0.2s;
}
[data-testid="stFileUploader"]:hover {
    border-color: var(--ruby) !important;
}
[data-testid="stFileUploaderDropzoneInstructions"] {
    font-size: 0.8rem !important;
    color: var(--text2) !important;
}

/* ── Buttons ── */
.stButton > button {
    background: var(--bg3) !important;
    color: var(--text2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    font-size: 0.78rem !important;
    font-weight: 500 !important;
    padding: 0.35rem 1rem !important;
    transition: all 0.15s ease !important;
}
.stButton > button:hover {
    border-color: var(--ruby) !important;
    color: var(--ruby) !important;
    background: var(--bg2) !important;
}

/* ── Chat input ── */
[data-testid="stChatInput"] textarea {
    background: var(--bg2) !important;
    color: var(--text) !important;
    border: 1.5px solid var(--border) !important;
    border-radius: 12px !important;
    font-family: 'Inter', sans-serif !important;
}
[data-testid="stChatInput"] textarea:focus {
    border-color: var(--ruby) !important;
    box-shadow: 0 0 0 3px rgba(192,57,43,0.12) !important;
}
[data-testid="stChatInputSubmitButton"] svg { fill: var(--ruby) !important; }

/* ── Chat messages ── */
[data-testid="stChatMessage"] {
    background: transparent !important;
    border: none !important;
    padding: 0.2rem 0 !important;
}

/* Bot avatar — ruby gem */
[data-testid="stChatMessage"] [data-testid="chatAvatarIcon-assistant"] {
    background: linear-gradient(135deg, var(--ruby), var(--ruby-light)) !important;
    border-radius: 10px !important;
    box-shadow: 0 2px 8px rgba(192,57,43,0.35) !important;
}

/* ── Assistant bubble ── */
.assistant-bubble {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 0 14px 14px 14px;
    padding: 0.85rem 1.1rem;
    font-size: 0.92rem;
    line-height: 1.65;
    color: var(--text);
    box-shadow: var(--shadow);
    max-width: 100%;
}

/* ── Source expander ── */
.streamlit-expanderHeader {
    background: var(--bg2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    font-size: 0.76rem !important;
    color: var(--text3) !important;
    font-weight: 500 !important;
}
.streamlit-expanderContent {
    background: var(--bg2) !important;
    border: 1px solid var(--border) !important;
    border-top: none !important;
    border-radius: 0 0 8px 8px !important;
}

/* ── Source card ── */
.src-card {
    background: var(--bg3);
    border-left: 2px solid var(--ruby);
    border-radius: 6px;
    padding: 0.5rem 0.75rem;
    margin-bottom: 0.4rem;
    font-size: 0.76rem;
    color: var(--text2);
    line-height: 1.55;
}

/* ── Empty state ── */
.empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 62vh;
    gap: 0.75rem;
    text-align: center;
    padding: 1rem;
}
.empty-icon {
    width: 64px;
    height: 64px;
    background: linear-gradient(135deg, var(--ruby), var(--ruby-light));
    border-radius: 18px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.8rem;
    box-shadow: 0 4px 20px rgba(192,57,43,0.3);
    margin-bottom: 0.5rem;
}
.empty-title {
    font-size: 1.4rem;
    font-weight: 600;
    color: var(--text);
    margin: 0;
}
.empty-sub {
    font-size: 0.88rem;
    color: var(--text3);
    margin: 0;
    max-width: 280px;
}

/* ── Mobile responsiveness ── */
@media (max-width: 768px) {
    .main .block-container {
        padding: 1rem 0.75rem 5rem !important;
    }
    .empty-title { font-size: 1.1rem; }
    .assistant-bubble { font-size: 0.87rem; }
    section[data-testid="stSidebar"] {
        min-width: 260px !important;
    }
}

/* ── Main container ── */
.main .block-container {
    max-width: 800px;
    padding-top: 1.5rem;
    padding-bottom: 5rem;
}

/* ── Status badge ── */
.status-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    background: rgba(192,57,43,0.1);
    border: 1px solid rgba(192,57,43,0.2);
    border-radius: 20px;
    padding: 0.25rem 0.75rem;
    font-size: 0.72rem;
    color: var(--ruby);
    font-weight: 500;
    margin-top: 0.5rem;
}
.status-dot {
    width: 6px;
    height: 6px;
    background: var(--ruby);
    border-radius: 50%;
    animation: pulse 2s infinite;
}
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
}
</style>
""", unsafe_allow_html=True)


# ── Session state ─────────────────────────────────────────────────────────────
def init_session() -> None:
    if "rag" not in st.session_state:
        st.session_state.rag = RAGEngine()
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "pdf_name" not in st.session_state:
        st.session_state.pdf_name = None
    if "chunk_count" not in st.session_state:
        st.session_state.chunk_count = 0
    if "model_ready" not in st.session_state:
        st.session_state.model_ready = False


init_session()
rag: RAGEngine = st.session_state.rag

if not st.session_state.model_ready:
    with st.spinner("Loading models…"):
        _ = st.session_state.rag.embed_model
        st.session_state.model_ready = True


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    # Logo
    st.markdown("""
    <div class="dc-logo">
        <div class="dc-logo-icon">💎</div>
        <div class="dc-logo-text">Doc<span>Chat</span></div>
    </div>
    <div class="dc-tagline">Chat with any PDF using AI</div>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Upload PDF",
        type=["pdf"],
        label_visibility="collapsed",
    )

    if uploaded_file is not None:
        if uploaded_file.name != st.session_state.pdf_name:
            with st.spinner("Indexing document…"):
                try:
                    chunk_count = rag.ingest_pdf(uploaded_file.read())
                    st.session_state.pdf_name = uploaded_file.name
                    st.session_state.chunk_count = chunk_count
                    st.session_state.messages = []
                    st.success(f"✓ Indexed · {chunk_count} chunks")
                except ValueError as e:
                    st.error(str(e))
                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            st.markdown(
                f'<div class="status-badge"><div class="status-dot"></div>'
                f'{st.session_state.pdf_name[:22]}{"…" if len(st.session_state.pdf_name) > 22 else ""}'
                f' · {st.session_state.chunk_count} chunks</div>',
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height:0.75rem'></div>", unsafe_allow_html=True)

    if st.session_state.messages:
        if st.button("Clear conversation", use_container_width=True):
            st.session_state.messages = []
            st.rerun()


# ── Main ──────────────────────────────────────────────────────────────────────
if not rag.is_ready():
    st.markdown("""
    <div class="empty-state">
        <div class="empty-icon">💎</div>
        <h2 class="empty-title">Upload a PDF to begin</h2>
        <p class="empty-sub">Drop any document in the sidebar and start asking questions instantly</p>
    </div>
    """, unsafe_allow_html=True)
    st.chat_input("Ask anything about the document…", disabled=True)
    st.stop()

# ── Message history ───────────────────────────────────────────────────────────
for msg in st.session_state.messages:
    avatar = "🧑" if msg["role"] == "user" else "💎"
    with st.chat_message(msg["role"], avatar=avatar):
        st.write(msg["content"])
        if msg["role"] == "assistant" and msg.get("sources"):
            with st.expander(f"Sources · {len(msg['sources'])} chunks", expanded=False):
                for i, src in enumerate(msg["sources"], 1):
                    st.markdown(
                        f'<div class="src-card"><strong>#{i}</strong>&nbsp;&nbsp;{src}</div>',
                        unsafe_allow_html=True,
                    )

# ── Chat input ────────────────────────────────────────────────────────────────
question = st.chat_input("Ask anything about the document…")

if question:
    question = question.strip()
    if not question:
        st.stop()

    st.session_state.messages.append({"role": "user", "content": question, "sources": []})
    with st.chat_message("user", avatar="🧑"):
        st.write(question)

    with st.chat_message("assistant", avatar="💎"):
        with st.spinner(""):
            try:
                result = rag.answer(question)
                answer = result["answer"]
                sources = result["sources"]

                st.write(answer)
                if sources:
                    with st.expander(f"Sources · {len(sources)} chunks", expanded=False):
                        for i, src in enumerate(sources, 1):
                            st.markdown(
                                f'<div class="src-card"><strong>#{i}</strong>&nbsp;&nbsp;{src}</div>',
                                unsafe_allow_html=True,
                            )

                st.session_state.messages.append(
                    {"role": "assistant", "content": answer, "sources": sources}
                )
            except (ValueError, RuntimeError) as e:
                err = str(e)
                st.error(err)
                st.session_state.messages.append(
                    {"role": "assistant", "content": f"Error: {err}", "sources": []}
                )
            except Exception as e:
                err = f"Unexpected error: {e}"
                st.error(err)
                st.session_state.messages.append(
                    {"role": "assistant", "content": err, "sources": []}
                )
