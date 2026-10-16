import logging

from langchain_core.runnables import RunnableLambda

from app.llm.chains import build_chains
from app.llm.schemas import (
    FactsSchema,
    IssuesSchema,
    LegalGuidance,
    LegalIssue,
    ProvisionRef,
)
from app.services.guidance import generate_guidance, retrieve


class FakeLLM:
    """Stands in for a chat model: with_structured_output(schema) returns a canned object."""

    def __init__(self, guidance: LegalGuidance):
        self.canned = {
            FactsSchema: FactsSchema(parties=["buyer", "online seller"], amounts=["Rs 5000"]),
            IssuesSchema: IssuesSchema(
                issues=[LegalIssue(issue="Cheating", search_queries=["cheating online", "fraud"])]
            ),
            LegalGuidance: guidance,
        }

    def with_structured_output(self, schema):
        return RunnableLambda(lambda _prompt: self.canned[schema])


def fake_search(distance: float):
    def search(query: str, k: int) -> list[dict]:
        return [
            {"act": "Bharatiya Nyaya Sanhita", "section": "318", "title": "Cheating",
             "page": 95, "text": "Whoever cheats...", "distance": distance},
            {"act": "Bharatiya Nyaya Sanhita", "section": "319", "title": "Cheating by personation",
             "page": 96, "text": "A person is said to cheat by personation...", "distance": distance + 0.1},
        ]
    return search


def _guidance(*ids: str, confidence="high") -> LegalGuidance:
    return LegalGuidance(
        applicable_provisions=[ProvisionRef(source_id=i, explanation="applies") for i in ids],
        remedies=["file complaint"], next_steps=["gather evidence"],
        documents_to_gather=["payment receipt"], confidence=confidence,
    )


def test_retrieve_dedupes_and_ranks_by_best_score():
    secs = retrieve(["a", "b"], fake_search(0.2), k=5)
    assert [s.source_id for s in secs] == [
        "Bharatiya Nyaya Sanhita::318", "Bharatiya Nyaya Sanhita::319"]
    assert secs[0].score == 0.8


def test_high_similarity_keeps_model_confidence_and_no_disclaimer():
    chains = build_chains(FakeLLM(_guidance("Bharatiya Nyaya Sanhita::318")))
    out = generate_guidance("I paid Rs 5000 online and never got the goods", chains,
                            fake_search(0.2), threshold=0.5)
    assert out.guidance.confidence == "high"
    assert out.disclaimer is None
    assert out.max_similarity == 0.8


def test_low_similarity_forces_low_confidence_and_disclaimer(caplog):
    chains = build_chains(FakeLLM(_guidance("Bharatiya Nyaya Sanhita::318")))
    with caplog.at_level(logging.INFO, logger="legal_rag.guidance"):
        out = generate_guidance("something unrelated and vague here", chains,
                                fake_search(0.7), threshold=0.5)
    assert out.guidance.confidence == "low"
    assert out.disclaimer and "not legal advice" in out.disclaimer
    assert "max_similarity=0.300" in caplog.text and "confidence=low" in caplog.text


def test_citations_to_unretrieved_sections_are_dropped():
    chains = build_chains(
        FakeLLM(_guidance("Bharatiya Nyaya Sanhita::318", "Indian Penal Code::420")))
    out = generate_guidance("I was cheated in an online purchase", chains,
                            fake_search(0.2), threshold=0.5)
    assert [p.source_id for p in out.guidance.applicable_provisions] == [
        "Bharatiya Nyaya Sanhita::318"]
    assert out.dropped_source_ids == ["Indian Penal Code::420"]


def test_no_valid_citations_means_low_confidence():
    chains = build_chains(FakeLLM(_guidance("Indian Penal Code::420")))
    out = generate_guidance("I was cheated in an online purchase", chains,
                            fake_search(0.2), threshold=0.5)
    assert out.guidance.applicable_provisions == []
    assert out.guidance.confidence == "low"
    assert out.disclaimer
