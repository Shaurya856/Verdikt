"""Metric computation for fact verification and guideline compliance."""


def compute_fact_metrics(
    supported: int, contradicted: int, not_found: int
) -> dict:
    """
    Compute fact verification metrics.

    N = total claims
    S = supported, C = contradicted, U = not_found

    accuracy          = (S / N) × 100
    risk              = (0×S + 0.3×U + 0.7×C) / N
    contradiction_rate = (C / N) × 100
    coverage          = ((S + C) / N) × 100
    """
    N = supported + contradicted + not_found
    if N == 0:
        return {
            "accuracy": 0.0,
            "risk": 0.0,
            "contradiction_rate": 0.0,
            "coverage": 0.0,
            "total_claims": 0,
            "supported": 0,
            "contradicted": 0,
            "not_found": 0,
        }

    return {
        "accuracy": round((supported / N) * 100, 2),
        "risk": round((0.3 * not_found + 0.7 * contradicted) / N, 4),
        "contradiction_rate": round((contradicted / N) * 100, 2),
        "coverage": round(((supported + contradicted) / N) * 100, 2),
        "total_claims": N,
        "supported": supported,
        "contradicted": contradicted,
        "not_found": not_found,
    }


def compute_guideline_metrics(
    satisfied: int, violated: int, missing: int
) -> dict:
    """
    Compute guideline compliance metrics.

    T = total constraints
    S = satisfied, V = violated, M = missing

    compliance    = (S / T) × 100
    violation_rate = (V / T) × 100
    missing_rate  = (M / T) × 100
    """
    T = satisfied + violated + missing
    if T == 0:
        return {
            "compliance": 0.0,
            "violation_rate": 0.0,
            "missing_rate": 0.0,
            "total_constraints": 0,
            "satisfied": 0,
            "violated": 0,
            "missing": 0,
        }

    return {
        "compliance": round((satisfied / T) * 100, 2),
        "violation_rate": round((violated / T) * 100, 2),
        "missing_rate": round((missing / T) * 100, 2),
        "total_constraints": T,
        "satisfied": satisfied,
        "violated": violated,
        "missing": missing,
    }
