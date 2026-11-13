from datetime import datetime
from pathlib import Path

import anthropic
import httpx2
import pytest

from xml_proofreader import cli
from xml_proofreader import proofreader as pr

GUIDE = "data/Style_Guide.docx"


def fake(items, lang, guide):
    return {i: [dict(original="teh", prefix="", type="spelling", correction="the", reason="typo")] for i, _ in items}


@pytest.fixture(autouse=True)
def key(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test")


def test_output_path(tmp_path):
    when = datetime(2026, 11, 13, 0, 16, 30)
    src = Path("/a/b/input.xml")
    first = tmp_path / "input.corrected.2026-11-13T00-16-30.xml"
    assert cli.output_path(src, directory=tmp_path, when=when) == first
    first.write_text("kept")
    assert cli.output_path(src, directory=tmp_path, when=when) == tmp_path / "input.corrected.2026-11-13T00-16-30-2.xml"
    assert first.read_text() == "kept"


def test_end_to_end(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(pr, "proofread", fake)
    out_dir = tmp_path / "outputs"
    monkeypatch.setattr(cli, "OUTPUT_DIR", out_dir)
    monkeypatch.setattr(cli, "now", lambda: datetime(2026, 11, 13, 0, 16, 30))
    src = tmp_path / "doc.xml"
    src.write_bytes(b'<r>\r\n<p>teh cat</p>\r\n</r>')           # Windows line endings
    assert cli.main([str(src), "--lang", "en", "--style-guide", GUIDE, "--no-cache"]) == 0
    out = (out_dir / "doc.corrected.2026-11-13T00-16-30.xml").read_bytes()
    assert b"\r\n" in out and b"<error" in out                  # line endings kept
    err = capsys.readouterr().err
    assert "Performance summary" in err and "peak memory" in err
    saved = (out_dir / "doc.corrected.2026-11-13T00-16-30.txt").read_text()
    assert saved.strip() == err.strip()


@pytest.mark.parametrize("args", [
    ["missing.xml", "--lang", "en", "--style-guide", GUIDE],
    ["data/example_input.xml", "--lang", "english!", "--style-guide", GUIDE],
    ["data/example_input.xml", "--lang", "en", "--style-guide", "nope.docx"],
    ["data/example_input.xml", "--lang", "en", "--style-guide", GUIDE, "-o", "data/example_input.xml"],
])
def test_bad_arguments_exit_2(args):
    assert cli.main(args) == 2


def test_malformed_xml_exit_2(tmp_path):
    src = tmp_path / "bad.xml"
    src.write_text("<r><p>oops</r>")
    assert cli.main([str(src), "--lang", "en", "--style-guide", GUIDE]) == 2


def test_missing_key_exit_2(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY")
    assert cli.main(["data/example_input.xml", "--lang", "en", "--style-guide", GUIDE]) == 2


def test_rejected_key_exit_1(monkeypatch, tmp_path):
    calls = []

    def rejected(items, lang, guide):
        calls.append(items)
        response = httpx2.Response(401, request=httpx2.Request("POST", "https://api.anthropic.com"))
        raise anthropic.AuthenticationError("invalid x-api-key", response=response, body=None)

    monkeypatch.setattr(pr, "proofread", rejected)
    monkeypatch.setattr(cli, "OUTPUT_DIR", tmp_path)
    assert cli.main(["data/example_input.xml", "--lang", "en", "--style-guide", GUIDE, "--no-cache"]) == 1
    assert len(calls) == 1                                      # not retried
    assert list(tmp_path.iterdir()) == []                       # no output written