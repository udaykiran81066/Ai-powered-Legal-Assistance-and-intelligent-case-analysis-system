from pathlib import Path

import fitz  # PyMuPDF


def load_pdf(path: Path) -> list[tuple[int, str]]:
    """Return (page_number, text) pairs, 1-indexed."""
    with fitz.open(path) as doc:
        return [(i + 1, page.get_text()) for i, page in enumerate(doc)]
