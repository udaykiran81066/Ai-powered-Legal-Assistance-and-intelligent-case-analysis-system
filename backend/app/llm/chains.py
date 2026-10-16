from dataclasses import dataclass

from langchain_core.runnables import Runnable

from app.core.config import settings
from app.llm.prompts import ANSWER_PROMPT, FACTS_PROMPT, ISSUES_PROMPT
from app.llm.schemas import FactsSchema, IssuesSchema, LegalGuidance


@dataclass
class Chains:
    """The three LLM steps. Each takes a dict and returns its Pydantic schema."""

    facts: Runnable
    issues: Runnable
    answer: Runnable


def build_chains(llm) -> Chains:
    """Wire prompts to any chat model that supports with_structured_output()."""
    return Chains(
        facts=FACTS_PROMPT | llm.with_structured_output(FactsSchema),
        issues=ISSUES_PROMPT | llm.with_structured_output(IssuesSchema),
        answer=ANSWER_PROMPT | llm.with_structured_output(LegalGuidance),
    )


def default_llm():
    from langchain_anthropic import ChatAnthropic

    if not settings.anthropic_api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set (see backend/.env.example)")
    return ChatAnthropic(
        model=settings.llm_model,
        api_key=settings.anthropic_api_key,
        temperature=0,
        max_tokens=2048,
    )
