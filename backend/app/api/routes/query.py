from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.llm.chains import build_chains, default_llm
from app.llm.schemas import GuidanceResponse
from app.services.guidance import generate_guidance

router = APIRouter()


class GuidanceRequest(BaseModel):
    text: str = Field(min_length=10, max_length=5000, description="The user's description of the problem")


@router.post("/guidance", response_model=GuidanceResponse)
def guidance(req: GuidanceRequest) -> GuidanceResponse:
    try:
        chains = build_chains(default_llm())
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    # Imported lazily so the API starts without loading torch/chromadb until first use.
    from app.retrieval.chroma_store import search

    return generate_guidance(req.text, chains, search)
