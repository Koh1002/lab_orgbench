"""Web検索ツール（Tavily API + テーマ単位キャッシュ）"""
from __future__ import annotations
import json
import hashlib
from pathlib import Path
from tavily import AsyncTavilyClient
import os

CACHE_DIR = Path("results/cache")


async def search_web(
    query: str,
    theme_id: str,
    max_results: int = 5,
) -> str:
    """
    Tavily APIで検索。同一(theme_id, query)は初回のみAPI呼び出し、
    以降はキャッシュから返す。
    """
    cache_path = _cache_path(theme_id, query)

    if cache_path.exists():
        return cache_path.read_text(encoding="utf-8")

    client = AsyncTavilyClient(api_key=os.environ["TAVILY_API_KEY"])
    result = await client.search(query=query, max_results=max_results)

    # 構造化して保存
    formatted = _format_results(query, result)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(formatted, encoding="utf-8")

    return formatted


def _cache_path(theme_id: str, query: str) -> Path:
    query_hash = hashlib.sha256(query.encode()).hexdigest()[:16]
    return CACHE_DIR / theme_id / f"{query_hash}.json"


def _format_results(query: str, result: dict) -> str:
    lines = [f"## Web Search: {query}\n"]
    if result.get("answer"):
        lines.append(f"**Summary:** {result['answer']}\n")
    for i, r in enumerate(result.get("results", []), 1):
        lines.append(f"### Result {i}: {r.get('title', 'N/A')}")
        lines.append(f"URL: {r.get('url', '')}")
        lines.append(f"{r.get('content', '')[:500]}\n")
    return "\n".join(lines)
