"""LLM-based guideline parsing into typed constraints."""

from dataclasses import dataclass

from verdikt.utils import llm_client
from verdikt.utils.json_parser import LLMParseError, extract_json_array

_SYSTEM = """You are a guideline parsing system. Parse the given guidelines into a structured list of constraints.

Each constraint must be classified as exactly one of:
- REQUIREMENT: Something that MUST exist or be present in the document
- PROHIBITION: Something that MUST NOT exist or be present in the document

Return a JSON array of objects. Each object must have:
- "type": either "REQUIREMENT" or "PROHIBITION"
- "text": a concise description of what is required or prohibited

Example:
Input:
"Ensure the document:
1. Defines transformers
2. Does not mention recurrence
3. Includes performance comparison"

Output:
[
  {"type": "REQUIREMENT", "text": "Defines transformers"},
  {"type": "PROHIBITION", "text": "Mentions recurrence"},
  {"type": "REQUIREMENT", "text": "Includes performance comparison"}
]"""


@dataclass
class Constraint:
    id: int
    type: str  # "REQUIREMENT" or "PROHIBITION"
    text: str


def parse_guidelines(guidelines_text: str) -> list[Constraint]:
    """Parse guideline text into typed constraints using Gemini."""
    raw = llm_client.complete(
        system=_SYSTEM,
        user_message=f"Parse these guidelines into constraints:\n\n{guidelines_text}",
        max_tokens=2048,
    )

    try:
        items = extract_json_array(raw)
    except LLMParseError:
        return []

    constraints = []
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            continue
        ctype = str(item.get("type", "")).strip().upper()
        text = str(item.get("text", "")).strip()
        if ctype in ("REQUIREMENT", "PROHIBITION") and text:
            constraints.append(Constraint(id=i, type=ctype, text=text))

    return constraints
