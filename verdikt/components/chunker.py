"""Deterministic, LLM-free sentence-level text chunker."""

import re
from dataclasses import dataclass


@dataclass
class Chunk:
    index: int
    text: str
    token_count: int  # word-based approximation


def _split_sentences(text: str) -> list[str]:
    """Split text into sentences using punctuation heuristics."""
    # Split on sentence-ending punctuation followed by whitespace
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return [s.strip() for s in sentences if s.strip()]


def _word_count(text: str) -> int:
    return len(text.split())


def chunk_document(text: str, max_tokens: int = 300) -> list[Chunk]:
    """
    Split document text into chunks of up to max_tokens words.
    Groups 1-2 sentences together, staying within the token limit.
    """
    sentences = _split_sentences(text)
    chunks: list[Chunk] = []
    i = 0
    idx = 0

    while i < len(sentences):
        current = sentences[i]

        # Try to include the next sentence if it fits
        if i + 1 < len(sentences):
            combined = current + " " + sentences[i + 1]
            if _word_count(combined) <= max_tokens:
                current = combined
                i += 1

        chunks.append(Chunk(index=idx, text=current, token_count=_word_count(current)))
        idx += 1
        i += 1

    return chunks
