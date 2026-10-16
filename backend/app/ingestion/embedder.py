import os
from functools import lru_cache

# Multi-threaded torch segfaults on this Windows setup once chromadb/pymupdf are loaded.
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

from sentence_transformers import SentenceTransformer

from app.core.config import settings

# BGE retrieval models expect this instruction on queries (not on documents).
BGE_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "


@lru_cache(maxsize=1)
def _model() -> SentenceTransformer:
    return SentenceTransformer(settings.embedding_model)


def embed(texts: list[str]) -> list[list[float]]:
    return _model().encode(texts, normalize_embeddings=True, show_progress_bar=False, batch_size=8).tolist()


def embed_query(text: str) -> list[float]:
    if "bge" in settings.embedding_model.lower():
        text = BGE_QUERY_PREFIX + text
    return embed([text])[0]
