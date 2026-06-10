"""Wikipedia evidence retrieval — search via MediaWiki API, fetch via web_search."""

import json
import urllib.parse

from verdikt.sources.web_search import fetch_url

_WIKI_API = "https://en.wikipedia.org/w/api.php"


def search_wikipedia(query: str, max_results: int = 3) -> list[dict]:
    """
    Search Wikipedia for pages related to a query and return their text extracts.

    Returns a list of dicts: {"source": "wikipedia", "title": ..., "text": ..., "url": ...}
    """
    # Step 1: Search for relevant page titles via the JSON API
    search_params = urllib.parse.urlencode(
        {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srlimit": max_results,
            "format": "json",
            "utf8": 1,
        }
    )
    search_url = f"{_WIKI_API}?{search_params}"
    raw = fetch_url(search_url)
    if not raw:
        return []

    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return []

    titles = [hit["title"] for hit in data.get("query", {}).get("search", [])]
    if not titles:
        return []

    # Step 2: Fetch plain-text extract for each title
    results = []
    for title in titles[:max_results]:
        extract_params = urllib.parse.urlencode(
            {
                "action": "query",
                "titles": title,
                "prop": "extracts",
                "exintro": True,
                "explaintext": True,
                "format": "json",
            }
        )
        extract_url = f"{_WIKI_API}?{extract_params}"
        raw_extract = fetch_url(extract_url)
        if not raw_extract:
            continue

        try:
            pages = json.loads(raw_extract).get("query", {}).get("pages", {})
        except (json.JSONDecodeError, ValueError):
            continue

        for page in pages.values():
            extract = page.get("extract", "").strip()
            if extract:
                results.append(
                    {
                        "source": "wikipedia",
                        "title": page.get("title", title),
                        "text": extract,
                        "url": f"https://en.wikipedia.org/wiki/{urllib.parse.quote(title)}",
                    }
                )

    return results
