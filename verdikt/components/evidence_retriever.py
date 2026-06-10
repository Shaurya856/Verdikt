"""Evidence retrieval from Wikipedia, arXiv, and user-provided document."""

from typing import Optional

from verdikt.components.chunker import chunk_document
from verdikt.sources.arxiv import search_arxiv
from verdikt.sources.wikipedia import search_wikipedia


def get_evidence_passages(
    query: str,
    document_text: Optional[str] = None,
    use_wikipedia: bool = True,
    use_arxiv: bool = True,
    max_per_source: int = 3,
) -> list[dict]:
    """
    Retrieve evidence passages for a given query.

    Returns a list of dicts:
      {"source": "wikipedia"|"arxiv"|"document", "title": ..., "text": ..., "url": ...}
    """
    passages: list[dict] = []

    # Include chunks from the user-provided document
    if document_text:
        chunks = chunk_document(document_text, max_tokens=300)
        for chunk in chunks:
            passages.append(
                {
                    "source": "document",
                    "title": "Provided document",
                    "text": chunk.text,
                    "url": None,
                }
            )

    if use_wikipedia:
        wiki_results = search_wikipedia(query, max_results=min(max_per_source, 2))
        passages.extend(wiki_results)

    if use_arxiv:
        arxiv_results = search_arxiv(query, max_results=min(max_per_source, 2))
        passages.extend(arxiv_results)

    return passages
