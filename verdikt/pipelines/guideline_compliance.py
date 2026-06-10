"""Guideline compliance pipeline: parse constraints -> align against chunks -> aggregate -> metrics."""

from dataclasses import dataclass, field

from verdikt.components.aggregator import aggregate_constraint
from verdikt.components.aligner import align_constraint
from verdikt.components.chunker import chunk_document
from verdikt.components.guideline_parser import Constraint, parse_guidelines
from verdikt.components.metrics import compute_guideline_metrics


@dataclass
class ConstraintResult:
    constraint: Constraint
    label: str  # SATISFIED | VIOLATED | MISSING
    reason: str
    matched_chunk: str = ""


@dataclass
class GuidelineComplianceResult:
    metrics: dict
    constraint_results: list[ConstraintResult]
    warning: str = ""


def run_guideline_compliance(
    document: str,
    guidelines: str,
    verbose: bool = False,
) -> GuidelineComplianceResult:
    """
    Full guideline compliance pipeline.

    Args:
        document: The document to check.
        guidelines: The guideline text defining constraints.
        verbose: Print progress to stdout.
    """
    # Step 1: Chunk the document (deterministic, no LLM)
    chunks = chunk_document(document, max_tokens=300)
    if verbose:
        print(f"Document split into {len(chunks)} chunks.")

    # Step 2: Parse guidelines into constraints
    if verbose:
        print("Parsing guidelines...")
    constraints = parse_guidelines(guidelines)

    if not constraints:
        return GuidelineComplianceResult(
            metrics=compute_guideline_metrics(0, 0, 0),
            constraint_results=[],
            warning="No constraints could be parsed from the guidelines.",
        )

    if verbose:
        print(f"Found {len(constraints)} constraints.")

    constraint_results: list[ConstraintResult] = []

    # Step 3: Align each constraint against all document chunks
    for i, constraint in enumerate(constraints, 1):
        if verbose:
            print(f"\n[{i}/{len(constraints)}] {constraint.type}: {constraint.text}")

        chunk_labels: list[str] = []
        best_reason = ""
        best_chunk = ""

        for chunk in chunks:
            label, reason = align_constraint(
                constraint.type, constraint.text, chunk.text
            )
            chunk_labels.append(label)

            if label in ("SATISFIED", "VIOLATED") and not best_reason:
                best_reason = reason
                best_chunk = chunk.text[:200]

            if verbose:
                print(f"  chunk {chunk.index}: {label}")

        # Step 4: Aggregate per constraint type
        final_label = aggregate_constraint(chunk_labels, constraint.type)
        if verbose:
            print(f"  -> FINAL: {final_label}")

        constraint_results.append(
            ConstraintResult(
                constraint=constraint,
                label=final_label,
                reason=best_reason,
                matched_chunk=best_chunk,
            )
        )

    # Step 5: Compute metrics
    satisfied = sum(1 for r in constraint_results if r.label == "SATISFIED")
    violated = sum(1 for r in constraint_results if r.label == "VIOLATED")
    missing = sum(1 for r in constraint_results if r.label == "MISSING")

    metrics = compute_guideline_metrics(satisfied, violated, missing)

    return GuidelineComplianceResult(metrics=metrics, constraint_results=constraint_results)
