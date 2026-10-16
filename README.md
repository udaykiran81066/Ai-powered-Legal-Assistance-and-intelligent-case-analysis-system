# Legal RAG — AI-Powered Legal Assistance

A retrieval-augmented generation (RAG) assistant that answers legal questions grounded in
Indian statutes (IPC, CrPC, Contract Act, …) and returns answers with source citations.

> Informational tool only — not legal advice.

## Architecture

```
PDFs ──► pdf_loader ──► chunker ──► embedder ──► ChromaDB
                                                    │
User question ──► FastAPI ──► retrieval (top-k) ◄───┘
                     │             │
                     │             ▼
                     │        LLM chain (prompt + context) ──► answer + citations
                     ▼
              SQLAlchemy DB (users, cases, query history)
```

| Layer | Location | Responsibility |
|---|---|---|
| API | `backend/app/api/routes` | `users`, `cases`, `query` endpoints |
| Config | `backend/app/core` | Env-based settings (pydantic-settings) |
| DB | `backend/app/db` | SQLAlchemy models and sessions |
| Ingestion | `backend/app/ingestion` | PDF loading, chunking, embeddings |
| Retrieval | `backend/app/retrieval` | Chroma vector store access |
| LLM | `backend/app/llm` | Prompts, chains, structured output schemas |
| Services | `backend/app/services` | Orchestration across the layers |
| Frontend | `frontend/` | Vite + React UI |

## Quick start

```bash
cd backend
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head      # create DB tables
uvicorn app.main:app --reload
pytest
```

Or: `docker compose up --build`

Put statute PDFs in `data/raw_pdfs/` (gitignored), then run `python scripts/ingest.py` (Phase 1).

## Roadmap

- [x] Phase 0 — Repo & skeleton
- [x] Phase 1 — Ingestion pipeline (PDF → chunks → embeddings → Chroma)
- [x] Phase 2 — Retrieval + LLM answer chain with citations
- [x] Phase 3 — Users (JWT auth), cases, query history (Postgres + Alembic)
- [ ] Phase 4 — React frontend
