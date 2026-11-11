import re

# matches <name ...>, </name>, and <name ... /> ; skips <?xml ?>, <!-- -->
TAG = re.compile(r'<(/?)([A-Za-z_][^\s/>]*)[^>]*?(/?)>')


def find_paragraphs(text):
    """Return (start, end) character positions of the content of every <p>."""
    paras = []
    stack = []                                   # (tag name, where its content starts)
    for m in TAG.finditer(text):
        closing, name, self_closing = m.group(1), m.group(2), m.group(3)
        if self_closing:                         # <br/> has no content, ignore
            continue
        if not closing:
            stack.append((name, m.end()))        # content starts right after the tag
        else:
            open_name, content_start = stack.pop()
            if open_name == "p":
                paras.append((content_start, m.start()))   # content ends before </p>
    return paras

def apply_edits(text, edits):
    """edits: list of (start, end, replacement). They must not overlap."""
    out, pos = [], 0
    for start, end, repl in sorted(edits):
        out.append(text[pos:start])     # untouched text before this edit
        out.append(repl)                # the replacement
        pos = end                       # skip past the replaced text
    out.append(text[pos:])              # untouched text after the last edit
    return "".join(out)