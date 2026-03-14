"""orchestrator.py のテスト — フロー実行、レビューゲート、メッシュ通信、タイムアウト"""
from __future__ import annotations
import json
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from orgbench.orchestrator import run_single, _execute_flow, _merge_outputs, _check_review_pass
from orgbench.models import (
    TemplateConfig, ThemeConfig, FlowStep, AgentDef,
    Message, MessageType, LLMCall, RunResult,
    AuthorityType, CommunicationType, ReviewType, ModelPreset,
)


# ============================================================
# _check_review_pass のテスト
# ============================================================

class TestCheckReviewPass:
    def test_approved_english(self):
        assert _check_review_pass("The proposal is APPROVED with minor suggestions.") is True

    def test_approved_lowercase(self):
        assert _check_review_pass("approved") is True

    def test_approved_mixed_case(self):
        assert _check_review_pass("Approved") is True

    def test_approved_japanese(self):
        assert _check_review_pass("本提案を承認します。") is True

    def test_not_approved(self):
        assert _check_review_pass("修正が必要です。以下の点を改善してください。") is False

    def test_empty_string(self):
        assert _check_review_pass("") is False

    def test_partial_match_approved(self):
        """approved が含まれていれば True"""
        assert _check_review_pass("I have not approved this") is True

    def test_rejection_with_details(self):
        assert _check_review_pass("財務予測に根拠がありません。収益モデルを再検討してください。") is False


# ============================================================
# _merge_outputs のテスト
# ============================================================

class TestMergeOutputs:
    def test_basic_merge(self, make_agent_def):
        agents = {
            "ceo": make_agent_def(name="ceo", role="CEO"),
            "writer": make_agent_def(name="writer", role="Writer"),
            "cfo": make_agent_def(name="cfo", role="CFO"),
        }
        template = TemplateConfig(
            name="test", authority=None, communication=None, review=None,
            model_preset=None,
            agents=[agents["ceo"], agents["writer"], agents["cfo"]],
            flow=[],
        )
        outputs = {"ceo": "CEO出力", "writer": "Writer出力", "cfo": "CFO出力"}

        merged = _merge_outputs(outputs, agents, template)
        assert "Writer（writer）の報告" in merged
        assert "CFO（cfo）の報告" in merged
        assert "CEO（ceo）の報告" not in merged  # CEOは除外

    def test_ceo_excluded(self, make_agent_def):
        """CEOの出力はマージ対象外"""
        agents = {"ceo": make_agent_def(name="ceo", role="CEO")}
        template = TemplateConfig(
            name="test", authority=None, communication=None, review=None,
            model_preset=None, agents=[agents["ceo"]], flow=[],
        )
        outputs = {"ceo": "CEO出力"}
        merged = _merge_outputs(outputs, agents, template)
        assert merged == ""

    def test_separator(self, make_agent_def):
        """セクション間が---で区切られる"""
        agents = {
            "ceo": make_agent_def(name="ceo", role="CEO"),
            "a": make_agent_def(name="a", role="A"),
            "b": make_agent_def(name="b", role="B"),
        }
        template = TemplateConfig(
            name="test", authority=None, communication=None, review=None,
            model_preset=None, agents=[agents["ceo"], agents["a"], agents["b"]], flow=[],
        )
        outputs = {"a": "A出力", "b": "B出力"}
        merged = _merge_outputs(outputs, agents, template)
        assert "\n\n---\n\n" in merged

    def test_agent_without_output_skipped(self, make_agent_def):
        """出力のないエージェントはスキップ"""
        agents = {
            "ceo": make_agent_def(name="ceo", role="CEO"),
            "a": make_agent_def(name="a", role="A"),
        }
        template = TemplateConfig(
            name="test", authority=None, communication=None, review=None,
            model_preset=None, agents=[agents["ceo"], agents["a"]], flow=[],
        )
        outputs = {}  # 誰も出力していない
        merged = _merge_outputs(outputs, agents, template)
        assert merged == ""


# ============================================================
# run_single のテスト — 基本フロー
# ============================================================

def _make_mock_agent_act(outputs: dict[str, str]):
    """agent_actのモック: エージェント名に対応する出力を返す"""
    call_count = {}

    async def mock_act(agent_def, instruction, context, theme_id, temperature=0.7):
        name = agent_def.name
        call_count[name] = call_count.get(name, 0) + 1
        text = outputs.get(f"{name}_{call_count[name]}", outputs.get(name, f"{name}_output"))
        call_log = LLMCall(
            agent=name, model=agent_def.model,
            input_tokens=100, output_tokens=50, cost_usd=0.001, duration_ms=500,
            timestamp=datetime.now(), purpose=agent_def.role,
            prompt_summary="", response_summary=text[:200],
        )
        return text, [call_log]

    return mock_act


class TestRunSingleBasic:
    @pytest.mark.asyncio
    async def test_simple_two_agent_flow(self, simple_template, make_theme):
        """2エージェントの単純フロー"""
        theme = make_theme()
        mock_act = _make_mock_agent_act({"ceo": "CEO指示", "writer": "最終提案"})

        with patch("orgbench.orchestrator.agent_act", side_effect=mock_act):
            result = await run_single(simple_template, theme, replication=1)

        assert isinstance(result, RunResult)
        assert result.config_name == "simple_test"
        assert result.theme_id == "t_test"
        assert result.replication == 1
        assert result.output_text == "最終提案"  # 最後のフローステップの出力
        assert result.timeout is False
        assert result.error is None
        assert result.total_llm_calls == 2
        assert result.total_cost_usd == pytest.approx(0.002)
        assert result.total_duration_sec > 0

    @pytest.mark.asyncio
    async def test_messages_recorded(self, simple_template, make_theme):
        """メッセージが正しく記録される"""
        theme = make_theme()
        mock_act = _make_mock_agent_act({"ceo": "CEO指示", "writer": "提案"})

        with patch("orgbench.orchestrator.agent_act", side_effect=mock_act):
            result = await run_single(simple_template, theme, replication=1)

        # 各ステップで2メッセージ（delegate + result）× 2ステップ = 4
        assert len(result.messages) == 4
        assert result.messages[0].msg_type == MessageType.DELEGATE_TASK
        assert result.messages[1].msg_type == MessageType.TASK_RESULT

    @pytest.mark.asyncio
    async def test_first_step_receives_theme_prompt(self, simple_template, make_theme):
        """最初のステップでテーマプロンプトが渡される"""
        theme = make_theme(task_prompt="カスタムテーマプロンプト")
        received_instructions = []

        async def capture_act(agent_def, instruction, context, theme_id, temperature=0.7):
            received_instructions.append((agent_def.name, instruction))
            return "output", [LLMCall(
                agent=agent_def.name, model="m", input_tokens=0, output_tokens=0,
                cost_usd=0, duration_ms=0, timestamp=datetime.now(),
                purpose="", prompt_summary="", response_summary="",
            )]

        with patch("orgbench.orchestrator.agent_act", side_effect=capture_act):
            await run_single(simple_template, theme, replication=1)

        # 最初のステップ（CEO）がテーマプロンプトを受け取る
        assert received_instructions[0] == ("ceo", "カスタムテーマプロンプト")

    @pytest.mark.asyncio
    async def test_context_passed_between_agents(self, simple_template, make_theme):
        """エージェント間でコンテキストが渡される"""
        theme = make_theme()
        received_contexts = []

        async def capture_act(agent_def, instruction, context, theme_id, temperature=0.7):
            received_contexts.append((agent_def.name, context))
            return f"{agent_def.name}の出力", [LLMCall(
                agent=agent_def.name, model="m", input_tokens=0, output_tokens=0,
                cost_usd=0, duration_ms=0, timestamp=datetime.now(),
                purpose="", prompt_summary="", response_summary="",
            )]

        with patch("orgbench.orchestrator.agent_act", side_effect=capture_act):
            await run_single(simple_template, theme, replication=1)

        # CEO: 最初のステップなのでコンテキストは空
        assert received_contexts[0] == ("ceo", "")
        # Writer: CEOの出力がコンテキストとして渡される
        assert received_contexts[1] == ("writer", "ceoの出力")


# ============================================================
# run_single のテスト — レビューゲート
# ============================================================

class TestRunSingleReviewGate:
    @pytest.mark.asyncio
    async def test_review_approved(self, review_template, make_theme):
        """レビュー合格: 差し戻しなし"""
        theme = make_theme()
        mock_act = _make_mock_agent_act({
            "ceo_1": "指示", "writer": "ドラフト",
            "cfo": "APPROVED: 問題なし",
            "ceo_2": "最終提案",
        })

        with patch("orgbench.orchestrator.agent_act", side_effect=mock_act):
            result = await run_single(review_template, theme, replication=1)

        assert result.error is None
        # レビュー合格なので差し戻しの追加呼び出しなし
        # ceo(1) + writer(1) + cfo(1) + ceo(2) = 4
        assert result.total_llm_calls == 4

    @pytest.mark.asyncio
    async def test_review_rejected_triggers_revision(self, review_template, make_theme):
        """レビュー不合格: writerに差し戻しが発生"""
        theme = make_theme()
        call_log = []

        async def mock_act(agent_def, instruction, context, theme_id, temperature=0.7):
            call_log.append(agent_def.name)
            outputs = {
                "ceo": "指示",
                "writer": "ドラフト",
                "cfo": "修正が必要。財務根拠が不足。",  # APPROVED含まない → 不合格
            }
            text = outputs.get(agent_def.name, "修正版")
            return text, [LLMCall(
                agent=agent_def.name, model="m", input_tokens=0, output_tokens=0,
                cost_usd=0, duration_ms=0, timestamp=datetime.now(),
                purpose="", prompt_summary="", response_summary="",
            )]

        with patch("orgbench.orchestrator.agent_act", side_effect=mock_act):
            result = await run_single(review_template, theme, replication=1)

        # ceo, writer, cfo, (revision: writer), ceo → 5回
        assert "writer" in call_log
        assert call_log.count("writer") >= 2  # 初回 + 差し戻し

    @pytest.mark.asyncio
    async def test_review_承認_japanese(self, review_template, make_theme):
        """日本語「承認」でもレビュー合格"""
        theme = make_theme()
        mock_act = _make_mock_agent_act({
            "ceo_1": "指示", "writer": "ドラフト",
            "cfo": "本提案を承認します。",
            "ceo_2": "最終提案",
        })

        with patch("orgbench.orchestrator.agent_act", side_effect=mock_act):
            result = await run_single(review_template, theme, replication=1)

        assert result.total_llm_calls == 4  # 差し戻しなし


# ============================================================
# run_single のテスト — メッシュ通信
# ============================================================

class TestRunSingleMesh:
    @pytest.mark.asyncio
    async def test_mesh_injects_peer_context(self, mesh_template, make_theme):
        """メッシュ通信でピアの出力がコンテキストに注入される"""
        theme = make_theme()
        received = {}

        async def capture_act(agent_def, instruction, context, theme_id, temperature=0.7):
            received[agent_def.name] = context
            return f"{agent_def.name}出力", [LLMCall(
                agent=agent_def.name, model="m", input_tokens=0, output_tokens=0,
                cost_usd=0, duration_ms=0, timestamp=datetime.now(),
                purpose="", prompt_summary="", response_summary="",
            )]

        with patch("orgbench.orchestrator.agent_act", side_effect=capture_act):
            await run_single(mesh_template, theme, replication=1)

        # writer は researcher のピア → researcher の出力後に writerが実行される
        # writerはresearcherの出力をcontextで受け取り、さらにresearcherがピアとして出力を持つ
        writer_ctx = received.get("writer", "")
        assert "researcher出力" in writer_ctx

    @pytest.mark.asyncio
    async def test_hub_no_peer_injection(self, simple_template, make_theme):
        """Hub通信ではピアコンテキストが注入されない"""
        theme = make_theme()
        received = {}

        async def capture_act(agent_def, instruction, context, theme_id, temperature=0.7):
            received[agent_def.name] = context
            return "output", [LLMCall(
                agent=agent_def.name, model="m", input_tokens=0, output_tokens=0,
                cost_usd=0, duration_ms=0, timestamp=datetime.now(),
                purpose="", prompt_summary="", response_summary="",
            )]

        with patch("orgbench.orchestrator.agent_act", side_effect=capture_act):
            await run_single(simple_template, theme, replication=1)

        # Hub通信なので「他メンバーの知見」セクションはない
        writer_ctx = received.get("writer", "")
        assert "他メンバーの知見" not in writer_ctx


# ============================================================
# run_single のテスト — __all__ 統合
# ============================================================

class TestRunSingleAllMerge:
    @pytest.mark.asyncio
    async def test_all_merge_step(self, review_template, make_theme):
        """__all__ ステップで全エージェントの出力が統合される"""
        theme = make_theme()
        received_contexts = {}

        async def capture_act(agent_def, instruction, context, theme_id, temperature=0.7):
            received_contexts[f"{agent_def.name}_{len(received_contexts)}"] = context
            if agent_def.name == "cfo":
                return "APPROVED", [LLMCall(
                    agent=agent_def.name, model="m", input_tokens=0, output_tokens=0,
                    cost_usd=0, duration_ms=0, timestamp=datetime.now(),
                    purpose="", prompt_summary="", response_summary="",
                )]
            return f"{agent_def.name}の成果", [LLMCall(
                agent=agent_def.name, model="m", input_tokens=0, output_tokens=0,
                cost_usd=0, duration_ms=0, timestamp=datetime.now(),
                purpose="", prompt_summary="", response_summary="",
            )]

        with patch("orgbench.orchestrator.agent_act", side_effect=capture_act):
            await run_single(review_template, theme, replication=1)

        # 最後のCEOステップ(__all__)のコンテキストにwriter/cfoの出力が含まれる
        last_ceo_key = [k for k in received_contexts if k.startswith("ceo")][-1]
        last_ceo_ctx = received_contexts[last_ceo_key]
        assert "Writer" in last_ceo_ctx or "writer" in last_ceo_ctx


# ============================================================
# run_single のテスト — タイムアウト
# ============================================================

class TestRunSingleTimeout:
    @pytest.mark.asyncio
    async def test_timeout_handled(self, simple_template, make_theme):
        """タイムアウト時にRunResultにtimeout=Trueが記録される"""
        theme = make_theme()

        async def slow_act(agent_def, instruction, context, theme_id, temperature=0.7):
            await asyncio.sleep(10)  # 超長い処理
            return "never reached", []

        with patch("orgbench.orchestrator.agent_act", side_effect=slow_act):
            result = await run_single(
                simple_template, theme, replication=1, timeout_sec=0.1,
            )

        assert result.timeout is True
        assert "Timeout" in result.error

    @pytest.mark.asyncio
    async def test_error_handled(self, simple_template, make_theme):
        """例外時にRunResultにerrorが記録される"""
        theme = make_theme()

        async def error_act(agent_def, instruction, context, theme_id, temperature=0.7):
            raise ValueError("Test error")

        with patch("orgbench.orchestrator.agent_act", side_effect=error_act):
            result = await run_single(simple_template, theme, replication=1)

        assert result.timeout is False
        assert "Test error" in result.error


# ============================================================
# run_single のテスト — コスト集計
# ============================================================

class TestRunSingleCostAggregation:
    @pytest.mark.asyncio
    async def test_costs_summed(self, simple_template, make_theme):
        """全LLM呼び出しのコストが合計される"""
        theme = make_theme()
        mock_act = _make_mock_agent_act({"ceo": "指示", "writer": "提案"})

        with patch("orgbench.orchestrator.agent_act", side_effect=mock_act):
            result = await run_single(simple_template, theme, replication=1)

        assert result.total_cost_usd == pytest.approx(0.002)  # 0.001 * 2
        assert result.total_input_tokens == 200  # 100 * 2
        assert result.total_output_tokens == 100  # 50 * 2


# ============================================================
# シングルエージェントのテスト
# ============================================================

class TestRunSingleSingleAgent:
    @pytest.mark.asyncio
    async def test_single_agent_flow(self, single_agent_template, make_theme):
        """シングルエージェントのフロー"""
        theme = make_theme()
        mock_act = _make_mock_agent_act({"single": "完成した提案"})

        with patch("orgbench.orchestrator.agent_act", side_effect=mock_act):
            result = await run_single(single_agent_template, theme, replication=1)

        assert result.output_text == "完成した提案"
        assert result.total_llm_calls == 1
