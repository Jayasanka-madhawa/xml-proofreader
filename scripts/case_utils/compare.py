"""Compare a corrected XML file with its hand-annotated expected file."""

from lxml import etree


def paragraphs(path):
    return [el for el in etree.parse(str(path)).getroot().iter()
            if isinstance(el.tag, str) and etree.QName(el).localname == "p"]


def errors(paragraph):
    found = []
    for err in paragraph.iter("error"):
        parent = err.getparent()
        if parent is not None and etree.QName(parent).localname == "error":
            continue
        found.append({
            "span": "".join(err.itertext()),
            "correction": err.get("correction") or "",
            "type": err.get("type") or "",
            "reason": err.get("reason") or "",
        })
    return found


def same_change(expected, actual):
    if expected["span"] == actual["span"] and expected["correction"] == actual["correction"]:
        return True
    if expected["span"] and expected["span"] in actual["span"]:
        return actual["correction"] == actual["span"].replace(expected["span"], expected["correction"], 1)
    if actual["span"] and actual["span"] in expected["span"]:
        return expected["correction"] == expected["span"].replace(actual["span"], actual["correction"], 1)
    return False


def overlaps(a, b):
    return a == b or (a and b and (a in b or b in a))


def compare(expected_path, actual_path):
    """Return rows of (paragraph number, kind, expected error, actual error).

    kind is "correct", "wrong fix", "missed", "extra" or "paragraph count".
    """
    rows = []
    expected_paras = paragraphs(expected_path)
    actual_paras = paragraphs(actual_path)
    if len(expected_paras) != len(actual_paras):
        rows.append((None, "paragraph count", {"span": str(len(expected_paras))}, {"span": str(len(actual_paras))}))
    for number, (exp_p, act_p) in enumerate(zip(expected_paras, actual_paras)):
        expected, actual = errors(exp_p), errors(act_p)
        used = [False] * len(actual)

        def take(test):
            for i, item in enumerate(actual):
                if not used[i] and test(item):
                    used[i] = True
                    return item
            return None

        for exp in expected:
            act = (take(lambda a: a["span"] == exp["span"] and a["correction"] == exp["correction"])
                   or take(lambda a: a["span"] == exp["span"])
                   or take(lambda a: overlaps(a["span"], exp["span"])))
            if act is None:
                rows.append((number, "missed", exp, None))
            elif same_change(exp, act):
                rows.append((number, "correct", exp, act))
            else:
                rows.append((number, "wrong fix", exp, act))
        for i, act in enumerate(actual):
            if not used[i]:
                rows.append((number, "extra", None, act))
    return rows
