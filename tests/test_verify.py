from xml_proofreader.verify import strip_errors, check_invariant
from xml_proofreader.xml_scan import find_paragraphs

ORIGINAL = open("data/example_input.xml", encoding="utf-8").read()
ANNOTATED = open("data/example_output.xml", encoding="utf-8").read()


def test_good_output_passes():
    assert strip_errors(ANNOTATED) == ORIGINAL
    assert check_invariant(ORIGINAL, ANNOTATED) == []


def test_changed_text_is_caught():
    bad = ANNOTATED.replace(">committe<", ">committee<")
    assert check_invariant(ORIGINAL, bad) == [0]


def test_extra_space_is_caught():
    bad = ANNOTATED.replace("members will", "members  will")
    assert check_invariant(ORIGINAL, bad) == [0]


def test_paragraph_inside_a_comment_is_ignored():
    text = "<!-- only <p>, not a paragraph --><p>real</p>"
    spans = find_paragraphs(text)
    assert len(spans) == 1
    assert text[spans[0][0]:spans[0][1]] == "real"