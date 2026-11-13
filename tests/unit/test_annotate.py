from xml_proofreader.annotate import locate


def test_prefix_picks_the_later_copy():
    text = "the court and the court"
    errors = [{
        "original": "court",
        "prefix": "and the ",
        "type": "spelling",
        "correction": "Court",
        "reason": "typo",
    }]
    placed = locate(text, errors)
    assert len(placed) == 1
    start, end, err = placed[0]
    assert text[start:end] == "court"
    assert start == text.rfind("court")
    assert err["correction"] == "Court"
