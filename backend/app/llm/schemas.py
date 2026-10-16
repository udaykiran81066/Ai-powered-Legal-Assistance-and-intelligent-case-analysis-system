from typing import Literal

from pydantic import BaseModel, Field


class FactsSchema(BaseModel):
    """Step 1: structured facts pulled from the user's free text."""

    parties: list[str] = Field(default_factory=list, description="People/organisations involved and their roles")
    events: list[str] = Field(default_factory=list, description="What happened, in chronological order")
    dates: list[str] = Field(default_factory=list, description="Dates or time references mentioned")
    amounts: list[str] = Field(default_factory=list, description="Money amounts mentioned, with currency")
    jurisdiction: str | None = Field(default=None, description="Place/state/court if stated, else null")


class LegalIssue(BaseModel):
    issue: str = Field(description="One legal issue arising from the facts")
    search_queries: list[str] = Field(description="1-2 queries to find relevant statute sections")


class IssuesSchema(BaseModel):
    """Step 2: 2-5 issues, each with queries to run against the vector store."""

    issues: list[LegalIssue] = Field(min_length=1, max_length=5)


class RetrievedSection(BaseModel):
    source_id: str  # "<act>::<section>", unique id used for grounding
    act: str
    section: str
    title: str
    page: int
    text: str
    score: float  # cosine similarity, higher is better


class ProvisionRef(BaseModel):
    source_id: str = Field(description="Must be one of the provided source_ids")
    explanation: str = Field(description="Why this provision applies to the facts")


class LegalGuidance(BaseModel):
    """Step 3: the grounded answer returned to the frontend."""

    applicable_provisions: list[ProvisionRef] = Field(default_factory=list)
    remedies: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)
    documents_to_gather: list[str] = Field(default_factory=list)
    coverage_note: str = Field(
        default="",
        description="If the provided sections do not cover an issue, say so here",
    )
    confidence: Literal["high", "medium", "low"] = "medium"


class GuidanceResponse(BaseModel):
    """What the API returns: the guidance plus the evidence and the decision trail."""

    guidance: LegalGuidance
    facts: FactsSchema
    issues: IssuesSchema
    sources: list[RetrievedSection]
    max_similarity: float
    threshold: float
    disclaimer: str | None = None
    dropped_source_ids: list[str] = Field(
        default_factory=list,
        description="source_ids the model cited that were not in the retrieved set",
    )
