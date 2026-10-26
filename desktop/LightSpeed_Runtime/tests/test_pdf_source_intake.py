import io
import sys
import pytest
from lightspeed_runtime.source_intake import build_source_envelope

pypdf = pytest.importorskip("pypdf")


def pdf_bytes(*, pages=1, encrypted=False):
    writer = pypdf.PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=72, height=72)
    if encrypted:
        writer.encrypt("test-only")
    stream = io.BytesIO()
    writer.write(stream)
    return stream.getvalue()


def test_blank_pdf_is_not_reported_as_semantically_complete():
    env = build_source_envelope(source_name="blank.pdf", data=pdf_bytes(), extract_pdf_text=True)
    assert env["projections"][0]["page_count"] == 1
    assert "pdf_has_no_extractable_text_ocr_not_performed" in env["unresolved"]
    assert env["native_preservation"]["round_trip_claim"] == "TEXT_PROJECTION_ONLY_LAYOUT_NOT_PRESERVED"


def test_page_budget_and_native_identity_are_preserved():
    data = pdf_bytes(pages=2)
    env = build_source_envelope(source_name="two.pdf", data=data, extract_pdf_text=True, extraction_limits={"pdf_pages": 1})
    assert env["projections"][0]["pages_sampled"] == 1
    assert "source_projection_structure_limit_reached" in env["unresolved"]
    assert env["sha256"] == build_source_envelope(source_name="two.pdf", data=data)["sha256"]


def test_encrypted_document_is_not_unlocked():
    env = build_source_envelope(source_name="private.pdf", data=pdf_bytes(encrypted=True), extract_pdf_text=True)
    assert env["projections"][0]["kind"] != "pdf_text"
    assert env["warnings"] and env["unresolved"]


def test_missing_optional_parser_falls_back_to_reference(monkeypatch):
    data = pdf_bytes()
    monkeypatch.setitem(sys.modules, "pypdf", None)
    env = build_source_envelope(source_name="a.pdf", data=data, extract_pdf_text=True)
    assert env["projections"][0]["kind"] != "pdf_text"
    assert env["warnings"]
