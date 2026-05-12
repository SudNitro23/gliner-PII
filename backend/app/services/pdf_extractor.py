from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class ExtractedPage:
    file_name: str
    page_number: int
    text: str
    error: str | None = None

    def to_dict(self) -> dict:
        return {
            "file_name": self.file_name,
            "page_number": self.page_number,
            "text": self.text,
            "error": self.error,
        }


@dataclass
class ExtractedDocument:
    file_name: str
    pages: list[ExtractedPage] = field(default_factory=list)
    extraction_errors: list[str] = field(default_factory=list)

    @property
    def text(self) -> str:
        return "\n".join(page.text for page in self.pages if page.text.strip()).strip()

    @property
    def page_count(self) -> int:
        return len(self.pages)

    @property
    def has_errors(self) -> bool:
        return bool(self.extraction_errors)

    def to_dict(self) -> dict:
        return {
            "file_name": self.file_name,
            "page_count": self.page_count,
            "pages": [page.to_dict() for page in self.pages],
            "extraction_errors": self.extraction_errors,
        }


def extract_pdf_text(pdf_path: Path) -> ExtractedDocument:
    file_name = pdf_path.name
    try:
        import fitz
    except ImportError as exc:
        raise RuntimeError("PyMuPDF is required for PDF text extraction") from exc

    extracted_document = ExtractedDocument(file_name=file_name)

    try:
        with fitz.open(str(pdf_path)) as document:
            for page_index, page in enumerate(document, start=1):
                try:
                    page_text = page.get_text("text")
                    extracted_document.pages.append(
                        ExtractedPage(
                            file_name=file_name,
                            page_number=page_index,
                            text=page_text.strip(),
                        )
                    )
                except Exception as exc:
                    error = f"Failed to extract page {page_index} from {file_name}: {exc}"
                    extracted_document.pages.append(
                        ExtractedPage(
                            file_name=file_name,
                            page_number=page_index,
                            text="",
                            error=error,
                        )
                    )
                    extracted_document.extraction_errors.append(error)
    except Exception as exc:
        raise RuntimeError(f"Failed to open or read PDF {file_name}: {exc}") from exc

    return extracted_document
