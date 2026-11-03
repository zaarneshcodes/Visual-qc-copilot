"""Layer 3a — retrieval over the SOP knowledge base (data/knowledge_base/*.md).

Backend "chroma": LangChain + Chroma with Chroma's ONNX MiniLM embeddings
(local, no API key, no torch). Backend "keyword": tiny BM25-style scorer with no ML
dependencies — used in CI and as an automatic fallback if the chroma stack fails.
"""
from __future__ import annotations

import logging
import math
import re
import uuid
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from .config import settings

log = logging.getLogger(__name__)


@dataclass
class Chunk:
    text: str
    source: str  # file name, e.g. SOP-BTL-001.md
    section: str  # nearest markdown heading


def _sop_files(sops_dir: Path) -> list[Path]:
    return sorted(p for p in sops_dir.glob("*.md") if p.name.lower() != "readme.md")


def split_markdown(text: str, source: str, max_chars: int = 900) -> list[Chunk]:
    """Split on headings first (keeps SOP sections intact), then on size."""
    chunks: list[Chunk] = []
    section, buf = "Introduction", []

    def flush():
        body = "\n".join(buf).strip()
        while body:
            chunks.append(Chunk(body[:max_chars], source, section))
            body = body[max_chars:]

    for line in text.splitlines():
        if line.startswith("#"):
            flush()
            buf = [line]
            section = line.lstrip("#").strip()
        else:
            buf.append(line)
    flush()
    return [c for c in chunks if len(c.text) > 40]


def load_chunks(sops_dir: Path | None = None) -> list[Chunk]:
    sops_dir = sops_dir or settings.sops_dir
    chunks: list[Chunk] = []
    for path in _sop_files(sops_dir):
        chunks.extend(split_markdown(path.read_text(encoding="utf-8"), path.name))
    return chunks


_TOKEN = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> list[str]:
    return _TOKEN.findall(text.lower())


class KeywordRetriever:
    def __init__(self, chunks: list[Chunk]):
        self.chunks = chunks
        self.docs = [Counter(_tokens(c.text + " " + c.section)) for c in chunks]
        self.avg_len = sum(sum(d.values()) for d in self.docs) / max(len(self.docs), 1)
        df = Counter(t for d in self.docs for t in d)
        n = len(self.docs)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}

    def search(self, query: str, k: int, product: str | None = None) -> list[Chunk]:
        q = _tokens(query)
        scored = []
        for chunk, doc in zip(self.chunks, self.docs, strict=False):
            length = sum(doc.values())
            s = 0.0
            for t in q:
                f = doc.get(t, 0)
                if f:
                    s += self.idf.get(t, 0) * f * 2.2 / (f + 1.2 * (0.25 + 0.75 * length / self.avg_len))
            if product and _matches_product(chunk.source, product):
                s *= 1.5  # prefer the SOP for the product being inspected
            scored.append((s, chunk))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [c for s, c in scored[:k] if s > 0]


def _matches_product(source: str, product: str) -> bool:
    tag = {"bottle": "BTL", "pcb": "PCB"}.get(product, product.upper())
    return tag in source.upper()


class OnnxMiniLMEmbeddings:
    """LangChain-compatible embeddings using Chroma's bundled ONNX all-MiniLM-L6-v2 (no torch needed)."""

    def __init__(self):
        from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

        self._fn = DefaultEmbeddingFunction()

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [list(map(float, v)) for v in self._fn(texts)]

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]


class ChromaRetriever:
    def __init__(self, chunks: list[Chunk]):
        from langchain_chroma import Chroma
        from langchain_core.documents import Document

        self.chunks = chunks
        docs = [Document(page_content=c.text, metadata={"source": c.source, "section": c.section}) for c in chunks]
        # In-memory index rebuilt from the knowledge base on every start: it is small, and this keeps
        # vectors in sync with the files in git. A fresh collection name avoids duplicate chunks.
        self.store = Chroma.from_documents(
            docs, OnnxMiniLMEmbeddings(), collection_name=f"sops_{uuid.uuid4().hex[:8]}"
        )

    def search(self, query: str, k: int, product: str | None = None) -> list[Chunk]:
        results = self.store.similarity_search(query, k=k * 2)
        chunks = [Chunk(d.page_content, d.metadata.get("source", "?"), d.metadata.get("section", "")) for d in results]
        if product:
            chunks.sort(key=lambda c: not _matches_product(c.source, product))
        return chunks[:k]


_retriever = None


def get_retriever(rebuild: bool = False):
    global _retriever
    if _retriever is not None and not rebuild:
        return _retriever
    chunks = load_chunks()
    if not chunks:
        log.warning("No SOP files found in %s — reports will not cite SOPs", settings.sops_dir)
    if settings.rag_backend == "chroma" and chunks:
        try:
            _retriever = ChromaRetriever(chunks)
            _retriever.backend = "chroma"
            return _retriever
        except Exception as exc:
            log.warning("Chroma backend unavailable (%s); using keyword retrieval", exc)
    _retriever = KeywordRetriever(chunks)
    _retriever.backend = "keyword"
    return _retriever


def retrieve(query: str, product: str | None = None, k: int | None = None) -> list[Chunk]:
    return get_retriever().search(query, k or settings.rag_top_k, product)
