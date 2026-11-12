import logging
import time
from concurrent.futures import ThreadPoolExecutor

import anthropic

from .annotate import build_edits, locate
from .cache import Cache
from .llm import MODEL, proofread
from .prompts import PROMPT_VERSION
from .styleguide import fingerprint
from .verify import check_invariant
from .xml_scan import apply_edits, find_paragraphs

log = logging.getLogger(__name__)


def make_batches(items, batch_size=6, max_chars=5000):
    """Group (id, text) pairs into batches, limited by count and by total characters."""
    batches, current, chars = [], [], 0
    for item in items:
        if current and (len(current) >= batch_size or chars + len(item[1]) > max_chars):
            batches.append(current)
            current, chars = [], 0
        current.append(item)
        chars += len(item[1])
    if current:
        batches.append(current)
    return batches


def proofread_with_retries(batch, lang, guide, retries=2):
    """Proofread a batch. On failure retry; later attempts send one paragraph at a time."""
    result, pending = {}, list(batch)
    for attempt in range(retries + 1):
        if not pending:
            break
        groups = [pending] if attempt == 0 else [[item] for item in pending]
        pending = []
        for group in groups:
            try:
                got = proofread(group, lang, guide)
            except anthropic.BadRequestError:
                raise                                   # our request is wrong; retrying cannot help
            except (anthropic.APIError, RuntimeError) as exc:
                log.warning("Model call failed (attempt %d): %s", attempt + 1, exc)
                pending.extend(group)
                continue
            for item in group:
                if item[0] in got:
                    result[item[0]] = got[item[0]]
                else:
                    pending.append(item)                # model skipped this paragraph
        if pending and attempt < retries:
            time.sleep(0.5 * (attempt + 1))
    for item in pending:
        log.error("Giving up on paragraph %d; it is left unchanged", item[0])
    return result


def proofread_text(text, lang, guide, cache=None, workers=8, batch_size=6):
    """Proofread every <p> in `text` and return the annotated XML text."""
    cache = cache or Cache(None)
    paras = sorted(find_paragraphs(text))
    fp = fingerprint(guide)

    answers = {}          # paragraph number -> list of errors
    waiting = {}          # cache key -> numbers of the paragraphs that share this exact text
    key_text = {}         # cache key -> that text
    for i, (s, e) in enumerate(paras):
        para = text[s:e]
        if not any(c.isalnum() for c in para):
            answers[i] = []                                  # nothing to proofread
            continue
        key = Cache.key(PROMPT_VERSION, MODEL, lang, fp, para)
        hit = cache.get(key)
        if hit is not None:
            answers[i] = hit                                 # answered on an earlier run
        else:
            waiting.setdefault(key, []).append(i)
            key_text[key] = para

    # identical paragraphs are sent once, under the number of the first one
    items = [(ids[0], key_text[key]) for key, ids in waiting.items()]
    key_of = {ids[0]: key for key, ids in waiting.items()}
    batches = make_batches(items, batch_size)
    log.info("%d paragraphs, %d to send in %d request(s)", len(paras), len(items), len(batches))

    if batches:
        with ThreadPoolExecutor(max_workers=min(workers, len(batches))) as pool:
            for result in pool.map(lambda b: proofread_with_retries(b, lang, guide), batches):
                for rep, errors in result.items():
                    cache.put(key_of[rep], errors)
                    for i in waiting[key_of[rep]]:
                        answers[i] = errors

    edits_by_para = {}
    for i, (s, e) in enumerate(paras):
        placed = locate(text[s:e], answers.get(i, []))
        if placed:
            edits_by_para[i] = build_edits(s, text[s:e], placed)

    for _ in range(3):
        all_edits = [edit for edits in edits_by_para.values() for edit in edits]
        result = apply_edits(text, all_edits)
        bad = check_invariant(text, result)
        if not bad:
            return result
        for i in bad:
            edits_by_para.pop(i, None)
    return text