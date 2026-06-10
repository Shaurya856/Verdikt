"""
Web content fetching via MCP (mcp-server-fetch) using mcp-use.

Requires Python 3.11+ and mcp-use installed:
    pip install mcp-use
    brew install uv   # provides 'uvx' to run mcp-server-fetch

Until then, falls back to plain requests.
"""

import sys

# mcp-use requires Python 3.11+
_MCP_AVAILABLE = sys.version_info >= (3, 11)

if _MCP_AVAILABLE:
    try:
        import asyncio
        from mcp_use import MCPClient

        _MCP_CONFIG = {
            "mcpServers": {
                "fetch": {
                    "command": "uvx",
                    "args": ["mcp-server-fetch"],
                }
            }
        }

        async def _fetch_url_async(url: str) -> str:
            """Fetch a URL via mcp-server-fetch MCP tool."""
            client = MCPClient.from_dict(_MCP_CONFIG)
            session = await client.create_session("fetch")
            try:
                result = await session.connector.call_tool("fetch", {"url": url})
                if isinstance(result, list):
                    return "\n".join(
                        item.text for item in result if hasattr(item, "text")
                    )
                return str(result)
            finally:
                await client.close_all_sessions()

        def fetch_url(url: str) -> str:
            """Fetch a URL using the MCP fetch server (Python 3.11+ / mcp-use)."""
            return asyncio.run(_fetch_url_async(url))

    except ImportError:
        _MCP_AVAILABLE = False

if not _MCP_AVAILABLE:
    import requests

    _HEADERS = {"User-Agent": "verdikt/1.0 (educational project)"}

    def fetch_url(url: str) -> str:
        """Fetch a URL using plain requests (fallback for Python < 3.11)."""
        try:
            resp = requests.get(url, headers=_HEADERS, timeout=10)
            resp.raise_for_status()
            return resp.text
        except requests.RequestException:
            return ""
