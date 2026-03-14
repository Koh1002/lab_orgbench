"""tools.py のテスト — キャッシュ機構、ハッシュ一貫性、フォーマット処理"""
from __future__ import annotations
import hashlib
import json
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

from orgbench.tools import search_web, _cache_path, _format_results, CACHE_DIR


# ============================================================
# _cache_path のテスト
# ============================================================

class TestCachePath:
    def test_deterministic(self):
        """同一入力で同一パスを返す"""
        p1 = _cache_path("t01", "AI market size")
        p2 = _cache_path("t01", "AI market size")
        assert p1 == p2

    def test_different_queries_different_paths(self):
        """異なるクエリは異なるパスを返す"""
        p1 = _cache_path("t01", "query A")
        p2 = _cache_path("t01", "query B")
        assert p1 != p2

    def test_different_themes_different_paths(self):
        """異なるテーマは異なるパスを返す"""
        p1 = _cache_path("t01", "same query")
        p2 = _cache_path("t02", "same query")
        assert p1 != p2

    def test_hash_format(self):
        """ファイル名がSHA256ハッシュの先頭16文字.json"""
        p = _cache_path("t01", "test query")
        expected_hash = hashlib.sha256("test query".encode()).hexdigest()[:16]
        assert p.name == f"{expected_hash}.json"

    def test_theme_as_subdirectory(self):
        """テーマIDがサブディレクトリになる"""
        p = _cache_path("t01_ai_accounting", "test")
        assert "t01_ai_accounting" in str(p)
        assert p.parent.name == "t01_ai_accounting"

    def test_path_under_cache_dir(self):
        """キャッシュディレクトリ配下に生成される"""
        p = _cache_path("t01", "test")
        assert str(CACHE_DIR) in str(p)

    def test_unicode_query(self):
        """日本語クエリでも正常に動作"""
        p = _cache_path("t01", "中小企業 AI 経理自動化 市場規模")
        assert p.name.endswith(".json")
        assert len(p.stem) == 16  # hex 16文字

    def test_empty_query(self):
        """空クエリでもクラッシュしない"""
        p = _cache_path("t01", "")
        assert p.name.endswith(".json")


# ============================================================
# _format_results のテスト
# ============================================================

class TestFormatResults:
    def test_basic_formatting(self):
        result = {
            "answer": "AI market is growing",
            "results": [
                {"title": "Article 1", "url": "https://example.com/1", "content": "Content 1"},
                {"title": "Article 2", "url": "https://example.com/2", "content": "Content 2"},
            ],
        }
        formatted = _format_results("AI market", result)
        assert "## Web Search: AI market" in formatted
        assert "**Summary:** AI market is growing" in formatted
        assert "### Result 1: Article 1" in formatted
        assert "### Result 2: Article 2" in formatted
        assert "https://example.com/1" in formatted

    def test_no_answer(self):
        """answerがない場合もクラッシュしない"""
        result = {"results": [{"title": "T", "url": "U", "content": "C"}]}
        formatted = _format_results("test", result)
        assert "**Summary:**" not in formatted
        assert "### Result 1: T" in formatted

    def test_empty_results(self):
        """結果が空でもクラッシュしない"""
        result = {"results": []}
        formatted = _format_results("test", result)
        assert "## Web Search: test" in formatted

    def test_content_truncated_at_500(self):
        """contentは500文字に切り詰められる"""
        long_content = "A" * 1000
        result = {"results": [{"title": "T", "url": "U", "content": long_content}]}
        formatted = _format_results("test", result)
        # 500文字で切られる
        assert "A" * 500 in formatted
        assert "A" * 501 not in formatted

    def test_missing_fields(self):
        """titleやurlが欠けていてもN/Aや空文字で補完"""
        result = {"results": [{}]}
        formatted = _format_results("test", result)
        assert "N/A" in formatted

    def test_multiple_results_numbered(self):
        """結果が連番で表示される"""
        result = {"results": [
            {"title": f"T{i}", "url": f"U{i}", "content": f"C{i}"}
            for i in range(5)
        ]}
        formatted = _format_results("test", result)
        for i in range(1, 6):
            assert f"### Result {i}:" in formatted


# ============================================================
# search_web のテスト
# ============================================================

class TestSearchWeb:
    @pytest.mark.asyncio
    async def test_cache_hit(self, tmp_path):
        """キャッシュが存在する場合、APIを呼ばずキャッシュから返す"""
        with patch("orgbench.tools.CACHE_DIR", tmp_path):
            # キャッシュを事前作成
            cache = tmp_path / "t01" / "dummy.json"
            # 実際のパスを計算
            actual_path = _cache_path.__wrapped__("t01", "test query") if hasattr(_cache_path, '__wrapped__') else None
            # CACHE_DIRがpatchされているので手動で計算
            query_hash = hashlib.sha256("test query".encode()).hexdigest()[:16]
            cache = tmp_path / "t01" / f"{query_hash}.json"
            cache.parent.mkdir(parents=True, exist_ok=True)
            cache.write_text("cached result", encoding="utf-8")

            result = await search_web("test query", "t01")
            assert result == "cached result"

    @pytest.mark.asyncio
    async def test_api_call_and_cache_write(self, tmp_path):
        """キャッシュがない場合、API呼び出し後にキャッシュに書き込む"""
        with patch("orgbench.tools.CACHE_DIR", tmp_path):
            mock_client = MagicMock()
            mock_client.search = AsyncMock(return_value={
                "answer": "test answer",
                "results": [{"title": "T", "url": "U", "content": "C"}],
            })

            with patch("orgbench.tools.AsyncTavilyClient", return_value=mock_client):
                with patch.dict("os.environ", {"TAVILY_API_KEY": "test_key"}):
                    result = await search_web("new query", "t01")

            assert "## Web Search: new query" in result
            assert "test answer" in result

            # キャッシュファイルが作成されたことを確認
            query_hash = hashlib.sha256("new query".encode()).hexdigest()[:16]
            cache_file = tmp_path / "t01" / f"{query_hash}.json"
            assert cache_file.exists()
            assert cache_file.read_text(encoding="utf-8") == result

    @pytest.mark.asyncio
    async def test_cache_prevents_duplicate_api_calls(self, tmp_path):
        """2回目の同一クエリはAPI呼び出しをスキップ"""
        with patch("orgbench.tools.CACHE_DIR", tmp_path):
            mock_client = MagicMock()
            mock_client.search = AsyncMock(return_value={
                "results": [{"title": "T", "url": "U", "content": "C"}],
            })

            with patch("orgbench.tools.AsyncTavilyClient", return_value=mock_client):
                with patch.dict("os.environ", {"TAVILY_API_KEY": "test_key"}):
                    result1 = await search_web("query", "t01")
                    result2 = await search_web("query", "t01")

            assert result1 == result2
            assert mock_client.search.call_count == 1  # 1回だけ

    @pytest.mark.asyncio
    async def test_different_themes_separate_cache(self, tmp_path):
        """異なるテーマは別々のキャッシュ"""
        with patch("orgbench.tools.CACHE_DIR", tmp_path):
            mock_client = MagicMock()
            call_count = 0

            async def mock_search(**kwargs):
                nonlocal call_count
                call_count += 1
                return {"results": [{"title": f"T{call_count}", "url": "U", "content": f"C{call_count}"}]}

            mock_client.search = mock_search

            with patch("orgbench.tools.AsyncTavilyClient", return_value=mock_client):
                with patch.dict("os.environ", {"TAVILY_API_KEY": "test_key"}):
                    result1 = await search_web("same query", "t01")
                    result2 = await search_web("same query", "t02")

            assert result1 != result2
            assert call_count == 2
