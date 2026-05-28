"""Multi-provider LLM client with automatic fallback."""

import logging
import os
import time
from typing import Optional

from openai import OpenAI, RateLimitError, AuthenticationError, APIError

logger = logging.getLogger(__name__)

_MAX_RETRIES = 4
_RETRY_DELAY = 15  # seconds between retries on rate limit

# Registry of supported providers. All expose an OpenAI-compatible chat endpoint.
PROVIDERS: dict[str, dict] = {
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "env_key": "GROQ_API_KEY",
        "default_model": "llama-3.3-70b-versatile",
        "label": "Groq",
    },
    "nvidia": {
        "base_url": "https://integrate.api.nvidia.com/v1",
        "env_key": "NVIDIA_API_KEY",
        "default_model": "meta/llama-3.3-70b-instruct",
        "label": "NVIDIA NIM",
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "env_key": "OPENROUTER_API_KEY",
        "default_model": "meta-llama/llama-3.3-70b-instruct:free",
        "label": "OpenRouter",
    },
    "google": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "env_key": "GOOGLE_API_KEY",
        "default_model": "gemini-2.5-flash",
        "label": "Google Gemini",
    },
}

# Auto-detection priority when LLM_PROVIDER is not set
_PROVIDER_PRIORITY = ["groq", "nvidia", "openrouter", "google"]


def available_providers() -> list[str]:
    """Return provider names that have an API key present in the environment."""
    return [p for p in _PROVIDER_PRIORITY if os.getenv(PROVIDERS[p]["env_key"])]


def _build_client(provider: str) -> tuple[OpenAI, str]:
    config = PROVIDERS[provider]
    api_key = os.getenv(config["env_key"])
    if not api_key:
        raise EnvironmentError(
            f"{config['env_key']} is not set. Required for provider '{provider}'."
        )
    model = os.getenv("LLM_MODEL") or config["default_model"]
    return OpenAI(api_key=api_key, base_url=config["base_url"]), model


def _call_provider(provider: str, system: str, user_message: str, max_tokens: int) -> str:
    client, model = _build_client(provider)
    last_error: Optional[Exception] = None

    for attempt in range(_MAX_RETRIES):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_message},
                ],
                max_tokens=max_tokens,
                temperature=0.1,
            )
            return response.choices[0].message.content or ""
        except RateLimitError as e:
            last_error = e
            wait = _RETRY_DELAY * (attempt + 1)
            logger.warning(
                "[%s] Rate limited (attempt %d/%d), retrying in %ds…",
                provider, attempt + 1, _MAX_RETRIES, wait,
            )
            time.sleep(wait)
        except (AuthenticationError, APIError):
            raise

    raise RuntimeError(
        f"[{provider}] Rate limit exceeded after {_MAX_RETRIES} retries. "
        "Try again shortly, or switch to another provider."
    ) from last_error


def complete(system: str, user_message: str, max_tokens: int = 1024) -> str:
    """
    Send a system + user prompt to an LLM and return the text response.

    Provider selection order:
    1. LLM_PROVIDER env var (explicit choice)
    2. Auto-detect from whichever API keys are present (groq → nvidia → openrouter → google)

    On rate-limit exhaustion or transient failure, falls back to the next
    available provider automatically.  LLM_MODEL overrides the default model
    for the selected provider.
    """
    explicit = os.getenv("LLM_PROVIDER", "").lower().strip()

    if explicit:
        if explicit not in PROVIDERS:
            raise ValueError(
                f"Unknown LLM_PROVIDER '{explicit}'. "
                f"Valid options: {', '.join(PROVIDERS)}"
            )
        # Preferred provider first, then others as fallback
        providers_to_try = [explicit] + [p for p in available_providers() if p != explicit]
    else:
        providers_to_try = available_providers()

    if not providers_to_try:
        raise EnvironmentError(
            "No LLM provider API key is configured. Set at least one of: "
            + ", ".join(PROVIDERS[p]["env_key"] for p in _PROVIDER_PRIORITY)
            + "\nSee .env.example for details."
        )

    last_error: Optional[Exception] = None
    for provider in providers_to_try:
        try:
            result = _call_provider(provider, system, user_message, max_tokens)
            if len(providers_to_try) > 1 and provider != providers_to_try[0]:
                logger.info("Succeeded using fallback provider '%s'.", provider)
            return result
        except EnvironmentError:
            continue  # Key missing for this provider — skip silently
        except RuntimeError as e:
            logger.warning("Provider '%s' exhausted, trying next. (%s)", provider, e)
            last_error = e
        except Exception as e:  # noqa: BLE001
            logger.warning("Provider '%s' failed: %s — trying next.", provider, e)
            last_error = e

    raise RuntimeError(
        f"All configured providers failed. Last error: {last_error}"
    ) from last_error
