import pytest
from xml_proofreader.styleguide import load_style_guide, fingerprint


def test_guide_text_is_loaded():
    guide = load_style_guide("data/Style_Guide.docx")
    assert "no comma between the month and the year" in guide.lower()
    assert "HIPAA" in guide


def test_fingerprint_changes_with_text():
    assert fingerprint("a") != fingerprint("b")
    assert fingerprint("a") == fingerprint("a")


def test_empty_docx_is_rejected(tmp_path):
    from docx import Document
    empty = tmp_path / "empty.docx"
    Document().save(empty)
    with pytest.raises(ValueError):
        load_style_guide(empty)