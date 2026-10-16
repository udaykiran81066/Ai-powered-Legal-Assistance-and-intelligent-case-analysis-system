from app.ingestion.chunker import chunk_by_section

DASH = "—"

PAGES = [
    (1, f"THE TEST ACT\n1. Short title.{DASH}This Act may be called the Test Act, 1860.\n"
        f"2. Definitions.{DASH}In this Act, unless the context otherwise requires, the following apply:\n"
        "(1) first item\n(2) second item\n"),
    (2, f"3. Cheating and dishonestly inducing delivery of property.{DASH}Whoever cheats and thereby "
        "dishonestly induces the person deceived to deliver any property shall be punished.\n"),
]


def _act(n_sections: int) -> str:
    return "\n".join(
        f"{i}. Heading number {i}.{DASH}Body text of provision {i}, long enough to be kept as a chunk."
        for i in range(1, n_sections + 1)
    )


def test_one_chunk_per_section_with_metadata():
    chunks = chunk_by_section("Test Act", PAGES)
    secs = {c.section: c for c in chunks}
    assert set(secs) == {"1", "2", "3"}
    assert "(1) first item" in secs["2"].text  # list items stay inside their section
    assert secs["1"].page == 1
    assert secs["1"].title == "Short title"
    assert secs["3"].page == 2


def test_table_of_contents_is_ignored_and_body_wins():
    toc = "\n".join(f"{i}. Heading number {i}." for i in range(1, 31))
    chunks = chunk_by_section("Act", [(1, toc), (2, _act(30))])
    assert len(chunks) == 30
    assert all(c.page == 2 for c in chunks)


def test_footnotes_and_midbody_lists_do_not_derail_sequence():
    body = _act(12).split("\n")
    body.insert(5, "4. See s. 75, infra.")  # footnote
    body.insert(8, "1. a list item inside a provision")
    body.insert(9, "2. another list item")
    chunks = chunk_by_section("Act", [(1, "\n".join(body))])
    assert [c.section for c in chunks] == [str(i) for i in range(1, 13)]


def test_no_space_after_number_and_quoted_heading():
    text = (
        f"1. Short title.{DASH}This Act may be called the Test Act, long enough to keep.\n"
        f"2.“Consent” defined.{DASH}Two or more persons consent when they agree on the same thing."
    )
    chunks = chunk_by_section("Act", [(1, text)])
    assert [c.section for c in chunks] == ["1", "2"]
