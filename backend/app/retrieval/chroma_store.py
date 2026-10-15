import chromadb

from app.core.config import settings
from app.ingestion.chunker import Chunk
from app.ingestion.embedder import embed

COLLECTION = "bare_acts"


def _collection():
    client = chromadb.PersistentClient(path=settings.chroma_dir)
    return client.get_or_create_collection(COLLECTION, metadata={"hnsw:space": "cosine"})


def add_chunks(chunks: list[Chunk], batch: int = 64) -> None:
    col = _collection()
    for i in range(0, len(chunks), batch):
        part = chunks[i : i + batch]
        col.upsert(
            ids=[f"{c.act}::{c.section}" for c in part],
            documents=[c.text for c in part],
            embeddings=embed([f"{c.act} s.{c.section} {c.title}\n{c.text}" for c in part]),
            metadatas=[
                {"act": c.act, "section": c.section, "title": c.title, "page": c.page}
                for c in part
            ],
        )


def search(query: str, k: int = 5) -> list[dict]:
    res = _collection().query(query_embeddings=embed([query]), n_results=k)
    return [
        {**meta, "text": doc, "distance": dist}
        for doc, meta, dist in zip(
            res["documents"][0], res["metadatas"][0], res["distances"][0]
        )
    ]
