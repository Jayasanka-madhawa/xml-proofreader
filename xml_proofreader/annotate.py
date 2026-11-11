from xml.sax.saxutils import escape


def attr(value):
    """Escape a value for use inside a double-quoted XML attribute."""
    return '"' + escape(value, {'"': "&quot;"}) + '"'


def error_tag(original, etype, correction, reason=None):
    """Build  <error type=".." correction="..">original</error>"""
    tag = f"<error type={attr(etype)} correction={attr(correction)}"
    if reason:
        tag += f" reason={attr(reason)}"
    return f"{tag}>{original}</error>"