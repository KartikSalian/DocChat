# DocChat — Chat with any PDF using AI

### Live Demo → [docchat-one.streamlit.app](https://docchat-one.streamlit.app)

> Upload any PDF and ask questions about it instantly.
> Powered by a **100% free** AI stack — no OpenAI, no paid APIs, zero cost.
> Now with an **OWASP LLM Top 10 security layer** built in.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.32-red?logo=streamlit)
![LangChain](https://img.shields.io/badge/LangChain-0.1-green?logo=chainlink)
![Groq](https://img.shields.io/badge/LLM-Groq%20Llama%203.1-orange)
![FAISS](https://img.shields.io/badge/Vector_Store-FAISS-blueviolet)
![Security](https://img.shields.io/badge/Security-OWASP%20LLM%20Top%2010-red)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

---

## What is DocChat?

DocChat is a **Retrieval-Augmented Generation (RAG)** chatbot that lets you have a conversation with your PDF documents. Upload one or more PDFs, ask questions in plain English, and get accurate answers with the exact source chunks highlighted.

Unlike simply sending a PDF to an LLM, DocChat uses semantic vector search to find the most relevant sections of your document before generating an answer — making responses faster, cheaper, and more grounded in the actual content.

---

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                        USER                              │
│                    (Streamlit UI)                        │
└─────────────────────────┬────────────────────────────────┘
                          │  PDF upload / question
                          ▼
┌──────────────────────────────────────────────────────────┐
│                   security.py                            │
│           OWASP LLM Security Layer (Pre-inference)       │
│  • LLM01: Prompt injection detection                     │
│  • LLM04: Input length / DoS throttling                  │
│  • LLM06: System prompt extraction detection             │
│  • Input sanitisation (null bytes, HTML tags)            │
└─────────────────────────┬────────────────────────────────┘
                          │  Clean, validated input
                          ▼
┌──────────────────────────────────────────────────────────┐
│                   rag_engine.py                          │
│                   RAGEngine class                        │
│                                                          │
│  ┌───────────┐   ┌──────────────┐   ┌─────────────────┐ │
│  │  PyPDF2   │──▶│  LangChain   │──▶│  FAISS          │ │
│  │ PDF parse │   │ Text splitter│   │  Vector store   │ │
│  └───────────┘   └──────────────┘   └────────┬────────┘ │
│                                               │          │
│  ┌────────────────────────────────┐           │          │
│  │ sentence-transformers (local)  │◀──────────┘          │
│  │ all-MiniLM-L6-v2              │  embed + search       │
│  └────────────────────────────────┘                      │
│                                                          │
│  ┌────────────────────────────────┐                      │
│  │ Groq Inference API (free)      │  top-3 chunks + Q    │
│  │ Llama 3.1 8B Instant           │─────────────────────▶│
│  └────────────────────────────────┘                      │
└─────────────────────────┬────────────────────────────────┘
                          │  LLM response
                          ▼
┌──────────────────────────────────────────────────────────┐
│                   security.py                            │
│           OWASP LLM Security Layer (Post-inference)      │
│  • LLM02: PII / credential leakage detection             │
│  • LLM02: Harmful content scanning                       │
│  • System prompt echo detection                          │
└─────────────────────────┬────────────────────────────────┘
                          │
                          ▼
             Answer + source chunks returned to user
```

---

## Security Layer — OWASP LLM Top 10

DocChat implements a **pre and post-inference security pipeline** based on the [OWASP LLM Top 10](https://owasp.org/www-project-top-10-for-large-language-model-applications/).

| OWASP ID | Vulnerability | How DocChat mitigates it |
|---|---|---|
| LLM01 | Prompt Injection | Regex detection of 10+ attack patterns — instruction overrides, persona hijacking, DAN jailbreaks, indirect injection triggers |
| LLM02 | Insecure Output Handling | Post-inference scanning for PII (credit cards, SSNs), credentials, and harmful content before response is shown |
| LLM04 | Model Denial of Service | Input length capped at 2000 characters — oversized inputs rejected before hitting the API |
| LLM06 | Sensitive Info Disclosure | Detects system prompt extraction attempts ("reveal your instructions", "what were you told") |

### How it works

Every query passes through two checkpoints:

**Pre-inference (input check)**
```
User input → sanitise_input() → check_input() → [BLOCK or PASS] → RAG pipeline
```

**Post-inference (output check)**
```
LLM response → check_output() → [BLOCK or PASS] → User sees answer
```

When a threat is detected, the user sees a severity-labelled warning instead of the response:
- 🔴 **HIGH** — prompt injection, PII leakage, credential exposure
- 🟠 **MEDIUM** — input DoS attempt
- 🟡 **LOW** — suspicious but inconclusive patterns

---

## Features

- **Multi-PDF support** — upload and query multiple documents in one session
- **Chat history** — switch between past conversations in the sidebar
- **Source transparency** — every answer shows the exact document chunks used
- **OWASP LLM security layer** — prompt injection detection, output scanning, DoS protection
- **100% free** — embeddings run locally; LLM inference uses Groq's free tier
- **No GPU required** — runs on CPU only
- **Dark mode** — clean minimal UI with ruby red theme
- **Mobile responsive** — works on phones and tablets

---

## Local Setup

### 1 — Clone the repo

```bash
git clone https://github.com/KartikSalian/DocChat.git
cd DocChat
```

### 2 — Install dependencies

```bash
pip install -r requirements.txt
```

### 3 — Get a free Groq API key

1. Go to [console.groq.com](https://console.groq.com) and sign up free
2. Click **API Keys → Create API Key**
3. Copy the key (starts with `gsk_...`)

### 4 — Configure your key

```bash
cp .env.example .env
# Open .env and paste your key:
# GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx
```

### 5 — Run the app

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## Deploy to Streamlit Community Cloud (Free)

1. Fork this repo to your GitHub account
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub
3. Click **Create app** and select this repo
4. Set **Main file path** to `app.py`
5. Click **Advanced settings → Secrets** and paste:
   ```
   GROQ_API_KEY = "gsk_xxxxxxxxxxxxxxxxxxxx"
   ```
6. Click **Deploy** — your app will be live in ~2 minutes

---

## Project Structure

```
DocChat/
├── app.py              # Streamlit UI (chat interface, history, upload)
├── rag_engine.py       # RAG pipeline (parse → chunk → embed → retrieve → generate)
├── security.py         # OWASP LLM Top 10 security layer (input + output checks)
├── assets/
│   └── logo.svg        # DocChat logo
├── .streamlit/
│   └── config.toml     # Theme configuration (ruby dark mode)
├── requirements.txt    # Pinned dependencies
├── .env.example        # API key template (safe to commit)
├── .gitignore          # Excludes .env, caches, indexes
└── README.md           # This file
```

---

## Tech Stack

| Component | Library / Service | Cost |
|---|---|---|
| UI | Streamlit 1.32 | Free |
| Orchestration | LangChain 0.1 | Free |
| PDF parsing | PyPDF2 3.0 | Free (local) |
| Embeddings | sentence-transformers all-MiniLM-L6-v2 | Free (local) |
| Vector store | FAISS-CPU 1.8 | Free (in-memory) |
| LLM | Llama 3.1 8B via Groq Inference API | Free tier |
| Security | Custom OWASP LLM Top 10 layer | Free |

---

## License

MIT © 2025 Kartik Salian — feel free to fork and build on this.
