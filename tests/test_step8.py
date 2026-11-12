import threading

import pytest

from xml_proofreader import proofreader as pr
from xml_proofreader.cache import Cache
from xml_proofreader.proofreader import make_batches, proofread_text

XML = "<r>" + "".join(f"<p>teh cat {n}</p>" for n in range(10)) + "<p>teh cat 0</p><p>- . -</p></r>"
GUIDE = "rules"


def fake_answer(items):
    return {i: [dict(original="teh", prefix="", type="spelling", correction="the", reason="typo")] for i, _ in items}


def test_make_batches_by_count_and_size():
    items = [(i, "x" * 10) for i in range(7)]
    assert [len(b) for b in make_batches(items, batch_size=3)] == [3, 3, 1]
    assert [len(b) for b in make_batches(items, batch_size=99, max_chars=25)] == [2, 2, 2, 1]


def test_batching_dedupe_skip_and_cache(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(pr, "proofread", lambda items, lang, guide: calls.append(list(items)) or fake_answer(items))
    cache = Cache(tmp_path)
    out = proofread_text(XML, "en", GUIDE, cache=cache, batch_size=4)
    assert out.count("<error") == 11                 # all 11 real paragraphs tagged, "- . -" skipped
    assert sum(len(c) for c in calls) == 10          # the duplicate "teh cat 0" was sent only once
    assert len(calls) == 3                           # 10 paragraphs / batch size 4
    calls.clear()
    proofread_text(XML, "en", GUIDE, cache=cache)    # second run
    assert calls == []                               # everything came from the cache


def test_retry_then_success_and_giving_up(monkeypatch):
    state = {"n": 0}

    def flaky(items, lang, guide):
        state["n"] += 1
        if state["n"] == 1:
            raise RuntimeError("temporary")
        return fake_answer(items)

    monkeypatch.setattr(pr, "proofread", flaky)
    monkeypatch.setattr(pr.time, "sleep", lambda s: None)
    assert "<error" in proofread_text("<r><p>teh cat</p></r>", "en", GUIDE)

    def always_fail(items, lang, guide):
        raise RuntimeError("down")

    monkeypatch.setattr(pr, "proofread", always_fail)
    assert proofread_text("<r><p>teh cat</p></r>", "en", GUIDE) == "<r><p>teh cat</p></r>"


def test_requests_run_in_parallel(monkeypatch):
    barrier = threading.Barrier(3, timeout=5)

    def slow(items, lang, guide):
        barrier.wait()                               # only passes if 3 requests run at the same time
        return fake_answer(items)

    monkeypatch.setattr(pr, "proofread", slow)
    xml = "<r>" + "".join(f"<p>teh cat {n}</p>" for n in range(3)) + "</r>"
    assert proofread_text(xml, "en", GUIDE, batch_size=1, workers=3).count("<error") == 3