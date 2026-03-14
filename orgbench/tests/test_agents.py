"""agents.py のテスト — エージェント行動、ツール使用、メッセージ構築"""
from __future__ import annotations
import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from orgbench.agents import agent_act, _build_user_message, _search_tool_schema, _act_with_search
from orgbench.models import AgentDef, LLMCall


# ============================================================
# _build_user_message のテスト
# ============================================================

class TestBuildUserMessage:
    def test_instruction_only(self):
        msg = _build_user_message("テスト指示", "")
        assert "## 指示\n\nテスト指示" in msg
        assert "## これまでの情報" not in msg
        assert "## 出力形式" in msg

    def test_with_context(self):
        msg = _build_user_message("指示", "コンテキスト内容")
        assert "## これまでの情報\n\nコンテキスト内容" in msg
        assert "## 指示\n\n指示" in msg

    def test_output_format_always_present(self):
        msg = _build_user_message("x", "")
        assert "Markdown形式で回答してください" in msg

    def test_context_before_instruction(self):
        """コンテキストは指示の前に配置される"""
        msg = _build_user_message("指示", "コンテキスト")
        ctx_pos = msg.index("これまでの情報")
        inst_pos = msg.index("指示")
        assert ctx_pos < inst_pos

    def test_empty_context_no_section(self):
        """空文字列のコンテキストではセクションが生成されない"""
        msg = _build_user_message("指示", "")
        assert "これまでの情報" not in msg

    def test_long_context_not_truncated(self):
        """長いコンテキストは切り詰められない（truncationはorchestrator側）"""
        long_ctx = "x" * 10000
        msg = _build_user_message("指示", long_ctx)
        assert long_ctx in msg


# ============================================================
# _search_tool_schema のテスト
# ============================================================

class TestSearchToolSchema:
    def test_schema_structure(self):
        schema = _search_tool_schema()
        assert schema["type"] == "function"
        assert schema["function"]["name"] == "web_search"
        assert "parameters" in schema["function"]
        params = schema["function"]["parameters"]
        assert params["type"] == "object"
        assert "query" in params["properties"]
        assert params["required"] == ["query"]


# ============================================================
# agent_act のテスト（ツールなし）
# ============================================================

class TestAgentActNoTools:
    @pytest.mark.asyncio
    async def test_basic_agent_act(self, make_agent_def):
        """ツールなしエージェントの基本動作"""
        from unittest.mock import MagicMock
        agent_def = make_agent_def(name="writer", tools=[])

        with patch("orgbench.agents.call_llm", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = ("ビジネス提案ドラフト", LLMCall(
                agent="writer", model="gpt-4o-mini", input_tokens=100, output_tokens=50,
                cost_usd=0.001, duration_ms=500, timestamp=MagicMock(),
                purpose="Writer", prompt_summary="", response_summary="",
            ))
            output, calls = await agent_act(
                agent_def=agent_def,
                instruction="提案を書け",
                context="調査結果...",
                theme_id="t01",
            )

        assert output == "ビジネス提案ドラフト"
        assert len(calls) == 1
        assert calls[0].agent == "writer"

    @pytest.mark.asyncio
    async def test_system_prompt_passed(self, make_agent_def):
        """system_promptがLLMに渡される"""
        agent_def = make_agent_def(system_prompt="あなたはCFOです。")

        with patch("orgbench.agents.call_llm", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = ("output", LLMCall(
                agent="test", model="m", input_tokens=0, output_tokens=0,
                cost_usd=0, duration_ms=0, timestamp=MagicMock(),
                purpose="", prompt_summary="", response_summary="",
            ))
            await agent_act(agent_def, "指示", "", "t01")

        call_args = mock_call.call_args
        messages = call_args.kwargs["messages"]
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "あなたはCFOです。"

    @pytest.mark.asyncio
    async def test_model_from_agent_def(self, make_agent_def):
        """agent_defのモデルがcall_llmに渡される"""
        agent_def = make_agent_def(model="claude-haiku-4-5-20251001")

        with patch("orgbench.agents.call_llm", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = ("out", LLMCall(
                agent="test", model="claude-haiku-4-5-20251001", input_tokens=0, output_tokens=0,
                cost_usd=0, duration_ms=0, timestamp=MagicMock(),
                purpose="", prompt_summary="", response_summary="",
            ))
            await agent_act(agent_def, "指示", "", "t01")

        assert mock_call.call_args.kwargs["model"] == "claude-haiku-4-5-20251001"


# ============================================================
# agent_act のテスト（ツールあり）
# ============================================================

class TestAgentActWithTools:
    @pytest.mark.asyncio
    async def test_tool_use_flow(self, make_agent_def):
        """ツール使用: LLM→tool_call→search→LLM→final output"""
        agent_def = make_agent_def(name="researcher", tools=["web_search"],
                                    model="gemini/gemini-2.5-flash")

        # 1回目: tool_calls返す、2回目: テキスト返す
        tool_call_log = LLMCall(
            agent="researcher", model="gemini/gemini-2.5-flash",
            input_tokens=100, output_tokens=50, cost_usd=0.001, duration_ms=500,
            timestamp=MagicMock(), purpose="Researcher_round0",
            prompt_summary="", response_summary="",
            metadata={"tool_calls": True},
        )
        final_log = LLMCall(
            agent="researcher", model="gemini/gemini-2.5-flash",
            input_tokens=200, output_tokens=100, cost_usd=0.002, duration_ms=800,
            timestamp=MagicMock(), purpose="Researcher_round1",
            prompt_summary="", response_summary="",
            metadata={},
        )

        tool_calls_json = json.dumps([{
            "id": "call_1",
            "name": "web_search",
            "arguments": {"query": "AI market size"},
        }])

        call_count = 0
        async def mock_call_llm(**kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return (tool_calls_json, tool_call_log)
            else:
                return ("調査結果レポート", final_log)

        with patch("orgbench.agents.call_llm", side_effect=mock_call_llm):
            with patch("orgbench.agents.search_web", new_callable=AsyncMock, return_value="検索結果"):
                output, calls = await agent_act(
                    agent_def=agent_def,
                    instruction="市場調査を実施",
                    context="",
                    theme_id="t01",
                )

        assert output == "調査結果レポート"
        assert len(calls) == 2
        assert calls[0].metadata.get("tool_calls") is True
        assert calls[1].metadata == {}

    @pytest.mark.asyncio
    async def test_no_tool_call_returns_immediately(self, make_agent_def):
        """ツール付きエージェントでもtool_callsがなければ即座に返る"""
        agent_def = make_agent_def(name="researcher", tools=["web_search"])
        direct_log = LLMCall(
            agent="researcher", model="m", input_tokens=0, output_tokens=0,
            cost_usd=0, duration_ms=0, timestamp=MagicMock(),
            purpose="", prompt_summary="", response_summary="",
            metadata={},  # tool_callsなし
        )

        with patch("orgbench.agents.call_llm", new_callable=AsyncMock,
                    return_value=("直接回答", direct_log)):
            output, calls = await agent_act(agent_def, "指示", "", "t01")

        assert output == "直接回答"
        assert len(calls) == 1

    @pytest.mark.asyncio
    async def test_max_3_rounds(self, make_agent_def):
        """最大3ラウンドでツール使用が打ち切られる"""
        agent_def = make_agent_def(name="researcher", tools=["web_search"])

        tool_log = LLMCall(
            agent="researcher", model="m", input_tokens=0, output_tokens=0,
            cost_usd=0, duration_ms=0, timestamp=MagicMock(),
            purpose="", prompt_summary="", response_summary="",
            metadata={"tool_calls": True},
        )

        tool_json = json.dumps([{"id": "c", "name": "web_search", "arguments": {"query": "q"}}])

        call_idx = 0
        async def mock_llm(**kwargs):
            nonlocal call_idx
            call_idx += 1
            # 常にtool_callsを返す（3ラウンド目はtools=Noneなので返さないはずだが、テスト用）
            if call_idx <= 2:
                return (tool_json, LLMCall(
                    agent="researcher", model="m", input_tokens=0, output_tokens=0,
                    cost_usd=0, duration_ms=0, timestamp=MagicMock(),
                    purpose="", prompt_summary="", response_summary="",
                    metadata={"tool_calls": True},
                ))
            else:
                return ("最終出力", LLMCall(
                    agent="researcher", model="m", input_tokens=0, output_tokens=0,
                    cost_usd=0, duration_ms=0, timestamp=MagicMock(),
                    purpose="", prompt_summary="", response_summary="",
                    metadata={},
                ))

        with patch("orgbench.agents.call_llm", side_effect=mock_llm):
            with patch("orgbench.agents.search_web", new_callable=AsyncMock, return_value="result"):
                output, calls = await agent_act(agent_def, "指示", "", "t01")

        assert len(calls) == 3  # 最大3ラウンド


# ============================================================
# ツール使用の境界条件
# ============================================================

class TestAgentToolEdgeCases:
    @pytest.mark.asyncio
    async def test_search_called_with_theme_id(self, make_agent_def):
        """search_webにtheme_idが正しく渡される"""
        agent_def = make_agent_def(name="researcher", tools=["web_search"])

        tool_log = LLMCall(
            agent="researcher", model="m", input_tokens=0, output_tokens=0,
            cost_usd=0, duration_ms=0, timestamp=MagicMock(),
            purpose="", prompt_summary="", response_summary="",
            metadata={"tool_calls": True},
        )
        final_log = LLMCall(
            agent="researcher", model="m", input_tokens=0, output_tokens=0,
            cost_usd=0, duration_ms=0, timestamp=MagicMock(),
            purpose="", prompt_summary="", response_summary="", metadata={},
        )

        tool_json = json.dumps([{"id": "c", "name": "web_search", "arguments": {"query": "test"}}])
        call_count = 0
        async def mock_llm(**kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return (tool_json, tool_log)
            return ("output", final_log)

        mock_search = AsyncMock(return_value="cached")

        with patch("orgbench.agents.call_llm", side_effect=mock_llm):
            with patch("orgbench.agents.search_web", mock_search):
                await agent_act(agent_def, "指示", "", "t05_insurance")

        mock_search.assert_called_once_with(query="test", theme_id="t05_insurance")
