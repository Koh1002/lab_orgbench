"""llm.py のテスト — コスト計算、リトライ、empty choices、tool_calls処理"""
from __future__ import annotations
import json
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from orgbench.llm import call_llm, _calc_cost, _make_call_log, PRICING, MAX_RETRIES
from orgbench.models import LLMCall

# conftest.pyのヘルパー関数を直接定義（pytest conftest は import できないため）
from unittest.mock import MagicMock
import json as _json

def make_mock_llm_response(content="テスト出力", input_tokens=100, output_tokens=50, tool_calls=None):
    message = MagicMock()
    message.content = content
    message.tool_calls = tool_calls
    choice = MagicMock()
    choice.message = message
    usage = MagicMock()
    usage.prompt_tokens = input_tokens
    usage.completion_tokens = output_tokens
    response = MagicMock()
    response.choices = [choice]
    response.usage = usage
    return response

def make_mock_tool_call_response(query="テスト検索", tool_call_id="call_123"):
    tc = MagicMock()
    tc.id = tool_call_id
    tc.function.name = "web_search"
    tc.function.arguments = _json.dumps({"query": query})
    return make_mock_llm_response(content=None, tool_calls=[tc])

def make_empty_choices_response():
    response = MagicMock()
    response.choices = []
    return response


# ============================================================
# _calc_cost のテスト
# ============================================================

class TestCalcCost:
    def test_haiku_pricing(self):
        cost = _calc_cost("claude-haiku-4-5-20251001", 1_000_000, 1_000_000)
        assert cost == pytest.approx(1.0 + 5.0)

    def test_gpt4o_mini_pricing(self):
        cost = _calc_cost("gpt-4o-mini", 1_000_000, 1_000_000)
        assert cost == pytest.approx(0.15 + 0.60)

    def test_gemini_flash_pricing(self):
        cost = _calc_cost("gemini/gemini-2.5-flash", 1_000_000, 1_000_000)
        assert cost == pytest.approx(0.15 + 0.60)

    def test_zero_tokens(self):
        cost = _calc_cost("gpt-4o-mini", 0, 0)
        assert cost == 0.0

    def test_unknown_model_returns_zero(self):
        cost = _calc_cost("unknown-model-xyz", 1000, 1000)
        assert cost == 0.0

    def test_typical_run_cost(self):
        """典型的な1エージェント呼び出しのコスト（~1000入力、~500出力トークン）"""
        cost = _calc_cost("gpt-4o-mini", 1000, 500)
        expected = (1000 * 0.15 + 500 * 0.60) / 1_000_000
        assert cost == pytest.approx(expected)

    def test_haiku_is_more_expensive_than_gpt4o_mini(self):
        """Haiku > GPT-4o-mini の価格関係"""
        haiku_cost = _calc_cost("claude-haiku-4-5-20251001", 1000, 1000)
        gpt_cost = _calc_cost("gpt-4o-mini", 1000, 1000)
        assert haiku_cost > gpt_cost

    def test_partial_model_name_match(self):
        """モデル名の部分一致でも正しく計算"""
        cost = _calc_cost("some-prefix-gpt-4o-mini-suffix", 1_000_000, 0)
        assert cost == pytest.approx(0.15)

    def test_all_pricing_entries_have_two_values(self):
        """PRICING辞書の全エントリが(input, output)の2値タプル"""
        for model, prices in PRICING.items():
            assert len(prices) == 2
            assert all(isinstance(p, (int, float)) for p in prices)
            assert all(p >= 0 for p in prices)


# ============================================================
# _make_call_log のテスト
# ============================================================

class TestMakeCallLog:
    def test_basic(self):
        log = _make_call_log("ceo", "gpt-4o-mini", 100, 50, 0.001, 500, "test", "prompt", "resp")
        assert isinstance(log, LLMCall)
        assert log.agent == "ceo"
        assert log.model == "gpt-4o-mini"
        assert log.input_tokens == 100
        assert log.output_tokens == 50
        assert log.cost_usd == 0.001
        assert log.duration_ms == 500
        assert log.purpose == "test"
        assert isinstance(log.timestamp, datetime)

    def test_prompt_summary_stored(self):
        log = _make_call_log("a", "m", 0, 0, 0, 0, "p", "long prompt text", "response text")
        assert log.prompt_summary == "long prompt text"
        assert log.response_summary == "response text"


# ============================================================
# call_llm のテスト
# ============================================================

class TestCallLLM:
    @pytest.mark.asyncio
    async def test_basic_call(self):
        mock_response = make_mock_llm_response(content="テスト出力", input_tokens=100, output_tokens=50)
        with patch("orgbench.llm.litellm.acompletion", new_callable=AsyncMock, return_value=mock_response):
            text, call_log = await call_llm(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "テスト"}],
                agent_name="test",
                purpose="unit_test",
            )
        assert text == "テスト出力"
        assert call_log.agent == "test"
        assert call_log.input_tokens == 100
        assert call_log.output_tokens == 50
        assert call_log.purpose == "unit_test"

    @pytest.mark.asyncio
    async def test_cost_tracked(self):
        mock_response = make_mock_llm_response(input_tokens=1000, output_tokens=500)
        with patch("orgbench.llm.litellm.acompletion", new_callable=AsyncMock, return_value=mock_response):
            _, call_log = await call_llm(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "test"}],
            )
        expected = (1000 * 0.15 + 500 * 0.60) / 1_000_000
        assert call_log.cost_usd == pytest.approx(expected)

    @pytest.mark.asyncio
    async def test_empty_choices_retry(self):
        """Gemini empty choices → リトライ → 最終的に空文字列を返す"""
        empty = make_empty_choices_response()
        with patch("orgbench.llm.litellm.acompletion", new_callable=AsyncMock, return_value=empty):
            with patch("orgbench.llm.asyncio.sleep", new_callable=AsyncMock):
                text, call_log = await call_llm(
                    model="gemini/gemini-2.5-flash",
                    messages=[{"role": "user", "content": "test"}],
                )
        assert text == ""
        assert call_log.input_tokens == 0

    @pytest.mark.asyncio
    async def test_empty_choices_then_success(self):
        """初回empty → 2回目成功"""
        empty = make_empty_choices_response()
        success = make_mock_llm_response(content="成功")
        mock_acomp = AsyncMock(side_effect=[empty, success])
        with patch("orgbench.llm.litellm.acompletion", mock_acomp):
            with patch("orgbench.llm.asyncio.sleep", new_callable=AsyncMock):
                text, _ = await call_llm(
                    model="gemini/gemini-2.5-flash",
                    messages=[{"role": "user", "content": "test"}],
                )
        assert text == "成功"
        assert mock_acomp.call_count == 2

    @pytest.mark.asyncio
    async def test_tool_calls_response(self):
        """tool_calls付きレスポンスがJSON形式で返る"""
        mock_response = make_mock_tool_call_response(query="AI market size")
        with patch("orgbench.llm.litellm.acompletion", new_callable=AsyncMock, return_value=mock_response):
            text, call_log = await call_llm(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "search"}],
                tools=[{"type": "function", "function": {"name": "web_search"}}],
            )
        parsed = json.loads(text)
        assert isinstance(parsed, list)
        assert parsed[0]["name"] == "web_search"
        assert parsed[0]["arguments"]["query"] == "AI market size"
        assert call_log.metadata.get("tool_calls") is True

    @pytest.mark.asyncio
    async def test_general_exception_retry(self):
        """一般例外 → リトライ → 最終的にRuntimeError"""
        mock_acomp = AsyncMock(side_effect=RuntimeError("connection error"))
        with patch("orgbench.llm.litellm.acompletion", mock_acomp):
            with patch("orgbench.llm.asyncio.sleep", new_callable=AsyncMock):
                with pytest.raises(RuntimeError, match="LLM call failed"):
                    await call_llm(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": "test"}],
                    )
        assert mock_acomp.call_count == MAX_RETRIES

    @pytest.mark.asyncio
    async def test_rate_limit_retry(self):
        """RateLimitError → リトライ → 成功"""
        import litellm
        rate_err = litellm.RateLimitError(
            message="rate limited", model="gpt-4o-mini", llm_provider="openai"
        )
        success = make_mock_llm_response(content="recovered")
        mock_acomp = AsyncMock(side_effect=[rate_err, success])
        with patch("orgbench.llm.litellm.acompletion", mock_acomp):
            with patch("orgbench.llm.asyncio.sleep", new_callable=AsyncMock):
                text, _ = await call_llm(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": "test"}],
                )
        assert text == "recovered"

    @pytest.mark.asyncio
    async def test_tools_passed_to_litellm(self):
        """toolsパラメータがlitellmに正しく渡される"""
        mock_response = make_mock_llm_response()
        mock_acomp = AsyncMock(return_value=mock_response)
        tools = [{"type": "function", "function": {"name": "test"}}]
        with patch("orgbench.llm.litellm.acompletion", mock_acomp):
            await call_llm(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "test"}],
                tools=tools,
            )
        call_kwargs = mock_acomp.call_args.kwargs
        assert call_kwargs["tools"] == tools

    @pytest.mark.asyncio
    async def test_no_tools_not_passed(self):
        """tools=None の場合、kwargsにtoolsが含まれない"""
        mock_response = make_mock_llm_response()
        mock_acomp = AsyncMock(return_value=mock_response)
        with patch("orgbench.llm.litellm.acompletion", mock_acomp):
            await call_llm(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "test"}],
            )
        call_kwargs = mock_acomp.call_args.kwargs
        assert "tools" not in call_kwargs

    @pytest.mark.asyncio
    async def test_prompt_summary_truncated(self):
        """プロンプトサマリーが200文字に切り詰められる"""
        long_content = "x" * 500
        mock_response = make_mock_llm_response()
        with patch("orgbench.llm.litellm.acompletion", new_callable=AsyncMock, return_value=mock_response):
            _, call_log = await call_llm(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": long_content}],
            )
        assert len(call_log.prompt_summary) == 200

    @pytest.mark.asyncio
    async def test_none_content_handled(self):
        """message.content が None の場合、空文字列になる"""
        mock_response = make_mock_llm_response(content=None)
        mock_response.choices[0].message.content = None
        mock_response.choices[0].message.tool_calls = None
        with patch("orgbench.llm.litellm.acompletion", new_callable=AsyncMock, return_value=mock_response):
            text, _ = await call_llm(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "test"}],
            )
        assert text == ""

    @pytest.mark.asyncio
    async def test_duration_tracked(self):
        """duration_ms が正の値で記録される"""
        mock_response = make_mock_llm_response()
        with patch("orgbench.llm.litellm.acompletion", new_callable=AsyncMock, return_value=mock_response):
            _, call_log = await call_llm(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "test"}],
            )
        assert call_log.duration_ms >= 0

    @pytest.mark.asyncio
    async def test_no_usage_defaults_to_zero(self):
        """usage が None の場合、トークン数は0"""
        mock_response = make_mock_llm_response()
        mock_response.usage = None
        with patch("orgbench.llm.litellm.acompletion", new_callable=AsyncMock, return_value=mock_response):
            _, call_log = await call_llm(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "test"}],
            )
        assert call_log.input_tokens == 0
        assert call_log.output_tokens == 0
