import pytest

from verdikt.components.metrics import compute_fact_metrics, compute_guideline_metrics


class TestComputeFactMetrics:
    def test_all_supported(self):
        m = compute_fact_metrics(supported=4, contradicted=0, not_found=0)
        assert m["accuracy"] == 100.0
        assert m["risk"] == 0.0
        assert m["contradiction_rate"] == 0.0
        assert m["coverage"] == 100.0
        assert m["total_claims"] == 4

    def test_all_contradicted(self):
        m = compute_fact_metrics(supported=0, contradicted=4, not_found=0)
        assert m["accuracy"] == 0.0
        assert m["contradiction_rate"] == 100.0
        assert m["risk"] == pytest.approx(0.7)
        assert m["coverage"] == 100.0

    def test_all_not_found(self):
        m = compute_fact_metrics(supported=0, contradicted=0, not_found=4)
        assert m["accuracy"] == 0.0
        assert m["risk"] == pytest.approx(0.3)
        assert m["coverage"] == 0.0
        assert m["contradiction_rate"] == 0.0

    def test_mixed_equal_split(self):
        m = compute_fact_metrics(supported=2, contradicted=1, not_found=1)
        assert m["total_claims"] == 4
        assert m["accuracy"] == 50.0
        assert m["coverage"] == 75.0
        assert m["contradiction_rate"] == 25.0

    def test_zero_claims_returns_zeros(self):
        m = compute_fact_metrics(0, 0, 0)
        assert m["accuracy"] == 0.0
        assert m["risk"] == 0.0
        assert m["total_claims"] == 0

    def test_contains_all_keys(self):
        m = compute_fact_metrics(1, 1, 1)
        for key in ("accuracy", "risk", "contradiction_rate", "coverage",
                    "total_claims", "supported", "contradicted", "not_found"):
            assert key in m

    def test_counts_match_inputs(self):
        m = compute_fact_metrics(supported=3, contradicted=2, not_found=1)
        assert m["supported"] == 3
        assert m["contradicted"] == 2
        assert m["not_found"] == 1

    def test_risk_formula(self):
        # risk = (0.3 * not_found + 0.7 * contradicted) / total
        m = compute_fact_metrics(supported=0, contradicted=2, not_found=2)
        expected = (0.3 * 2 + 0.7 * 2) / 4
        assert m["risk"] == pytest.approx(expected, abs=1e-4)


class TestComputeGuidelineMetrics:
    def test_all_satisfied(self):
        m = compute_guideline_metrics(satisfied=3, violated=0, missing=0)
        assert m["compliance"] == 100.0
        assert m["violation_rate"] == 0.0
        assert m["missing_rate"] == 0.0

    def test_all_violated(self):
        m = compute_guideline_metrics(satisfied=0, violated=3, missing=0)
        assert m["compliance"] == 0.0
        assert m["violation_rate"] == 100.0

    def test_mixed(self):
        m = compute_guideline_metrics(satisfied=2, violated=1, missing=1)
        assert m["total_constraints"] == 4
        assert m["compliance"] == 50.0
        assert m["violation_rate"] == 25.0
        assert m["missing_rate"] == 25.0

    def test_zero_constraints_returns_zeros(self):
        m = compute_guideline_metrics(0, 0, 0)
        assert m["compliance"] == 0.0
        assert m["total_constraints"] == 0

    def test_contains_all_keys(self):
        m = compute_guideline_metrics(1, 1, 1)
        for key in ("compliance", "violation_rate", "missing_rate",
                    "total_constraints", "satisfied", "violated", "missing"):
            assert key in m

    def test_counts_match_inputs(self):
        m = compute_guideline_metrics(satisfied=4, violated=2, missing=1)
        assert m["satisfied"] == 4
        assert m["violated"] == 2
        assert m["missing"] == 1
