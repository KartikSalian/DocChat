"""
DocChat — RAG-powered PDF chatbot
Streamlit front-end: chat history + multi-document support.
"""

import os
import uuid

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

:root {
    --ruby:  #C0392B;
    --ruby2: #E74C3C;
    --bg:    #0d0d0d;
    --bg2:   #141414;
    --bg3:   #1c1c1c;
    --brd:   #2a2a2a;
    --txt:   #f0f0f0;
    --txt2:  #aaaaaa;
    --txt3:  #555555;
    --shad:  0 2px 12px rgba(0,0,0,0.4);
}

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
}

#MainMenu, footer, header { visibility: hidden; }

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: var(--bg2) !important;
    border-right: 1px solid var(--brd) !important;
    width: 280px !important;
}
section[data-testid="stSidebar"] * { color: var(--txt) !important; }

/* ── Logo ── */
.dc-logo {
    display: flex; align-items: center; gap: .6rem; margin-bottom: .15rem;
}
.dc-logo-icon {
    width: 34px; height: 34px;
    background: linear-gradient(135deg, var(--ruby), var(--ruby2));
    border-radius: 9px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1rem;
    box-shadow: 0 2px 8px rgba(192,57,43,.4);
    flex-shrink: 0;
}
.dc-logo-text { font-size: 1.1rem; font-weight: 700; letter-spacing: -.3px; }
.dc-logo-text span { color: var(--ruby) !important; }
.dc-tag { font-size: .72rem; color: var(--txt3) !important; margin-bottom: 1rem; padding-left:.25rem; }

/* ── New chat button ── */
.new-chat-btn > button {
    background: linear-gradient(135deg, var(--ruby), var(--ruby2)) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 8px !important;
    font-size: .8rem !important;
    font-weight: 600 !important;
    padding: .45rem 1rem !important;
    width: 100% !important;
    margin-bottom: .75rem !important;
    transition: opacity .15s !important;
}
.new-chat-btn > button:hover { opacity: .88 !important; }

/* ── History items ── */
.hist-item {
    display: flex; align-items: center; justify-content: space-between;
    padding: .45rem .65rem;
    border-radius: 7px;
    cursor: pointer;
    margin-bottom: .2rem;
    transition: background .15s;
    border: 1px solid transparent;
}
.hist-item:hover  { background: var(--bg3); }
.hist-item.active { background: var(--bg3); border-color: var(--ruby); }
.hist-title { font-size: .78rem; color: var(--txt2) !important; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 170px; }
.hist-title.active { color: var(--txt) !important; font-weight: 500; }
.hist-del { font-size: .7rem; color: var(--txt3) !important; cursor: pointer; flex-shrink:0; }
.hist-section { font-size: .65rem; color: var(--txt3) !important; font-weight:600; letter-spacing:.05em; text-transform:uppercase; margin: .75rem 0 .3rem; padding-left:.25rem; }

/* ── Docs list ── */
.doc-pill {
    display: inline-flex; align-items: center; gap: .35rem;
    background: var(--bg3); border: 1px solid var(--brd);
    border-radius: 20px; padding: .2rem .6rem;
    font-size: .7rem; color: var(--txt2) !important;
    margin: .15rem .1rem;
}
.doc-dot { width:6px; height:6px; background:var(--ruby); border-radius:50%; flex-shrink:0; }

/* ── Upload ── */
[data-testid="stFileUploader"] {
    background: var(--bg3) !important;
    border: 1.5px dashed var(--brd) !important;
    border-radius: 10px !important;
}
[data-testid="stFileUploader"]:hover { border-color: var(--ruby) !important; }

/* ── Regular buttons ── */
.stButton > button {
    background: var(--bg3) !important; color: var(--txt2) !important;
    border: 1px solid var(--brd) !important; border-radius: 8px !important;
    font-size: .78rem !important; font-weight: 500 !important;
    transition: all .15s !important;
}
.stButton > button:hover { border-color: var(--ruby) !important; color: var(--ruby) !important; }

/* ── Chat input ── */
[data-testid="stChatInput"] textarea {
    background: var(--bg2) !important; color: var(--txt) !important;
    border: 1.5px solid var(--brd) !important; border-radius: 12px !important;
    font-family: 'Inter', sans-serif !important;
}
[data-testid="stChatInput"] textarea:focus { border-color: var(--ruby) !important; }
[data-testid="stChatInputSubmitButton"] svg { fill: var(--ruby) !important; }

/* ── Messages ── */
[data-testid="stChatMessage"] { background: transparent !important; border: none !important; padding: .2rem 0 !important; }

/* ── Source expander ── */
.streamlit-expanderHeader {
    background: var(--bg2) !important; border: 1px solid var(--brd) !important;
    border-radius: 8px !important; font-size: .75rem !important; color: var(--txt3) !important;
}
.streamlit-expanderContent {
    background: var(--bg2) !important; border: 1px solid var(--brd) !important;
    border-top: none !important; border-radius: 0 0 8px 8px !important;
}
.src-card {
    background: var(--bg3); border-left: 2px solid var(--ruby);
    border-radius: 6px; padding: .5rem .75rem; margin-bottom: .35rem;
    font-size: .74rem; color: var(--txt2); line-height: 1.5;
}
.src-from { font-size: .65rem; color: var(--ruby) !important; margin-bottom: .2rem; font-weight:600; }

/* ── Empty state ── */
.empty-state {
    display:flex; flex-direction:column; align-items:center;
    justify-content:center; height:60vh; gap:.75rem; text-align:center; padding:1rem;
}
.empty-icon {
    width:60px; height:60px;
    background: linear-gradient(135deg,var(--ruby),var(--ruby2));
    border-radius:16px; display:flex; align-items:center; justify-content:center;
    font-size:1.6rem; box-shadow:0 4px 20px rgba(192,57,43,.3); margin-bottom:.5rem;
}
.empty-title { font-size:1.3rem; font-weight:600; color:var(--txt); margin:0; }
.empty-sub   { font-size:.85rem; color:var(--txt3); margin:0; max-width:260px; }

/* ── Main ── */
.main .block-container { max-width:800px; padding-top:1.5rem; padding-bottom:5rem; }

/* ── Mobile ── */
@media(max-width:768px){
    .main .block-container { padding:1rem .75rem 5rem !important; }
    section[data-testid="stSidebar"] { width:260px !important; }
}
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────
def new_chat() -> dict:
    return {"id": str(uuid.uuid4()), "title": "New chat", "messages": [], "rag": RAGEngine()}


def get_current() -> dict:
    return st.session_state.chats[st.session_state.active_id]


# ── Session state ─────────────────────────────────────────────────────────────
if "chats" not in st.session_state:
    first = new_chat()
    st.session_state.chats = {first["id"]: first}
    st.session_state.active_id = first["id"]

if "model_ready" not in st.session_state:
    st.session_state.model_ready = False

# Pre-warm embedding model using any RAGEngine instance
if not st.session_state.model_ready:
    with st.spinner("Loading models…"):
        _ = get_current()["rag"].embed_model
        st.session_state.model_ready = True

chat = get_current()
rag: RAGEngine = chat["rag"]


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    # Logo
    st.markdown("""
    <div class="dc-logo">
        <div class="dc-logo-icon">💎</div>
        <div class="dc-logo-text">Doc<span>Chat</span></div>
    </div>
    <div class="dc-tag">Chat with any PDF using AI</div>
    """, unsafe_allow_html=True)

    # New chat
    st.markdown('<div class="new-chat-btn">', unsafe_allow_html=True)
    if st.button("＋  New chat", use_container_width=True):
        c = new_chat()
        st.session_state.chats[c["id"]] = c
        st.session_state.active_id = c["id"]
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # History list
    st.markdown('<div class="hist-section">Recent</div>', unsafe_allow_html=True)
    for cid, c in reversed(list(st.session_state.chats.items())):
        is_active = cid == st.session_state.active_id
        active_cls = "active" if is_active else ""
        col1, col2 = st.columns([5, 1])
        with col1:
            if st.button(
                c["title"],
                key=f"hist_{cid}",
                use_container_width=True,
            ):
                st.session_state.active_id = cid
                st.rerun()
        with col2:
            if st.button("✕", key=f"del_{cid}"):
                del st.session_state.chats[cid]
                if st.session_state.active_id == cid:
                    if st.session_state.chats:
                        st.session_state.active_id = list(st.session_state.chats)[-1]
                    else:
                        c2 = new_chat()
                        st.session_state.chats[c2["id"]] = c2
                        st.session_state.active_id = c2["id"]
                st.rerun()

    st.divider()

    # Upload docs for current chat
    st.markdown('<div style="font-size:.72rem;color:#555;font-weight:600;text-transform:uppercase;letter-spacing:.05em;margin-bottom:.4rem;">Documents</div>', unsafe_allow_html=True)

    uploaded_files = st.file_uploader(
        "Upload PDFs",
        type=["pdf"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )

    if uploaded_files:
        for uf in uploaded_files:
            if uf.name not in rag.indexed_docs():
                with st.spinner(f"Indexing {uf.name}…"):
                    try:
                        rag.add_document(uf.read(), uf.name)
                        st.success(f"✓ {uf.name}")
                    except Exception as e:
                        st.error(f"{uf.name}: {e}")

    # Show indexed docs
    if rag.indexed_docs():
        for doc in rag.indexed_docs():
            st.markdown(
                f'<div class="doc-pill"><div class="doc-dot"></div>{doc[:28]}{"…" if len(doc)>28 else ""}</div>',
                unsafe_allow_html=True,
            )


# ── Re-fetch after potential switch ──────────────────────────────────────────
chat = get_current()
rag  = chat["rag"]

# ── Main area ─────────────────────────────────────────────────────────────────
if not rag.is_ready():
    st.markdown("""
    <div class="empty-state">
        <div class="empty-icon">💎</div>
        <h2 class="empty-title">Upload a PDF to begin</h2>
        <p class="empty-sub">Drop one or more documents in the sidebar and start asking questions</p>
    </div>
    """, unsafe_allow_html=True)
    st.chat_input("Ask anything about the document…", disabled=True)
    st.stop()

# ── Message history ───────────────────────────────────────────────────────────
for msg in chat["messages"]:
    avatar = "🧑" if msg["role"] == "user" else "💎"
    with st.chat_message(msg["role"], avatar=avatar):
        st.write(msg["content"])
        if msg["role"] == "assistant" and msg.get("sources"):
            with st.expander(f"Sources · {len(msg['sources'])} chunks", expanded=False):
                for i, h in enumerate(msg["sources"], 1):
                    st.markdown(
                        f'<div class="src-card">'
                        f'<div class="src-from">📄 {h["source"]}</div>'
                        f'<strong>#{i}</strong>&nbsp; {h["text"]}'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

# ── Input ─────────────────────────────────────────────────────────────────────
question = st.chat_input("Ask anything about the document…")

if question:
    question = question.strip()
    if not question:
        st.stop()

    # Auto-title from first question
    if chat["title"] == "New chat":
        chat["title"] = question[:40] + ("…" if len(question) > 40 else "")

    chat["messages"].append({"role": "user", "content": question, "sources": []})
    with st.chat_message("user", avatar="🧑"):
        st.write(question)

    with st.chat_message("assistant", avatar="💎"):
        with st.spinner(""):
            try:
                result  = rag.answer(question)
                answer  = result["answer"]
                sources = result["sources"]

                st.write(answer)
                if sources:
                    with st.expander(f"Sources · {len(sources)} chunks", expanded=False):
                        for i, h in enumerate(sources, 1):
                            st.markdown(
                                f'<div class="src-card">'
                                f'<div class="src-from">📄 {h["source"]}</div>'
                                f'<strong>#{i}</strong>&nbsp; {h["text"]}'
                                f'</div>',
                                unsafe_allow_html=True,
                            )

                chat["messages"].append(
                    {"role": "assistant", "content": answer, "sources": sources}
                )
            except (ValueError, RuntimeError) as e:
                err = str(e)
                st.error(err)
                chat["messages"].append({"role": "assistant", "content": f"Error: {err}", "sources": []})
            except Exception as e:
                err = f"Unexpected error: {e}"
                st.error(err)
                chat["messages"].append({"role": "assistant", "content": err, "sources": []})
