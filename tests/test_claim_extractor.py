from unittest.mock import patch

from fact_checker.components.claim_extractor import extract_claims


class TestExtractClaims:
    def test_returns_list_of_strings(self):
        response = '["Transformers outperform RNNs", "Transformers do not use recurrence"]'
        with patch("fact_checker.utils.llm_client.complete", return_value=response):
            claims = extract_claims("some document text")
        assert claims == ["Transformers outperform RNNs", "Transformers do not use recurrence"]

    def test_handles_markdown_fenced_response(self):
        response = '```json\n["claim one", "claim two"]\n```'
        with patch("fact_checker.utils.llm_client.complete", return_value=response):
            claims = extract_claims("text")
        assert claims == ["claim one", "claim two"]

    def test_returns_empty_list_on_parse_error(self):
        with patch("fact_checker.utils.llm_client.complete", return_value="not valid json at all"):
            claims = extract_claims("text")
        assert claims == []

    def test_returns_empty_list_on_empty_array(self):
        with patch("fact_checker.utils.llm_client.complete", return_value="[]"):
            claims = extract_claims("text")
        assert claims == []

    def test_filters_out_non_string_items(self):
        response = '["valid claim", 123, null, "another claim"]'
        with patch("fact_checker.utils.llm_client.complete", return_value=response):
            claims = extract_claims("text")
        assert claims == ["valid claim", "another claim"]

    def test_filters_blank_strings(self):
        response = '["real claim", "   ", ""]'
        with patch("fact_checker.utils.llm_client.complete", return_value=response):
            claims = extract_claims("text")
        assert claims == ["real claim"]

    def test_passes_document_in_user_message(self):
        with patch("fact_checker.utils.llm_client.complete", return_value='["c"]') as mock_complete:
            extract_claims("my document")
        call_kwargs = mock_complete.call_args
        user_msg = call_kwargs[1].get("user_message") or call_kwargs[0][1]
        assert "my document" in user_msg
