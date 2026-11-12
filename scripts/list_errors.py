import sys

from lxml import etree

root = etree.parse(sys.argv[1]).getroot()
paragraphs = [el for el in root.iter() if isinstance(el.tag, str) and etree.QName(el).localname == "p"]
for n, p in enumerate(paragraphs):
    for err in p.iter("error"):
        print(f"p{n:<2} {err.get('type'):<15} {''.join(err.itertext())!r:<32} -> {err.get('correction')!r}")