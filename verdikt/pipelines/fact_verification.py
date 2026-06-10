"""Fact verification pipeline: claim extraction -> evidence retrieval -> NLI -> aggregation -> metrics."""

from dataclasses import dataclass, field

from typing import Optional

from verdikt.components.aggregator import aggregate_nli
from verdikt.components.aligner import align_claim
from verdikt.components.claim_extractor import extract_claims
from verdikt.components.chunker import chunk_document
from verdikt.components.evidence_retriever import get_evidence_passages
from verdikt.components.metrics import compute_fact_metrics


@dataclass
class ClaimResult:
    claim: str
    label: str  # SUPPORTED | CONTRADICTED | NOT_FOUND
    reason: str
    evidence_used: list[dict] = field(default_factory=list)


@dataclass
class FactVerificationResult:
    metrics: dict
    claim_results: list[ClaimResult]
    warning: str = ""


def run_fact_verification(
    document: str,
    reference_document: Optional[str] = None,
    use_wikipedia: bool = True,
    use_arxiv: bool = True,
    verbose: bool = False,
) -> FactVerificationResult:
    """
    Full fact verification pipeline.

    Args:
        document: The text to verify.
        reference_document: Optional additional document to use as evidence source.
        use_wikipedia: Whether to search Wikipedia for evidence.
        use_arxiv: Whether to search arXiv for evidence.
        verbose: Print progress to stdout.
    """
    # Step 1: Extract claims
    if verbose:
        print("Extracting claims...")
    claims = extract_claims(document)

    if not claims:
        return FactVerificationResult(
            metrics=compute_fact_metrics(0, 0, 0),
            claim_results=[],
            warning="No claims could be extracted from the document.",
        )

    if verbose:
        print(f"Found {len(claims)} claims.")

    claim_results: list[ClaimResult] = []

    for i, claim in enumerate(claims, 1):
        if verbose:
            print(f"\n[{i}/{len(claims)}] Claim: {claim}")

        # Step 2: Retrieve evidence
        evidence_passages = get_evidence_passages(
            query=claim,
            document_text=reference_document,
            use_wikipedia=use_wikipedia,
            use_arxiv=use_arxiv,
        )

        if not evidence_passages:
            claim_results.append(
                ClaimResult(claim=claim, label="NOT_FOUND", reason="No evidence found.")
            )
            if verbose:
                print("  -> NOT_FOUND (no evidence retrieved)")
            continue

        # Step 3: Chunk each evidence source and run NLI
        # Cap chunks per passage to limit API calls (free tier: 15 RPM)
        chunk_labels: list[str] = []
        best_reason = ""
        used_evidence: list[dict] = []

        for passage in evidence_passages:
            chunks = chunk_document(passage["text"], max_tokens=300)[:3]
            for chunk in chunks:
                label, reason = align_claim(claim, chunk.text)
                chunk_labels.append(label)
                if label in ("SUPPORTED", "CONTRADICTED") and not best_reason:
                    best_reason = reason
                    used_evidence.append(
                        {
                            "source": passage["source"],
                            "url": passage.get("url"),
                            "text": chunk.text[:200],
                        }
                    )
                if verbose:
                    print(f"  [{passage['source']}] chunk {chunk.index}: {label}")

        # Step 4: Aggregate
        final_label = aggregate_nli(chunk_labels)
        if verbose:
            print(f"  -> FINAL: {final_label}")

        claim_results.append(
            ClaimResult(
                claim=claim,
                label=final_label,
                reason=best_reason,
                evidence_used=used_evidence,
            )
        )

    # Step 5: Compute metrics
    supported = sum(1 for r in claim_results if r.label == "SUPPORTED")
    contradicted = sum(1 for r in claim_results if r.label == "CONTRADICTED")
    not_found = sum(1 for r in claim_results if r.label == "NOT_FOUND")

    metrics = compute_fact_metrics(supported, contradicted, not_found)

    return FactVerificationResult(metrics=metrics, claim_results=claim_results)
