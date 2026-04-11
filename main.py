"""CLI entry point for the document verification system."""

import argparse
import json
import os
import sys

from dotenv import load_dotenv

load_dotenv()


def _check_api_key():
    if not os.getenv("GOOGLE_API_KEY"):
        print(
            "Error: GOOGLE_API_KEY is not set.\n"
            "Get a free key from https://aistudio.google.com/apikey and add it to your .env file.",
            file=sys.stderr,
        )
        sys.exit(1)


def _print_fact_results(result) -> None:
    m = result.metrics
    print("\n" + "=" * 60)
    print("FACT VERIFICATION RESULTS")
    print("=" * 60)
    if result.warning:
        print(f"Warning: {result.warning}")
        return

    print(f"  Total Claims:        {m['total_claims']}")
    print(f"  Supported:           {m['supported']}")
    print(f"  Contradicted:        {m['contradicted']}")
    print(f"  Not Found:           {m['not_found']}")
    print()
    print(f"  Accuracy:            {m['accuracy']:.1f}%")
    print(f"  Coverage:            {m['coverage']:.1f}%")
    print(f"  Contradiction Rate:  {m['contradiction_rate']:.1f}%")
    print(f"  Risk Score:          {m['risk']:.4f}")
    print()
    print("CLAIM BREAKDOWN:")
    print("-" * 60)
    for r in result.claim_results:
        icon = {"SUPPORTED": "✓", "CONTRADICTED": "✗", "NOT_FOUND": "?"}.get(r.label, "?")
        print(f"  [{icon}] {r.label:<13} {r.claim}")
        if r.reason:
            print(f"          Reason: {r.reason}")
    print("=" * 60)


def _print_guideline_results(result) -> None:
    m = result.metrics
    print("\n" + "=" * 60)
    print("GUIDELINE COMPLIANCE RESULTS")
    print("=" * 60)
    if result.warning:
        print(f"Warning: {result.warning}")
        return

    print(f"  Total Constraints:   {m['total_constraints']}")
    print(f"  Satisfied:           {m['satisfied']}")
    print(f"  Violated:            {m['violated']}")
    print(f"  Missing:             {m['missing']}")
    print()
    print(f"  Compliance:          {m['compliance']:.1f}%")
    print(f"  Violation Rate:      {m['violation_rate']:.1f}%")
    print(f"  Missing Rate:        {m['missing_rate']:.1f}%")
    print()
    print("CONSTRAINT BREAKDOWN:")
    print("-" * 60)
    for r in result.constraint_results:
        icon = {"SATISFIED": "✓", "VIOLATED": "✗", "MISSING": "?"}.get(r.label, "?")
        ctype = f"[{r.constraint.type[:3]}]"
        print(f"  [{icon}] {ctype} {r.label:<10} {r.constraint.text}")
        if r.reason:
            print(f"          Reason: {r.reason}")
    print("=" * 60)


def cmd_fact(args) -> None:
    _check_api_key()

    document = args.text or open(args.document).read()
    reference = open(args.reference).read() if args.reference else None

    from fact_checker.pipelines.fact_verification import run_fact_verification

    result = run_fact_verification(
        document=document,
        reference_document=reference,
        use_wikipedia=not args.no_wikipedia,
        use_arxiv=not args.no_arxiv,
        verbose=args.verbose,
    )

    if args.json:
        output = {
            "metrics": result.metrics,
            "claims": [
                {"claim": r.claim, "label": r.label, "reason": r.reason}
                for r in result.claim_results
            ],
        }
        if result.warning:
            output["warning"] = result.warning
        print(json.dumps(output, indent=2))
    else:
        _print_fact_results(result)


def cmd_guideline(args) -> None:
    _check_api_key()

    document = args.text or open(args.document).read()
    guidelines = args.guidelines_text or open(args.guidelines).read()

    from fact_checker.pipelines.guideline_compliance import run_guideline_compliance

    result = run_guideline_compliance(
        document=document,
        guidelines=guidelines,
        verbose=args.verbose,
    )

    if args.json:
        output = {
            "metrics": result.metrics,
            "constraints": [
                {
                    "id": r.constraint.id,
                    "type": r.constraint.type,
                    "text": r.constraint.text,
                    "label": r.label,
                    "reason": r.reason,
                }
                for r in result.constraint_results
            ],
        }
        if result.warning:
            output["warning"] = result.warning
        print(json.dumps(output, indent=2))
    else:
        _print_guideline_results(result)


def main():
    parser = argparse.ArgumentParser(
        description="Document Verification System — fact checking and guideline compliance."
    )
    subparsers = parser.add_subparsers(dest="mode", required=True)

    # --- fact mode ---
    fact_parser = subparsers.add_parser("fact", help="Fact verification mode")
    fact_input = fact_parser.add_mutually_exclusive_group(required=True)
    fact_input.add_argument("--document", "-d", help="Path to document file")
    fact_input.add_argument("--text", "-t", help="Document text (inline)")
    fact_parser.add_argument("--reference", "-r", help="Path to reference document for evidence")
    fact_parser.add_argument("--no-wikipedia", action="store_true", help="Disable Wikipedia search")
    fact_parser.add_argument("--no-arxiv", action="store_true", help="Disable arXiv search")
    fact_parser.add_argument("--json", action="store_true", help="Output results as JSON")
    fact_parser.add_argument("--verbose", "-v", action="store_true", help="Print progress")
    fact_parser.set_defaults(func=cmd_fact)

    # --- guideline mode ---
    guide_parser = subparsers.add_parser("guideline", help="Guideline compliance mode")
    guide_input = guide_parser.add_mutually_exclusive_group(required=True)
    guide_input.add_argument("--document", "-d", help="Path to document file")
    guide_input.add_argument("--text", "-t", help="Document text (inline)")
    guide_group = guide_parser.add_mutually_exclusive_group(required=True)
    guide_group.add_argument("--guidelines", "-g", help="Path to guidelines file")
    guide_group.add_argument("--guidelines-text", help="Guidelines text (inline)")
    guide_parser.add_argument("--json", action="store_true", help="Output results as JSON")
    guide_parser.add_argument("--verbose", "-v", action="store_true", help="Print progress")
    guide_parser.set_defaults(func=cmd_guideline)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
