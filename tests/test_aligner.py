from unittest.mock import patch

from fact_checker.components.aligner import align_claim, align_constraint


class TestAlignClaim:
    def test_returns_label_and_reason(self):
        response = '{"label": "SUPPORTED", "reason": "Evidence confirms the claim."}'
        with patch("fact_checker.utils.llm_client.complete", return_value=response):
            label, reason = align_claim("claim text", "evidence text")
        assert label == "SUPPORTED"
        assert reason == "Evidence confirms the claim."

    def test_contradicted_label(self):
        response = '{"label": "CONTRADICTED", "reason": "Evidence opposes the claim."}'
        with patch("fact_checker.utils.llm_client.complete", return_value=response):
            label, _ = align_claim("claim", "evidence")
        assert label == "CONTRADICTED"

    def test_not_found_label(self):
        response = '{"label": "NOT_FOUND", "reason": "No relevant evidence."}'
        with patch("fact_checker.utils.llm_client.complete", return_value=response):
            label, _ = align_claim("claim", "evidence")
        assert label == "NOT_FOUND"

    def test_normalizes_alias_contradicts(self):
        response = '{"label": "CONTRADICTS", "reason": "opposite"}'
        with patch("fact_checker.utils.llm_client.complete", return_value=response):
            label, _ = align_claim("claim", "evidence")
        assert label == "CONTRADICTED"

    def test_normalizes_alias_supports(self):
        response = '{"label": "SUPPORTS", "reason": "yes"}'
        with patch("fact_checker.utils.llm_client.complete", return_value=response):
            label, _ = align_claim("claim", "evidence")
        assert label == "SUPPORTED"

    def test_fallback_on_parse_error_finds_contradicted(self):
        with patch("fact_checker.utils.llm_client.complete", return_value="The claim is CONTRADICTED by this."):
            label, reason = align_claim("claim", "evidence")
        assert label == "CONTRADICTED"
        assert reason == ""

    def test_fallback_on_parse_error_finds_supported(self):
        with patch("fact_checker.utils.llm_client.complete", return_value="This is SUPPORTED clearly."):
            label, reason = align_claim("claim", "evidence")
        assert label == "SUPPORTED"

    def test_fallback_on_parse_error_defaults_not_found(self):
        with patch("fact_checker.utils.llm_client.complete", return_value="I cannot determine anything here."):
            label, _ = align_claim("claim", "evidence")
        assert label == "NOT_FOUND"

    def test_missing_reason_returns_empty_string(self):
        response = '{"label": "SUPPORTED"}'
        with patch("fact_checker.utils.llm_client.complete", return_value=response):
            _, reason = align_claim("claim", "evidence")
        assert reason == ""


class TestAlignConstraint:
    def test_returns_satisfied(self):
        response = '{"label": "SATISFIED", "reason": "Chunk meets the requirement."}'
        with patch("fact_checker.utils.llm_client.complete", return_value=response):
            label, reason = align_constraint("REQUIREMENT", "Defines transformers", "chunk text")
        assert label == "SATISFIED"
        assert reason == "Chunk meets the requirement."

    def test_returns_violated(self):
        response = '{"label": "VIOLATED", "reason": "Prohibited content found."}'
        with patch("fact_checker.utils.llm_client.complete", return_value=response):
            label, _ = align_constraint("PROHIBITION", "Mentions recurrence", "uses recurrence networks")
        assert label == "VIOLATED"

    def test_returns_missing(self):
        response = '{"label": "MISSING", "reason": "Not addressed."}'
        with patch("fact_checker.utils.llm_client.complete", return_value=response):
            label, _ = align_constraint("REQUIREMENT", "Includes examples", "unrelated chunk")
        assert label == "MISSING"

    def test_normalizes_violation_alias(self):
        response = '{"label": "VIOLATION", "reason": "bad content"}'
        with patch("fact_checker.utils.llm_client.complete", return_value=response):
            label, _ = align_constraint("PROHIBITION", "mentions X", "X is here")
        assert label == "VIOLATED"

    def test_fallback_on_parse_error_finds_violated(self):
        with patch("fact_checker.utils.llm_client.complete", return_value="This is clearly VIOLATED."):
            label, _ = align_constraint("PROHIBITION", "constraint", "chunk")
        assert label == "VIOLATED"

    def test_fallback_on_parse_error_finds_satisfied(self):
        with patch("fact_checker.utils.llm_client.complete", return_value="The chunk is SATISFIED."):
            label, _ = align_constraint("REQUIREMENT", "constraint", "chunk")
        assert label == "SATISFIED"

    def test_fallback_on_parse_error_defaults_missing(self):
        with patch("fact_checker.utils.llm_client.complete", return_value="unclear response here"):
            label, _ = align_constraint("REQUIREMENT", "constraint", "chunk")
        assert label == "MISSING"
