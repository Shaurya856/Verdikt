"""arXiv evidence retrieval — fetch via web_search, parse Atom XML."""

import re
import urllib.parse
import xml.etree.ElementTree as ET

from verdikt.sources.web_search import fetch_url

_ARXIV_API = "https://export.arxiv.org/api/query"
_ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}


def search_arxiv(query: str, max_results: int = 3) -> list[dict]:
    """
    Search arXiv for papers related to a query and return their abstracts.

    Returns a list of dicts: {"source": "arxiv", "title": ..., "text": ..., "url": ...}
    """
    params = urllib.parse.urlencode(
        {
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": max_results,
        }
    )
    url = f"{_ARXIV_API}?{params}"
    raw = fetch_url(url)
    if not raw:
        return []

    try:
        root = ET.fromstring(raw)
    except ET.ParseError:
        return []

    results = []
    for entry in root.findall("atom:entry", _ATOM_NS):
        title_elem = entry.find("atom:title", _ATOM_NS)
        summary_elem = entry.find("atom:summary", _ATOM_NS)
        id_elem = entry.find("atom:id", _ATOM_NS)

        if title_elem is None or summary_elem is None:
            continue

        title = re.sub(r"\s+", " ", title_elem.text or "").strip()
        abstract = re.sub(r"\s+", " ", summary_elem.text or "").strip()
        url_str = (id_elem.text or "").strip()

        if abstract:
            results.append(
                {
                    "source": "arxiv",
                    "title": title,
                    "text": abstract,
                    "url": url_str,
                }
            )

    return results
