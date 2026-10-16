from fastapi.testclient import TestClient

from app.main import app


def test_health():
    r = TestClient(app).get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_guidance_without_api_key_returns_503(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "anthropic_api_key", "")
    r = TestClient(app).post("/query/guidance", json={"text": "I was cheated in an online purchase"})
    assert r.status_code == 503
