import pytest
from unittest.mock import patch

import fact_checker.utils.llm_client as llm_client


class TestAvailableProviders:
    def test_empty_when_no_keys_set(self):
        # conftest autouse fixture clears all keys
        assert llm_client.available_providers() == []

    def test_groq_detected_when_key_set(self, monkeypatch):
        monkeypatch.setenv("GROQ_API_KEY", "test-key")
        assert "groq" in llm_client.available_providers()

    def test_nvidia_detected(self, monkeypatch):
        monkeypatch.setenv("NVIDIA_API_KEY", "test-key")
        assert "nvidia" in llm_client.available_providers()

    def test_openrouter_detected(self, monkeypatch):
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
        assert "openrouter" in llm_client.available_providers()

    def test_google_detected(self, monkeypatch):
        monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
        assert "google" in llm_client.available_providers()

    def test_priority_order_with_all_keys(self, monkeypatch):
        monkeypatch.setenv("GROQ_API_KEY", "k1")
        monkeypatch.setenv("NVIDIA_API_KEY", "k2")
        monkeypatch.setenv("OPENROUTER_API_KEY", "k3")
        monkeypatch.setenv("GOOGLE_API_KEY", "k4")
        assert llm_client.available_providers() == ["groq", "nvidia", "openrouter", "google"]

    def test_only_configured_providers_returned(self, monkeypatch):
        monkeypatch.setenv("NVIDIA_API_KEY", "k")
        monkeypatch.setenv("GOOGLE_API_KEY", "k")
        result = llm_client.available_providers()
        assert result == ["nvidia", "google"]
        assert "groq" not in result
        assert "openrouter" not in result


class TestComplete:
    def test_calls_available_provider(self, monkeypatch):
        monkeypatch.setenv("GROQ_API_KEY", "key")
        with patch.object(llm_client, "_call_provider", return_value="answer") as mock_call:
            result = llm_client.complete("sys", "usr")
        assert result == "answer"
        mock_call.assert_called_once_with("groq", "sys", "usr", 1024)

    def test_respects_explicit_llm_provider(self, monkeypatch):
        monkeypatch.setenv("GROQ_API_KEY", "k1")
        monkeypatch.setenv("GOOGLE_API_KEY", "k2")
        monkeypatch.setenv("LLM_PROVIDER", "google")
        with patch.object(llm_client, "_call_provider", return_value="ok") as mock_call:
            llm_client.complete("s", "u")
        assert mock_call.call_args[0][0] == "google"

    def test_passes_custom_max_tokens(self, monkeypatch):
        monkeypatch.setenv("GROQ_API_KEY", "key")
        with patch.object(llm_client, "_call_provider", return_value="ok") as mock_call:
            llm_client.complete("s", "u", max_tokens=512)
        assert mock_call.call_args[0][3] == 512

    def test_falls_back_on_runtime_error(self, monkeypatch):
        monkeypatch.setenv("GROQ_API_KEY", "k1")
        monkeypatch.setenv("GOOGLE_API_KEY", "k2")

        calls = []

        def mock_call(provider, system, user_message, max_tokens):
            calls.append(provider)
            if provider == "groq":
                raise RuntimeError("groq exhausted")
            return "google result"

        with patch.object(llm_client, "_call_provider", side_effect=mock_call):
            result = llm_client.complete("sys", "usr")

        assert result == "google result"
        assert calls == ["groq", "google"]

    def test_raises_when_all_providers_fail(self, monkeypatch):
        monkeypatch.setenv("GROQ_API_KEY", "k1")
        monkeypatch.setenv("GOOGLE_API_KEY", "k2")
        with patch.object(llm_client, "_call_provider", side_effect=RuntimeError("fail")):
            with pytest.raises(RuntimeError, match="All configured providers failed"):
                llm_client.complete("s", "u")

    def test_raises_when_no_providers_configured(self):
        # conftest cleared all keys; no monkeypatch.setenv calls here
        with pytest.raises(EnvironmentError, match="No LLM provider"):
            llm_client.complete("s", "u")

    def test_raises_for_unknown_explicit_provider(self, monkeypatch):
        monkeypatch.setenv("LLM_PROVIDER", "totally_unknown")
        with pytest.raises(ValueError, match="Unknown LLM_PROVIDER"):
            llm_client.complete("s", "u")

    def test_explicit_provider_with_fallback_to_others(self, monkeypatch):
        monkeypatch.setenv("LLM_PROVIDER", "groq")
        monkeypatch.setenv("GROQ_API_KEY", "k1")
        monkeypatch.setenv("GOOGLE_API_KEY", "k2")

        calls = []

        def mock_call(provider, *args):
            calls.append(provider)
            if provider == "groq":
                raise RuntimeError("groq rate limited")
            return "google fallback"

        with patch.object(llm_client, "_call_provider", side_effect=mock_call):
            result = llm_client.complete("s", "u")

        assert result == "google fallback"
        assert calls[0] == "groq"
        assert "google" in calls
