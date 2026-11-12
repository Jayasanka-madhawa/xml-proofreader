import json

CATEGORIES = ["grammar", "spelling", "punctuation", "capitalization", "clarity", "styleguide"]

EXAMPLE = """\
Paragraph: My name is john and the firm earned $2,000,000 in January, 2024.
Errors:
[{"original": "john", "prefix": "name is ", "type": "capitalization", "correction": "John", "reason": "Proper nouns are capitalized"},
 {"original": "$2,000,000", "prefix": "earned ", "type": "styleguide", "correction": "$2 million", "reason": "Spell out million, billion, etc."},
 {"original": "January, 2024", "prefix": "in ", "type": "styleguide", "correction": "January 2024", "reason": "No comma between month and year"}]
A paragraph with no problems gets an empty list."""


def build_system_prompt(lang, guide):
    return f"""You are an expert copy editor. You receive paragraphs and report their errors by calling the `report_errors` tool exactly once. You never rewrite paragraphs; you only report errors.

# Language
The text is in the language with BCP-47 tag "{lang}". Proofread it by that language's norms.

# What to check
Grammar, spelling, punctuation, capitalization, clarity, and every rule of the Style_Guide below. Allowed values for `type`: {", ".join(CATEGORIES)}. A Style_Guide violation is always `styleguide`.

# How to report an error
- `original`: the faulty text, copied EXACTLY from the paragraph. Keep it as short as possible (usually one word or a short phrase).
- `prefix`: up to 20 characters that come right before `original` in the paragraph, copied exactly ("" if it starts the paragraph). It tells us which occurrence you mean.
- `correction`: the text that replaces `original`. It must differ from `original`.
- `reason`: a few words naming the rule that was broken.
- A missing comma or word has no characters to wrap: wrap the neighbouring word(s) and give the fixed version as `correction`.
- Errors must not overlap.

# Be precise, not busy
- Report only real errors or clear Style_Guide violations. Do not rewrite for taste.
- Never touch quoted material or names of laws and works.
- If a paragraph is fine, return an empty list for it. Every paragraph id must appear in `results`.

# Example
{EXAMPLE}

# Style_Guide
<style_guide>
{guide}
</style_guide>"""


def build_user_message(paragraphs):
    """paragraphs: list of (id, text)."""
    payload = [{"id": i, "text": t} for i, t in paragraphs]
    return "Proofread these paragraphs and answer with the `report_errors` tool.\n" + json.dumps(payload, ensure_ascii=False, indent=1)


REPORT_TOOL = {
    "name": "report_errors",
    "description": "Report all proofreading errors, grouped by paragraph id.",
    "input_schema": {
        "type": "object",
        "properties": {
            "results": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "errors": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "original": {"type": "string"},
                                    "prefix": {"type": "string"},
                                    "type": {"type": "string", "enum": CATEGORIES},
                                    "correction": {"type": "string"},
                                    "reason": {"type": "string"},
                                },
                                "required": ["original", "prefix", "type", "correction", "reason"],
                            },
                        },
                    },
                    "required": ["id", "errors"],
                },
            }
        },
        "required": ["results"],
    },
}

PROMPT_VERSION = "1"      # bump when the prompt changes so old cached answers are not reused