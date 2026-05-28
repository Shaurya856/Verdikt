"""Shared fixtures: clear all LLM provider env vars before every test."""

import pytest

_PROVIDER_KEYS = (
    "GROQ_API_KEY",
    "NVIDIA_API_KEY",
    "OPENROUTER_API_KEY",
    "GOOGLE_API_KEY",
    "LLM_PROVIDER",
    "LLM_MODEL",
)


@pytest.fixture(autouse=True)
def clear_llm_env(monkeypatch):
    """Guarantee a clean env for every test — no real API keys leak in."""
    for key in _PROVIDER_KEYS:
        monkeypatch.delenv(key, raising=False)
