"""Ingest bare-act PDFs from data/raw_pdfs into ChromaDB.

Usage (from backend/):  python -m scripts.ingest [--reset]
The act name is the PDF filename stem with '_' -> ' ', e.g. Indian_Penal_Code.pdf.
"""
import argparse
import shutil
from pathlib import Path

from app.core.config import settings
from app.ingestion.chunker import chunk_by_section
from app.ingestion.pdf_loader import load_pdf
from app.retrieval.chroma_store import add_chunks

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw_pdfs"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reset", action="store_true", help="wipe the vector store first")
    args = ap.parse_args()
    if args.reset:
        shutil.rmtree(settings.chroma_dir, ignore_errors=True)

    pdfs = sorted(RAW_DIR.glob("*.pdf"))
    if not pdfs:
        raise SystemExit(f"No PDFs found in {RAW_DIR}")
    for pdf in pdfs:
        act = pdf.stem.replace("_", " ")
        chunks = chunk_by_section(act, load_pdf(pdf))
        add_chunks(chunks)
        print(f"{act}: {len(chunks)} sections ingested")


if __name__ == "__main__":
    main()
