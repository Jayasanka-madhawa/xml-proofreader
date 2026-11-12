from xml.sax.saxutils import escape
from .prompts import CATEGORIES

def attr(value):
    """Escape a value for use inside a double-quoted XML attribute."""
    return '"' + escape(value, {'"': "&quot;"}) + '"'


def error_tag(original, etype, correction, reason=None):
    """Build  <error type=".." correction="..">original</error>"""
    tag = f"<error type={attr(etype)} correction={attr(correction)}"
    if reason:
        tag += f" reason={attr(reason)}"
    return f"{tag}>{original}</error>"


def find_all(text, needle):
    """Every position where `needle` occurs in `text`."""
    positions, i = [], text.find(needle)
    while i != -1:
        positions.append(i)
        i = text.find(needle, i + 1)
    return positions


def locate(para_text, errors):
    """Place the model's suggestions inside one paragraph.

    Returns a sorted list of (start, end, error) with positions relative to
    para_text. Unsafe suggestions are silently dropped.
    """
    placed = []
    for err in errors:
        original, correction = err.get("original"), err.get("correction")
        if not original or not correction or original == correction:
            continue                                   # empty or no-op
        if err.get("type") not in CATEGORIES:
            continue                                   # unknown category
        candidates = find_all(para_text, original)
        prefix = err.get("prefix") or ""
        if prefix:
            matching = [p for p in candidates if para_text[:p].endswith(prefix)]
            candidates = matching or candidates        # prefer the occurrence after `prefix`
        for pos in candidates:
            end = pos + len(original)
            if any(pos < e and end > s for s, e, _ in placed):
                continue                               # overlaps an earlier error
            placed.append((pos, end, err))
            break                                      # first free candidate wins
    return sorted(placed, key=lambda item: item[0])


def build_edits(para_start, para_text, placed):
    """Turn placed errors into (start, end, replacement) edits on the whole file."""
    edits = []
    for s, e, err in placed:
        reason = err.get("reason") or None
        tag = error_tag(para_text[s:e], err["type"], err["correction"], reason)
        edits.append((para_start + s, para_start + e, tag))
    return edits