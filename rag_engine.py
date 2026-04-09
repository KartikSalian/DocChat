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


# ── Constants ──────────────────────────────────────────────────────────────────
EMBED_MODEL_NAME = "all-MiniLM-L6-v2"
LLM_MODEL_ID = "llama-3.1-8b-instant"   # free on Groq
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
TOP_K = 3
MAX_NEW_TOKENS = 512


class RAGEngine:
    """
    Manages the full RAG pipeline:
      1. Parse PDF → raw text
      2. Split text into overlapping chunks
      3. Embed chunks with sentence-transformers (local, free)
      4. Store / search embeddings with FAISS
      5. Query the Hugging Face Inference API with retrieved context
    """

    def __init__(self):
        self._embed_model: Optional[SentenceTransformer] = None
        self._index: Optional[faiss.IndexFlatL2] = None
        self._chunks: list[str] = []
        self._groq_key: str = os.getenv("GROQ_API_KEY", "")

    # ── Lazy-load the embedding model ──────────────────────────────────────────
    @property
    def embed_model(self) -> SentenceTransformer:
        if self._embed_model is None:
            self._embed_model = SentenceTransformer(EMBED_MODEL_NAME)
        return self._embed_model

    # ── PDF parsing ────────────────────────────────────────────────────────────
    def parse_pdf(self, file_bytes: bytes) -> str:
        """Extract raw text from PDF bytes. Raises ValueError on failure."""
        import io

        reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        if len(reader.pages) == 0:
            raise ValueError("The uploaded PDF contains no pages.")

        pages_text: list[str] = []
        for page in reader.pages:
            text = page.extract_text() or ""
            pages_text.append(text)

        full_text = "\n".join(pages_text).strip()
        if not full_text:
            raise ValueError(
                "No readable text found in the PDF. "
                "The file may be scanned or image-based."
            )
        return full_text

    # ── Chunking ───────────────────────────────────────────────────────────────
    def split_text(self, text: str) -> list[str]:
        """Split text into overlapping chunks using LangChain splitter."""
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

    # ── Embedding & FAISS index ────────────────────────────────────────────────
    def build_index(self, chunks: list[str]) -> None:
        """Embed chunks and build a FAISS flat-L2 index in memory."""
        embeddings: np.ndarray = self.embed_model.encode(
            chunks, show_progress_bar=False, convert_to_numpy=True
        )
        embeddings = embeddings.astype("float32")

        dim = embeddings.shape[1]
        index = faiss.IndexFlatL2(dim)
        index.add(embeddings)

        self._index = index
        self._chunks = chunks

    # ── Full ingest pipeline ───────────────────────────────────────────────────
    def ingest_pdf(self, file_bytes: bytes) -> int:
        """Parse, chunk, embed, and index a PDF. Returns number of chunks."""
        text = self.parse_pdf(file_bytes)
        chunks = self.split_text(text)
        self.build_index(chunks)
        return len(chunks)

    # ── Retrieval ──────────────────────────────────────────────────────────────
    def retrieve(self, query: str, top_k: int = TOP_K) -> list[str]:
        """Return the top-k most relevant chunks for a query."""
        if self._index is None or not self._chunks:
            raise RuntimeError("No document has been indexed yet.")

        q_embed = self.embed_model.encode(
            [query], show_progress_bar=False, convert_to_numpy=True
        ).astype("float32")

        distances, indices = self._index.search(q_embed, top_k)
        results = [
            self._chunks[i]
            for i in indices[0]
            if i < len(self._chunks)
        ]
        return results

    # ── LLM inference via Hugging Face ─────────────────────────────────────────
    def query_llm(self, question: str, context_chunks: list[str]) -> str:
        """Send prompt to Groq Inference API and return the answer."""
        if not self._groq_key:
            raise ValueError(
                "GROQ_API_KEY is not set. "
                "Add it to your .env file (get a free key at console.groq.com)."
            )

        context = "\n\n---\n\n".join(context_chunks)
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
            return self._clean_response(result.choices[0].message.content or "")
        except Exception as e:
            err = str(e)
            if "401" in err or "invalid_api_key" in err.lower():
                raise RuntimeError("Invalid Groq API key. Check your GROQ_API_KEY value.")
            raise RuntimeError(f"Groq API error: {err[:300]}")

    @staticmethod
    def _clean_response(text: str) -> str:
        """Remove any stray stop tokens or leading/trailing whitespace."""
        for token in ["</s>", "[INST]", "[/INST]", "<<SYS>>", "<</SYS>>"]:
            text = text.replace(token, "")
        return text.strip()

    # ── Full query pipeline ────────────────────────────────────────────────────
    def answer(self, question: str) -> dict:
        """
        End-to-end RAG query.
        Returns {"answer": str, "sources": list[str]}.
        """
        question = question.strip()
        if not question:
            raise ValueError("Question must not be empty.")

        sources = self.retrieve(question)
        answer_text = self.query_llm(question, sources)
        return {"answer": answer_text, "sources": sources}

    # ── State helpers ──────────────────────────────────────────────────────────
    def is_ready(self) -> bool:
        """True if a document has been indexed and the engine can answer."""
        return self._index is not None and bool(self._chunks)

    def reset(self) -> None:
        """Clear the current index and chunks."""
        self._index = None
        self._chunks = []
