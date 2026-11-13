from xml_proofreader.xml_scan import find_paragraphs


def texts(xml):
    return [xml[start:end] for start, end in find_paragraphs(xml)]


def test_paragraph_inside_a_comment_is_ignored():
    xml = "<!-- only <p>, not a paragraph --><p>real</p>"
    assert texts(xml) == ["real"]


def test_paragraph_inside_cdata_is_kept_as_text():
    xml = "<p><![CDATA[keep <p> this]]></p>"
    assert texts(xml) == ["<![CDATA[keep <p> this]]>"]


def test_nested_paragraphs_are_both_found():
    xml = "<doc><p>outer <p>inner</p> tail</p></doc>"
    assert texts(xml) == ["inner", "outer <p>inner</p> tail"]


def test_namespace_on_the_document_does_not_hide_paragraphs():
    xml = '<doc xmlns="http://example.com" xmlns:meta="http://example.com/meta"><p>hello</p></doc>'
    assert texts(xml) == ["hello"]


def test_a_heading_is_not_a_paragraph():
    xml = "<doc><heading>Bad Title</heading><p>real</p></doc>"
    assert texts(xml) == ["real"]
