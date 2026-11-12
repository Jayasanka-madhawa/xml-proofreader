from .annotate import build_edits, locate
from .llm import proofread
from .verify import check_invariant
from .xml_scan import apply_edits, find_paragraphs


def proofread_text(text, lang, guide):
    """Proofread every <p> in `text` and return the annotated XML text."""
    paras = sorted(find_paragraphs(text))
    items = [(i, text[s:e]) for i, (s, e) in enumerate(paras)]
    answers = proofread(items, lang, guide)                 # {paragraph number: [errors]}

    edits_by_para = {}
    for i, (s, e) in enumerate(paras):
        placed = locate(text[s:e], answers.get(i, []))
        if placed:
            edits_by_para[i] = build_edits(s, text[s:e], placed)

    # apply, verify, and drop any paragraph whose text changed (should never happen)
    for _ in range(3):
        all_edits = [edit for edits in edits_by_para.values() for edit in edits]
        result = apply_edits(text, all_edits)
        bad = check_invariant(text, result)
        if not bad:
            return result
        for i in bad:
            edits_by_para.pop(i, None)
    return text