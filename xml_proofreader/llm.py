import anthropic
from dotenv import load_dotenv

from .prompts import REPORT_TOOL, build_system_prompt, build_user_message

load_dotenv()                      # makes ANTHROPIC_API_KEY available from .env
MODEL = "claude-sonnet-5-5"


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
    for block in response.content:
        if block.type == "tool_use" and block.name == "report_errors":
            return parse_results(block.input)
    raise RuntimeError("The model did not call report_errors")