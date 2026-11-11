import re

from lxml import etree


def strip_errors(text):
    """Remove <error ...> and </error> tags, leaving the text between them."""
    return re.sub(r"<error\b[^>]*>|</error>", "", text)


def paragraph_texts(xml_text, tag="p"):
    """Text content of every <p>, as a real XML parser sees it (tags and attributes excluded)."""
    root = etree.fromstring(xml_text.encode("utf-8"))
    return ["".join(el.itertext()) for el in root.iter(tag)]


def check_invariant(original, annotated):
    """Return the numbers of paragraphs whose text differs (empty list = all good)."""
    before = paragraph_texts(original)
    after = paragraph_texts(annotated)
    if len(before) != len(after):
        return list(range(max(len(before), len(after))))
    return [i for i, (a, b) in enumerate(zip(before, after)) if a != b]