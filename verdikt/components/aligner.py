"""LLM-based NLI alignment for both fact verification and guideline compliance."""

from verdikt.utils import llm_client
from verdikt.utils.json_parser import (
    LLMParseError,
    extract_json_object,
    normalize_constraint_label,
    normalize_nli_label,
)

_NLI_SYSTEM = """You are a Natural Language Inference (NLI) classifier.

Your task: given a CLAIM and an EVIDENCE passage, determine the logical relationship.

Rules:
- Base your judgment ONLY on the evidence text provided. Do NOT use any external knowledge.
- SUPPORTED: The evidence explicitly entails or confirms the claim is true.
- CONTRADICTED: The evidence explicitly states something that conflicts with the claim.
- NOT_FOUND: The evidence does not contain enough information to support or contradict the claim.

Logical precision requirements:
- Handle quantifiers carefully: "all X" ≠ "some X". Evidence about "some" does not support a claim about "all".
- Handle negation correctly: evidence saying "X does not Y" does NOT support a claim that "X does Y".
- Handle modality: "can do X" ≠ "always does X".
- CONTRADICTED takes precedence: if evidence both supports and contradicts, return CONTRADICTED.

Return a JSON object with exactly two fields:
{"label": "SUPPORTED" | "CONTRADICTED" | "NOT_FOUND", "reason": "one brief sentence"}"""

_CONSTRAINT_SYSTEM = """You are a document compliance checker.

Your task: given a CONSTRAINT and a DOCUMENT CHUNK, determine whether the chunk satisfies, violates, or does not address the constraint.

For REQUIREMENT constraints:
- SATISFIED: The chunk fulfills or contains what is required.
- MISSING: The chunk does not address the requirement.

For PROHIBITION constraints:
- VIOLATED: The chunk positively asserts or contains the prohibited content.
- SATISFIED: The chunk explicitly negates or avoids the prohibited content.
- MISSING: Cannot determine from this chunk.

Important negation handling: If the prohibition is "mentions X" and the chunk says "does not use X", this is SATISFIED, not VIOLATED. Only mark VIOLATED if the document positively asserts the prohibited content.

Return a JSON object with exactly two fields:
{"label": "SATISFIED" | "VIOLATED" | "MISSING", "reason": "one brief sentence"}"""


def align_claim(claim: str, evidence: str) -> tuple[str, str]:
    """
    Run NLI between a claim and an evidence passage.
    Returns (label, reason) where label is SUPPORTED | CONTRADICTED | NOT_FOUND.
    """
    raw = llm_client.complete(
        system=_NLI_SYSTEM,
        user_message=f"CLAIM: {claim}\n\nEVIDENCE: {evidence}",
        max_tokens=128,
    )

    try:
        obj = extract_json_object(raw)
        label = normalize_nli_label(str(obj.get("label", "")))
        reason = str(obj.get("reason", "")).strip()
        return label, reason
    except LLMParseError:
        raw_upper = raw.upper()
        if "CONTRADICTED" in raw_upper:
            return "CONTRADICTED", ""
        if "SUPPORTED" in raw_upper:
            return "SUPPORTED", ""
        return "NOT_FOUND", ""


def align_constraint(
    constraint_type: str,
    constraint_text: str,
    chunk: str,
) -> tuple[str, str]:
    """
    Align a constraint against a document chunk.
    Returns (label, reason) where label is SATISFIED | VIOLATED | MISSING.
    """
    raw = llm_client.complete(
        system=_CONSTRAINT_SYSTEM,
        user_message=(
            f"CONSTRAINT TYPE: {constraint_type}\n"
            f"CONSTRAINT: {constraint_text}\n\n"
            f"DOCUMENT CHUNK: {chunk}"
        ),
        max_tokens=128,
    )

    try:
        obj = extract_json_object(raw)
        label = normalize_constraint_label(str(obj.get("label", "")))
        reason = str(obj.get("reason", "")).strip()
        return label, reason
    except LLMParseError:
        raw_upper = raw.upper()
        if "VIOLATED" in raw_upper:
            return "VIOLATED", ""
        if "SATISFIED" in raw_upper:
            return "SATISFIED", ""
        return "MISSING", ""
