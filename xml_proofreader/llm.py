import threading
import anthropic
from dotenv import load_dotenv

from .config import SETTINGS
from .prompts import REPORT_TOOL, build_system_prompt, build_user_message

load_dotenv()                      # makes ANTHROPIC_API_KEY available from .env
MODEL = SETTINGS["model"]          # set in config.json

# running totals for the performance summary (updated from several threads)
USAGE = {"calls": 0, "input_tokens": 0, "output_tokens": 0, "cache_read_tokens": 0}
_lock = threading.Lock()


def _record(usage):
    with _lock:
        USAGE["calls"] += 1
        USAGE["input_tokens"] += (usage.input_tokens or 0) + (getattr(usage, "cache_creation_input_tokens", 0) or 0)
        USAGE["output_tokens"] += usage.output_tokens or 0
        USAGE["cache_read_tokens"] += getattr(usage, "cache_read_input_tokens", 0) or 0


def parse_results(payload):
    """Turn the tool's JSON into {paragraph id: [error dicts]}."""
    out = {}
    for item in payload.get("results", []):
        out[item["id"]] = item.get("errors", [])
    return out


def proofread(paragraphs, lang, guide, client=None):
    """paragraphs: list of (id, text). Returns {id: [errors]}."""
    client = client or anthropic.Anthropic()
    response = client.messages.create(
        model=MODEL,
        max_tokens=4000,
        system=[{
            "type": "text",
            "text": build_system_prompt(lang, guide),
            "cache_control": {"type": "ephemeral"},    # the guide is identical every call
        }],
        tools=[REPORT_TOOL],
        messages=[{"role": "user", "content": build_user_message(paragraphs)}],
    )
    if getattr(response, "usage", None):
        _record(response.usage)
    for block in response.content:
        if block.type == "tool_use" and block.name == "report_errors":
            return parse_results(block.input)
    raise RuntimeError("The model did not call report_errors")