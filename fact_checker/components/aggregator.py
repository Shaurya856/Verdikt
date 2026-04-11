"""Deterministic aggregation logic for NLI and constraint results."""


def aggregate_nli(labels: list[str]) -> str:
    """
    Aggregate NLI labels across multiple evidence chunks for a single claim.

    Rules:
    - CONTRADICTED takes precedence over everything
    - SUPPORTED requires at least one explicit entailment
    - Otherwise NOT_FOUND
    """
    if "CONTRADICTED" in labels:
        return "CONTRADICTED"
    if "SUPPORTED" in labels:
        return "SUPPORTED"
    return "NOT_FOUND"


def aggregate_constraint(labels: list[str], constraint_type: str) -> str:
    """
    Aggregate alignment labels across all document chunks for a single constraint.

    REQUIREMENT:
    - Any SATISFIED chunk -> SATISFIED
    - Otherwise -> MISSING

    PROHIBITION:
    - Any VIOLATED chunk -> VIOLATED
    - Otherwise -> SATISFIED
    """
    if constraint_type == "REQUIREMENT":
        if "SATISFIED" in labels:
            return "SATISFIED"
        return "MISSING"
    else:  # PROHIBITION
        if "VIOLATED" in labels:
            return "VIOLATED"
        return "SATISFIED"
