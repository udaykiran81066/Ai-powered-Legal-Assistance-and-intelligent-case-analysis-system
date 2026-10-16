from langchain_core.prompts import ChatPromptTemplate

FACTS_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You extract facts from a person's description of a legal problem in India. "
            "Use only what the text states; never invent parties, dates or amounts. "
            "Leave a field empty if the text does not say.",
        ),
        ("human", "{user_text}"),
    ]
)

ISSUES_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a legal researcher for Indian law. From the facts, list 2-5 distinct legal "
            "issues. For each, write 1-2 short search queries in plain language that would find "
            "the relevant statute sections (criminal law: BNS/BNSS; contracts; consumer "
            "protection; IT law). Do not answer the issues.",
        ),
        ("human", "Facts:\n{facts}"),
    ]
)

ANSWER_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You give general legal information about Indian law, not legal advice.\n"
            "GROUNDING RULES:\n"
            "1. Only cite from the SECTIONS provided below. Never cite a section, act or case "
            "that is not in that list.\n"
            "2. Every entry in applicable_provisions must carry the source_id of a provided "
            "section, exactly as written.\n"
            "3. If the sections do not cover an issue, say so in coverage_note instead of "
            "guessing. If nothing applies, return an empty applicable_provisions list.\n"
            "4. Remedies, next_steps and documents_to_gather must follow from the cited "
            "sections and the facts; keep them practical and concise.\n"
            "5. Set confidence to high only if the sections clearly cover every issue.",
        ),
        (
            "human",
            "FACTS:\n{facts}\n\nISSUES:\n{issues}\n\nSECTIONS:\n{sections}\n\n"
            "Produce the guidance.",
        ),
    ]
)
