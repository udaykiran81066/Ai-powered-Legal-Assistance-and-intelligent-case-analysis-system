from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.models import User
from app.db.session import get_db
from app.llm.chains import build_chains, default_llm
from app.llm.schemas import GuidanceResponse
from app.services.guidance import generate_guidance

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

Pipeline = Callable[[str], GuidanceResponse]


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    user_id = decode_access_token(token)
    user = db.get(User, user_id) if user_id is not None else None
    if user is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def get_pipeline() -> Pipeline:
    """The RAG pipeline as text -> GuidanceResponse. Overridden in tests."""
    try:
        chains = build_chains(default_llm())
    except RuntimeError as e:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(e))
    # Imported lazily so the API starts without loading torch/chromadb until first use.
    from app.retrieval.chroma_store import search

    return lambda text: generate_guidance(text, chains, search)
