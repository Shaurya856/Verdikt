"""Gemini LLM client wrapper used by all components."""

import os
import time
import warnings
from typing import Optional

# Suppress google-auth FutureWarnings about Python version
warnings.filterwarnings("ignore", category=FutureWarning, module="google")

from google import genai
from google.genai import types
from google.genai import errors as genai_errors

_MODEL = "gemini-2.0-flash"
_MAX_RETRIES = 4
_RETRY_DELAY = 15  # seconds to wait after a 429


def _make_client() -> genai.Client:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "GOOGLE_API_KEY is not set. Get a free key from https://aistudio.google.com/apikey"
        )
    return genai.Client(api_key=api_key)


_client: Optional[genai.Client] = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = _make_client()
    return _client


def complete(system: str, user_message: str, max_tokens: int = 1024) -> str:
    """
    Call Gemini with a system prompt and user message, return the text response.

    Uses gemini-2.0-flash which is free on the Google AI Studio free tier (15 RPM).
    Automatically retries up to _MAX_RETRIES times on 429 rate-limit errors.
    """
    client = _get_client()
    last_error: Optional[Exception] = None

    for attempt in range(_MAX_RETRIES):
        try:
            response = client.models.generate_content(
                model=_MODEL,
                contents=user_message,
                config=types.GenerateContentConfig(
                    system_instruction=system,
                    max_output_tokens=max_tokens,
                    temperature=0.1,
                ),
            )
            text = response.text
            if text is None:
                return ""
            return text
        except genai_errors.ClientError as e:
            if e.code == 429:
                last_error = e
                wait = _RETRY_DELAY * (attempt + 1)
                time.sleep(wait)
                continue
            raise
    raise RuntimeError(
        f"Gemini rate limit exceeded after {_MAX_RETRIES} retries. "
        "Try again in a minute, or reduce the document size."
    ) from last_error
