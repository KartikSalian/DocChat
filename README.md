# 📄 DocChat — RAG PDF Chatbot

> Ask questions about any PDF document using a **100 % free** AI stack.
> No OpenAI. No paid APIs. Zero cost.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.32-red?logo=streamlit)
![LangChain](https://img.shields.io/badge/LangChain-0.1-green?logo=chainlink)
![HuggingFace](https://img.shields.io/badge/HuggingFace-Zephyr--7B-yellow?logo=huggingface)
![FAISS](https://img.shields.io/badge/Vector_Store-FAISS-blueviolet)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                        USER                             │
│                    (Streamlit UI)                       │
└──────────────────────────┬──────────────────────────────┘
                           │  PDF upload / question
                           ▼
┌─────────────────────────────────────────────────────────┐
│                     app.py                              │
│             Streamlit front-end                         │
│   • Sidebar PDF upload                                  │
│   • Chat interface + history                            │
│   • Source chunk expander                               │
└──────────────────────────┬──────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                  rag_engine.py                          │
│                  RAGEngine class                        │
│                                                         │
│  ┌────────────┐   ┌───────────────┐   ┌─────────────┐  │
│  │  PyPDF2    │──▶│  LangChain    │──▶│  FAISS      │  │
│  │ PDF parser │   │ Text splitter │   │ Vector store│  │
│  └────────────┘   └───────────────┘   └──────┬──────┘  │
│                                              │          │
│  ┌─────────────────────────────┐            │          │
│  │ sentence-transformers       │◀───────────┘          │
│  │ all-MiniLM-L6-v2 (local)   │  embed chunks & query │
│  └─────────────────────────────┘                       │
│                                                         │
│  ┌─────────────────────────────┐                       │
│  │ HuggingFace Inference API   │  top-3 chunks + Q     │
│  │ Zephyr-7B-β (free tier)    │──────────────────────▶│
│  └─────────────────────────────┘                       │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
              Answer + source chunks returned
```

---

## Features

- **Upload any PDF** — research papers, manuals, contracts, books
- **Conversational Q&A** — full message history preserved in session
- **Source transparency** — every answer shows the exact document chunks used
- **100 % free** — embeddings run locally; only the LLM call uses HF free tier
- **No GPU required** — runs on CPU, works on Hugging Face Spaces free tier
- **Error handling** — friendly messages for API issues, bad PDFs, empty questions

---

## Local Setup

### 1 — Clone & create a virtual environment

```bash
git clone https://github.com/<your-username>/docchat.git
cd docchat

python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
```

### 2 — Install dependencies

```bash
pip install -r requirements.txt
```

### 3 — Get a free Hugging Face token

1. Go to <https://huggingface.co/join> and create a free account.
2. Navigate to **Settings → Access Tokens**.
3. Click **New token**, choose **Read** role, and copy the token.

### 4 — Configure your token

```bash
cp .env.example .env
# Open .env and paste your token:
# HUGGINGFACE_TOKEN=hf_xxxxxxxxxxxxxxxxxxxx
```

### 5 — Run the app

```bash
streamlit run app.py
```

Open <http://localhost:8501> in your browser.

---

## Deploy to Hugging Face Spaces (Free)

1. Create a new **Space** at <https://huggingface.co/new-space>.
   - SDK: **Streamlit**
   - Hardware: **CPU Basic** (free)

2. Push your code (excluding `.env`):

   ```bash
   git remote add space https://huggingface.co/spaces/<username>/<space-name>
   git push space main
   ```

3. Add your token as a **Space secret**:
   - Space → **Settings → Variables and secrets**
   - Name: `HUGGINGFACE_TOKEN`, Value: `hf_xxxxxxxxxxxxxxxxxxxx`

4. The Space will rebuild automatically. Done!

---

## Project Structure

```
DocChat/
├── app.py            # Streamlit UI
├── rag_engine.py     # RAG pipeline (parse → embed → retrieve → generate)
├── requirements.txt  # Pinned dependencies
├── .env.example      # Token template (safe to commit)
├── .gitignore        # Excludes .env, caches, indexes
└── README.md         # This file
```

---

## Tech Stack

| Component | Library / Service | Cost |
|-----------|-------------------|------|
| UI | Streamlit 1.32 | Free |
| Orchestration | LangChain 0.1 | Free |
| PDF parsing | PyPDF2 3.0 | Free |
| Embeddings | sentence-transformers all-MiniLM-L6-v2 | Free (local) |
| Vector store | FAISS-CPU 1.8 | Free (in-memory) |
| LLM | HuggingFaceH4/zephyr-7b-beta via HF Inference API | Free tier |

---

## Screenshots

<!-- Add screenshots here after running the app -->
| Upload & Index | Chat Interface |
|---|---|
| _(screenshot)_ | _(screenshot)_ |

---

## License

MIT © 2024 — feel free to fork and build on this.
