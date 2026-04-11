"""LLM-based atomic claim extraction from document text."""

from fact_checker.utils import llm_client
from fact_checker.utils.json_parser import LLMParseError, extract_json_array

_SYSTEM = """You are a claim extraction system. Extract all atomic factual claims from the given text.

Rules:
- Each claim must be a single, verifiable factual statement
- Do not paraphrase or change the meaning of any claim
- Do not merge multiple facts into one claim
- Do not invent or infer claims that are not explicitly stated in the text
- Do not include opinions, recommendations, or subjective statements
- Do not include procedural instructions or questions

Return a JSON array of strings. Each string is one atomic claim.

Example:
Input: "Transformers outperform RNNs in many tasks and do not use recurrence."
Output: ["Transformers outperform RNNs in many tasks", "Transformers do not use recurrence"]"""


def extract_claims(document: str) -> list[str]:
    """Extract atomic factual claims from document text using Gemini."""
    raw = llm_client.complete(
        system=_SYSTEM,
        user_message=f"Extract atomic claims from:\n\n{document}",
        max_tokens=4096,
    )

    try:
        claims = extract_json_array(raw)
        return [str(c) for c in claims if isinstance(c, str) and c.strip()]
    except LLMParseError:
        return []
