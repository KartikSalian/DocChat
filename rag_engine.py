"""
RAG Engine for DocChat
Handles PDF parsing, embedding, vector storage, and LLM inference.
"""

import os
from typing import Optional

import PyPDF2
import faiss
import numpy as np
from groq import Groq
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
from security import check_input, check_output, sanitise_input


# ── Constants ──────────────────────────────────────────────────────────────────
EMBED_MODEL_NAME = "all-MiniLM-L6-v2"
LLM_MODEL_ID     = "llama-3.1-8b-instant"
CHUNK_SIZE        = 500
CHUNK_OVERLAP     = 50
TOP_K             = 3
MAX_NEW_TOKENS    = 512


class RAGEngine:
    def __init__(self):
        self._embed_model: Optional[SentenceTransformer] = None
        self._index: Optional[faiss.IndexFlatL2] = None
        self._chunks: list[str] = []
        self._doc_map: list[str] = []          # which filename each chunk came from
        self._groq_key: str = os.getenv("GROQ_API_KEY", "")

    # ── Lazy-load embedding model ──────────────────────────────────────────────
    @property
    def embed_model(self) -> SentenceTransformer:
        if self._embed_model is None:
            self._embed_model = SentenceTransformer(EMBED_MODEL_NAME)
        return self._embed_model

    # ── PDF parsing ────────────────────────────────────────────────────────────
    def parse_pdf(self, file_bytes: bytes) -> str:
        import io
        reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        if not reader.pages:
            raise ValueError("The PDF contains no pages.")
        text = "\n".join(p.extract_text() or "" for p in reader.pages).strip()
        if not text:
            raise ValueError("No readable text found — the PDF may be scanned/image-based.")
        return text

    # ── Chunking ───────────────────────────────────────────────────────────────
    def split_text(self, text: str) -> list[str]:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        chunks = splitter.split_text(text)
        if not chunks:
            raise ValueError("Text splitting produced no chunks.")
        return chunks

    # ── Add one document to the index ─────────────────────────────────────────
    def add_document(self, file_bytes: bytes, filename: str) -> int:
        """Parse, chunk, embed and add a single PDF to the index. Returns chunk count."""
        text   = self.parse_pdf(file_bytes)
        chunks = self.split_text(text)

        embeddings = self.embed_model.encode(
            chunks, show_progress_bar=False, convert_to_numpy=True
        ).astype("float32")

        if self._index is None:
            self._index = faiss.IndexFlatL2(embeddings.shape[1])

        self._index.add(embeddings)
        self._chunks.extend(chunks)
        self._doc_map.extend([filename] * len(chunks))
        return len(chunks)

    # ── Legacy single-file ingest (kept for compatibility) ────────────────────
    def ingest_pdf(self, file_bytes: bytes, filename: str = "document.pdf") -> int:
        self.reset()
        return self.add_document(file_bytes, filename)

    # ── Retrieval ──────────────────────────────────────────────────────────────
    def retrieve(self, query: str, top_k: int = TOP_K) -> list[dict]:
        if self._index is None or not self._chunks:
            raise RuntimeError("No document has been indexed yet.")
        q = self.embed_model.encode(
            [query], show_progress_bar=False, convert_to_numpy=True
        ).astype("float32")
        _, indices = self._index.search(q, top_k)
        return [
            {"text": self._chunks[i], "source": self._doc_map[i]}
            for i in indices[0] if i < len(self._chunks)
        ]

    # ── LLM ───────────────────────────────────────────────────────────────────
    def query_llm(self, question: str, hits: list[dict]) -> str:
        if not self._groq_key:
            raise ValueError("GROQ_API_KEY is not set.")

        context = "\n\n---\n\n".join(
            f"[{h['source']}]\n{h['text']}" for h in hits
        )
        system_msg = (
            "You are a helpful assistant. Answer the question using only the "
            "document context provided. If the answer isn't in the context, say so."
        )
        try:
            client = Groq(api_key=self._groq_key)
            result = client.chat.completions.create(
                model=LLM_MODEL_ID,
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
                ],
                max_tokens=MAX_NEW_TOKENS,
                temperature=0.3,
            )
            return (result.choices[0].message.content or "").strip()
        except Exception as e:
            err = str(e)
            if "401" in err or "invalid_api_key" in err.lower():
                raise RuntimeError("Invalid Groq API key.")
            raise RuntimeError(f"Groq API error: {err[:300]}")

    # ── Full pipeline ──────────────────────────────────────────────────────────
    def answer(self, question: str) -> dict:
        question = question.strip()
        if not question:
            raise ValueError("Question must not be empty.")

        # ── LLM01/LLM04/LLM06: Input security check ───────────────────────────
        question = sanitise_input(question)
        threat   = check_input(question)
        if not threat.safe:
            return {
                "answer": f"🚨 **Security Block [{threat.threat}]**\n\n{threat.detail}",
                "sources": [],
                "blocked": True,
                "threat":  threat,
            }

        hits   = self.retrieve(question)
        answer = self.query_llm(question, hits)

        # ── LLM02: Output security check ──────────────────────────────────────
        out_threat = check_output(answer)
        if not out_threat.safe:
            return {
                "answer": f"⚠️ **Response Blocked [{out_threat.threat}]**\n\n{out_threat.detail}",
                "sources": [],
                "blocked": True,
                "threat":  out_threat,
            }

        return {"answer": answer, "sources": hits, "blocked": False}

    # ── Helpers ────────────────────────────────────────────────────────────────
    def is_ready(self) -> bool:
        return self._index is not None and bool(self._chunks)

    def indexed_docs(self) -> list[str]:
        """Return unique filenames currently indexed."""
        seen = []
        for d in self._doc_map:
            if d not in seen:
                seen.append(d)
        return seen

    def reset(self) -> None:
        self._index   = None
        self._chunks  = []
        self._doc_map = []
