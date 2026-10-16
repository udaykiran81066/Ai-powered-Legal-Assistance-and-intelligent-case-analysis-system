import logging
from collections.abc import Callable

from app.core.config import settings
from app.llm.chains import Chains
from app.llm.schemas import GuidanceResponse, RetrievedSection

log = logging.getLogger("legal_rag.guidance")

DISCLAIMER = (
    "The retrieved statute sections may not cover your situation well, so this is a low-confidence "
    "answer. It is general information, not legal advice; please consult a qualified lawyer."
)

SearchFn = Callable[[str, int], list[dict]]


def source_id(act: str, section: str) -> str:
    return f"{act}::{section}"


def retrieve(queries: list[str], search: SearchFn, k: int) -> list[RetrievedSection]:
    """Run every query, dedupe by section, keep each section's best score, rank by score."""
    best: dict[str, RetrievedSection] = {}
    for q in queries:
        for r in search(q, k):
            sid = source_id(r["act"], r["section"])
            score = 1.0 - float(r["distance"])  # collection uses cosine distance
            if sid not in best or score > best[sid].score:
                best[sid] = RetrievedSection(
                    source_id=sid, act=r["act"], section=r["section"], title=r["title"],
                    page=int(r["page"]), text=r["text"], score=round(score, 4),
                )
    return sorted(best.values(), key=lambda s: s.score, reverse=True)


def _format_sections(sections: list[RetrievedSection], max_chars: int = 1500) -> str:
    return "\n\n".join(
        f"[source_id: {s.source_id}] {s.act}, s.{s.section} - {s.title}\n{s.text[:max_chars]}"
        for s in sections
    )


def generate_guidance(
    user_text: str,
    chains: Chains,
    search: SearchFn,
    k: int | None = None,
    threshold: float | None = None,
) -> GuidanceResponse:
    k = k or settings.top_k
    threshold = settings.similarity_threshold if threshold is None else threshold

    facts = chains.facts.invoke({"user_text": user_text})
    issues = chains.issues.invoke({"facts": facts.model_dump_json(indent=2)})

    queries = [q for i in issues.issues for q in i.search_queries]
    sections = retrieve(queries, search, k)
    max_sim = sections[0].score if sections else 0.0

    guidance = chains.answer.invoke(
        {
            "facts": facts.model_dump_json(indent=2),
            "issues": "\n".join(f"- {i.issue}" for i in issues.issues),
            "sections": _format_sections(sections),
        }
    )

    # Enforce grounding in code, not just in the prompt: drop citations to unknown ids.
    valid = {s.source_id for s in sections}
    dropped = [p.source_id for p in guidance.applicable_provisions if p.source_id not in valid]
    guidance.applicable_provisions = [
        p for p in guidance.applicable_provisions if p.source_id in valid
    ]

    low = max_sim < threshold or not guidance.applicable_provisions
    if low:
        guidance.confidence = "low"
    log.info(
        "confidence decision: max_similarity=%.3f threshold=%.3f provisions_kept=%d "
        "dropped=%s -> confidence=%s",
        max_sim, threshold, len(guidance.applicable_provisions), dropped, guidance.confidence,
    )

    return GuidanceResponse(
        guidance=guidance,
        facts=facts,
        issues=issues,
        sources=sections,
        max_similarity=round(max_sim, 4),
        threshold=threshold,
        disclaimer=DISCLAIMER if low else None,
        dropped_source_ids=dropped,
    )
