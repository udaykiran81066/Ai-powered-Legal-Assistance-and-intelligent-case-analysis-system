import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_pipeline
from app.db import models  # noqa: F401  (registers tables on Base)
from app.db.session import Base, get_db
from app.llm.schemas import (
    FactsSchema,
    GuidanceResponse,
    IssuesSchema,
    LegalGuidance,
    LegalIssue,
    ProvisionRef,
    RetrievedSection,
)
from app.main import app


def fake_pipeline(text: str) -> GuidanceResponse:
    sid = "Bharatiya Nyaya Sanhita::318"
    return GuidanceResponse(
        guidance=LegalGuidance(
            applicable_provisions=[ProvisionRef(source_id=sid, explanation="cheating")],
            remedies=["file a complaint"], next_steps=["gather evidence"],
            documents_to_gather=["receipt"], confidence="high",
        ),
        facts=FactsSchema(parties=["buyer", "seller"], amounts=["Rs 5000"]),
        issues=IssuesSchema(issues=[LegalIssue(issue="Cheating", search_queries=["cheating"])]),
        sources=[RetrievedSection(
            source_id=sid, act="Bharatiya Nyaya Sanhita", section="318", title="Cheating",
            page=95, text="Whoever, by deceiving any person...", score=0.82)],
        max_similarity=0.82, threshold=0.5,
    )


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_db():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_pipeline] = lambda: fake_pipeline
    yield TestClient(app)
    app.dependency_overrides.clear()


def register_and_login(client: TestClient, email: str = "a@example.com") -> dict:
    pw = "correct-horse-battery"
    assert client.post("/auth/register", json={"email": email, "password": pw}).status_code == 201
    r = client.post("/auth/login", data={"username": email, "password": pw})
    assert r.status_code == 200
    return {"Authorization": f"Bearer {r.json()['access_token']}"}
