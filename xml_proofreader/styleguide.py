import hashlib

from docx import Document


def load_style_guide(path):
    """Read a .docx and return its text (one line per non-empty paragraph)."""
    doc = Document(path)
    lines = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    if not lines:
        raise ValueError(f"No text found in {path}")
    return "\n".join(lines)


def fingerprint(text):
    """Short hash of the guide text; changes whenever the guide changes."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]