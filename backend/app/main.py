from fastapi import FastAPI

from app.api.routes import cases, query, users
from app.core.config import settings

app = FastAPI(title=settings.app_name, version="0.1.0")

app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(cases.router, prefix="/cases", tags=["cases"])
app.include_router(query.router, prefix="/query", tags=["query"])


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
