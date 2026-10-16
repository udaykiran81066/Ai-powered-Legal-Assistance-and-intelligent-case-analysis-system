"""Score retrieval quality against a small hand-labelled query set.

Run once per embedding model, each with its own store, e.g. (from backend/):
    EMBEDDING_MODEL=BAAI/bge-base-en-v1.5 CHROMA_DIR=./chroma_bge python -m scripts.ingest --reset
    EMBEDDING_MODEL=BAAI/bge-base-en-v1.5 CHROMA_DIR=./chroma_bge python -m scripts.eval_retrieval
"""
from app.core.config import settings
from app.retrieval.chroma_store import search

# query -> any one of these (act, section) pairs counts as a hit
CASES = [
    ("someone cheated me in an online purchase",
     [("Bharatiya Nyaya Sanhita", "318"), ("Information Technology Act", "66D")]),
    ("seller delivered a defective product and refuses refund",
     [("Consumer Protection Act", "2"), ("Consumer Protection Act", "39")]),
    ("punishment for murder", [("Bharatiya Nyaya Sanhita", "103")]),
    ("someone stole my mobile phone", [("Bharatiya Nyaya Sanhita", "303")]),
    ("hacking into my computer without permission",
     [("Information Technology Act", "66"), ("Information Technology Act", "43")]),
    ("impersonating someone online to cheat", [("Information Technology Act", "66D")]),
    ("compensation when the other party breaks a contract",
     [("Indian Contract Act", "73")]),
    ("bail before arrest", [("Bharatiya Nagarik Suraksha Sanhita", "482")]),
    ("when can police arrest without a warrant",
     [("Bharatiya Nagarik Suraksha Sanhita", "35")]),
    ("what is a contract of guarantee", [("Indian Contract Act", "126")]),
    ("misleading advertisement by a company",
     [("Consumer Protection Act", "21"), ("Consumer Protection Act", "89")]),
    ("criminal breach of trust by an employee",
     [("Bharatiya Nyaya Sanhita", "316")]),
]


def main(k: int = 5) -> None:
    print(f"model={settings.embedding_model} store={settings.chroma_dir}")
    hits1 = hitsk = 0
    for query, expected in CASES:
        got = [(r["act"], r["section"]) for r in search(query, k)]
        rank = next((i + 1 for i, g in enumerate(got) if g in expected), None)
        hits1 += rank == 1
        hitsk += rank is not None
        print(f"  rank={rank or '-':>1}  {query}")
    n = len(CASES)
    print(f"hit@1 = {hits1}/{n}   hit@{k} = {hitsk}/{n}")


if __name__ == "__main__":
    main()
