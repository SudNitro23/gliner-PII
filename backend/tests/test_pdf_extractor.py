from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from app.services.pdf_extractor import extract_pdf_text


class FakePage:
    def __init__(self, text: str | None = None, error: Exception | None = None) -> None:
        self._text = text
        self._error = error

    def get_text(self, mode: str) -> str:
        assert mode == "text"
        if self._error is not None:
            raise self._error
        return self._text or ""


class FakeDocument:
    def __init__(self, pages: list[FakePage]) -> None:
        self._pages = pages

    def __enter__(self) -> FakeDocument:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def __iter__(self):
        return iter(self._pages)


def test_extract_pdf_text_returns_page_level_mapping(monkeypatch) -> None:
    fake_fitz = SimpleNamespace(
        open=lambda path: FakeDocument([FakePage("Page one"), FakePage("Page two")])
    )
    monkeypatch.setitem(__import__("sys").modules, "fitz", fake_fitz)

    document = extract_pdf_text(Path("/tmp/sample.pdf"))

    assert document.file_name == "sample.pdf"
    assert document.page_count == 2
    assert document.text == "Page one\nPage two"
    assert document.pages[0].file_name == "sample.pdf"
    assert document.pages[0].page_number == 1
    assert document.pages[1].page_number == 2


def test_extract_pdf_text_keeps_page_mapping_when_one_page_fails(monkeypatch) -> None:
    fake_fitz = SimpleNamespace(
        open=lambda path: FakeDocument(
            [
                FakePage("Page one"),
                FakePage(error=RuntimeError("boom")),
                FakePage("Page three"),
            ]
        )
    )
    monkeypatch.setitem(__import__("sys").modules, "fitz", fake_fitz)

    document = extract_pdf_text(Path("/tmp/problem.pdf"))

    assert document.page_count == 3
    assert document.text == "Page one\nPage three"
    assert document.pages[1].page_number == 2
    assert document.pages[1].error is not None
    assert document.has_errors is True
    assert len(document.extraction_errors) == 1
