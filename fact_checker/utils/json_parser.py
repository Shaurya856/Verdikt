"""Robust JSON extraction from LLM responses."""

import json
import re


class LLMParseError(Exception):
    pass


def extract_json_array(text: str) -> list:
    """Extract a JSON array from LLM output, handling markdown fences and preamble."""
    text = text.strip()

    # Strip markdown code fences
    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence_match:
        text = fence_match.group(1).strip()

    # Try direct parse
    try:
        result = json.loads(text)
        if isinstance(result, list):
            return result
    except json.JSONDecodeError:
        pass

    # Extract between first [ and last ]
    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end != -1 and end > start:
        try:
            result = json.loads(text[start : end + 1])
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            pass

    raise LLMParseError(f"Could not extract JSON array from: {text[:200]}")


def extract_json_object(text: str) -> dict:
    """Extract a JSON object from LLM output, handling markdown fences and preamble."""
    text = text.strip()

    # Strip markdown code fences
    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence_match:
        text = fence_match.group(1).strip()

    # Try direct parse
    try:
        result = json.loads(text)
        if isinstance(result, dict):
            return result
    except json.JSONDecodeError:
        pass

    # Extract between first { and last }
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            result = json.loads(text[start : end + 1])
            if isinstance(result, dict):
                return result
        except json.JSONDecodeError:
            pass

    raise LLMParseError(f"Could not extract JSON object from: {text[:200]}")


# Normalize variant NLI labels to canonical form
_NLI_LABEL_MAP = {
    "SUPPORTED": "SUPPORTED",
    "SUPPORT": "SUPPORTED",
    "SUPPORTS": "SUPPORTED",
    "CONTRADICTED": "CONTRADICTED",
    "CONTRADICT": "CONTRADICTED",
    "CONTRADICTS": "CONTRADICTED",
    "CONTRADICTION": "CONTRADICTED",
    "NOT_FOUND": "NOT_FOUND",
    "NOTFOUND": "NOT_FOUND",
    "NO_INFORMATION": "NOT_FOUND",
    "UNKNOWN": "NOT_FOUND",
    "INSUFFICIENT": "NOT_FOUND",
}

_CONSTRAINT_LABEL_MAP = {
    "SATISFIED": "SATISFIED",
    "SATISFY": "SATISFIED",
    "VIOLATED": "VIOLATED",
    "VIOLATION": "VIOLATED",
    "VIOLATES": "VIOLATED",
    "MISSING": "MISSING",
    "NOT_FOUND": "MISSING",
    "UNKNOWN": "MISSING",
}


def normalize_nli_label(label: str) -> str:
    return _NLI_LABEL_MAP.get(label.strip().upper(), "NOT_FOUND")


def normalize_constraint_label(label: str) -> str:
    return _CONSTRAINT_LABEL_MAP.get(label.strip().upper(), "MISSING")
