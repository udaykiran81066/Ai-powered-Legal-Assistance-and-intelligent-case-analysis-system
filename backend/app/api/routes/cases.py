from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import Pipeline, get_current_user, get_pipeline
from app.api.schemas import CaseCreate, CaseDetail, CaseSummary
from app.db.models import Case, RetrievedReference, User
from app.db.session import get_db
from app.llm.schemas import FactsSchema, GuidanceResponse

router = APIRouter()


def _detail(case: Case) -> CaseDetail:
    return CaseDetail(
        id=case.id,
        query_text=case.query_text,
        confidence=case.confidence,
        created_at=case.created_at,
        facts=FactsSchema.model_validate(case.facts_json),
        response=GuidanceResponse.model_validate(case.response_json),
        references=case.references,
    )


@router.post("", response_model=CaseDetail, status_code=status.HTTP_201_CREATED)
def create_case(
    req: CaseCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    pipeline: Pipeline = Depends(get_pipeline),
) -> CaseDetail:
    """Run the RAG pipeline on the user's text and save the case with its evidence."""
    result = pipeline(req.query_text)
    case = Case(
        user_id=user.id,
        query_text=req.query_text,
        facts_json=result.facts.model_dump(mode="json"),
        response_json=result.model_dump(mode="json"),
        confidence=result.guidance.confidence,
        references=[
            RetrievedReference(
                act=s.act, section=s.section, page=s.page, chunk_text=s.text, score=s.score
            )
            for s in result.sources
        ],
    )
    db.add(case)
    db.commit()
    return _detail(case)


@router.get("", response_model=list[CaseSummary])
def list_cases(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[Case]:
    stmt = select(Case).where(Case.user_id == user.id).order_by(Case.created_at.desc(), Case.id.desc())
    return list(db.scalars(stmt))


@router.get("/{case_id}", response_model=CaseDetail)
def get_case(
    case_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> CaseDetail:
    case = db.get(Case, case_id)
    # 404 (not 403) for other users' cases so ids can't be probed.
    if case is None or case.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Case not found")
    return _detail(case)
