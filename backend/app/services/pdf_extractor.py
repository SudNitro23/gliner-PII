from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ExtractedDocument:
    text: str
    page_count: int


def extract_pdf_text(pdf_path: Path) -> ExtractedDocument:
    try:
        import fitz
    except ImportError as exc:
        raise RuntimeError("PyMuPDF is required for PDF text extraction") from exc

    page_texts: list[str] = []

    with fitz.open(str(pdf_path)) as document:
        for page in document:
            page_texts.append(page.get_text("text"))

        return ExtractedDocument(
            text="\n".join(page_texts).strip(),
            page_count=document.page_count,
        )

