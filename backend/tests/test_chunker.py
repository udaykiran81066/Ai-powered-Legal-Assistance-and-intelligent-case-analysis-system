from app.ingestion.chunker import chunk_by_section

PAGES = [
    (1, "THE TEST ACT\n1. Short title.—This Act may be called the Test Act, 1860.\n"
        "2. Definitions.—In this Act, unless the context otherwise requires, the following apply:\n"
        "(1) first item\n(2) second item\n"),
    (2, "420. Cheating and dishonestly inducing delivery of property.—Whoever cheats and thereby "
        "dishonestly induces the person deceived to deliver any property shall be punished.\n"
        "420A. Another provision.—Text of the lettered provision that is long enough to keep.\n"),
]


def test_one_chunk_per_section_with_metadata():
    chunks = chunk_by_section("Test Act", PAGES)
    secs = {c.section: c for c in chunks}
    assert "1" in secs and "2" in secs
    assert "(1) first item" in secs["2"].text  # list items stay inside their section
    assert secs["1"].page == 1
    assert secs["1"].title == "Short title"
