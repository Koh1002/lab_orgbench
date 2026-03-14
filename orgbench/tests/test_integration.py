"""統合テスト — モック LLM でのエンドツーエンドフロー検証"""
from __future__ import annotations
import json
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
from pathlib import Path

from orgbench.orchestrator import run_single
from orgbench.runner import _save_result, _meta_to_stub, _save_scores
from orgbench.judge import judge_batch
from orgbench.analysis import manipulation_check, estimate_effect_sizes
from orgbench.models import (
    AgentDef, FlowStep, TemplateConfig, ThemeConfig,
    RunResult, JudgeScore, LLMCall, Message, MessageType,
    AuthorityType, CommunicationType, ReviewType, ModelPreset,
)


# ============================================================
# ヘルパー
# ============================================================

def _make_deterministic_agent_act(response_map: dict[str, str]):
    """エージェント名 → 固定レスポンスの決定論的モック"""
    call_history = []

    async def mock_act(agent_def, instruction, context, theme_id, temperature=0.7):
        call_history.append({
            "agent": agent_def.name,
            "instruction": instruction[:100],
            "context_length": len(context),
        })
        text = response_map.get(agent_def.name, f"output_from_{agent_def.name}")
        call_log = LLMCall(
            agent=agent_def.name, model=agent_def.model,
            input_tokens=150, output_tokens=80,
            cost_usd=0.001, duration_ms=300,
            timestamp=datetime.now(), purpose=agent_def.role,
            prompt_summary=instruction[:200], response_summary=text[:200],
        )
        return text, [call_log]

    return mock_act, call_history


def _build_full_template():
    """6エージェント・フルフロー(Deep+Hub+Balanced+Hetero)テンプレート"""
    agents = [
        AgentDef(name="ceo", role="CEO", model="claude-haiku-4-5-20251001",
                 system_prompt="CEOプロンプト", manages=["tl"]),
        AgentDef(name="tl", role="TL", model="gpt-4o-mini",
                 system_prompt="TLプロンプト", reports_to=["ceo"], manages=["researcher", "writer"]),
        AgentDef(name="researcher", role="Researcher", model="gemini/gemini-2.5-flash",
                 system_prompt="Researcherプロンプト", reports_to=["tl"], tools=["web_search"]),
        AgentDef(name="writer", role="Writer", model="gpt-4o-mini",
                 system_prompt="Writerプロンプト", reports_to=["tl"]),
        AgentDef(name="cfo", role="CFO", model="gpt-4o-mini",
                 system_prompt="CFOプロンプト", reports_to=["ceo"]),
        AgentDef(name="cdo", role="CDO", model="gpt-4o-mini",
                 system_prompt="CDOプロンプト", reports_to=["ceo"]),
    ]
    flow = [
        FlowStep(agent="ceo", input_from=None, action="テーマ分析", output_to="tl"),
        FlowStep(agent="tl", input_from="ceo", action="タスク分解", output_to="researcher"),
        FlowStep(agent="researcher", input_from="tl", action="市場調査", output_to="writer"),
        FlowStep(agent="writer", input_from="researcher", action="ドラフト作成", output_to="cfo"),
        FlowStep(agent="cfo", input_from="writer", action="財務レビュー", output_to="writer", gate="review_gate"),
        FlowStep(agent="cdo", input_from="writer", action="技術レビュー", output_to="writer", gate="review_gate"),
        FlowStep(agent="ceo", input_from="__all__", action="最終統合", output_to=None),
    ]
    return TemplateConfig(
        name="full_test",
        authority=AuthorityType.DEEP_HIERARCHY,
        communication=CommunicationType.HUB_AND_SPOKE,
        review=ReviewType.BALANCED,
        model_preset=ModelPreset.HETEROGENEOUS,
        agents=agents, flow=flow, max_review_rounds=1,
    )


def _build_theme():
    return ThemeConfig(
        id="t_integ", title="統合テスト用テーマ",
        domain="Test", uncertainty_group="medium",
        task_prompt="テスト用ビジネス提案を作成してください。具体的な数値を含めること。",
    )


# ============================================================
# E2E: フルフロー（レビュー合格パス）
# ============================================================

class TestE2EApprovedPath:
    @pytest.mark.asyncio
    async def test_full_flow_approved(self):
        """6エージェント・フルフロー、レビュー全合格"""
        template = _build_full_template()
        theme = _build_theme()

        responses = {
            "ceo": "## CEO指示\n市場分析と技術分析を重点的に",
            "tl": "## TL分解\n1. 市場調査\n2. 技術スタック分析",
            "researcher": "## 調査結果\n市場規模: 500億円\n主要競合: A社, B社",
            "writer": "# ビジネス提案\n## エグゼクティブサマリー\nAI活用提案",
            "cfo": "APPROVED: 財務面は妥当。収益モデルが明確。",
            "cdo": "APPROVED: 技術スタックは適切。スケーラビリティも問題なし。",
        }
        mock_act, history = _make_deterministic_agent_act(responses)

        with patch("orgbench.orchestrator.agent_act", side_effect=mock_act):
            result = await run_single(template, theme, replication=1)

        # 基本検証
        assert result.config_name == "full_test"
        assert result.theme_id == "t_integ"
        assert result.error is None
        assert result.timeout is False

        # フルフロー: 7ステップ（レビュー合格なので差し戻しなし）
        assert result.total_llm_calls == 7

        # メッセージ: 各ステップ2メッセージ × 7 = 14
        assert len(result.messages) == 14

        # コスト集計
        assert result.total_cost_usd == pytest.approx(0.007)  # 0.001 × 7

        # 最終出力はCEOの統合ステップから
        # 最後のCEO呼び出しでは__all__なので、outputsの"ceo"が最終
        assert len(result.output_text) > 0

        # 呼び出し順序の検証
        agent_order = [h["agent"] for h in history]
        assert agent_order == ["ceo", "tl", "researcher", "writer", "cfo", "cdo", "ceo"]

    @pytest.mark.asyncio
    async def test_first_step_gets_theme_prompt(self):
        """最初のCEOがテーマプロンプトを受け取る"""
        template = _build_full_template()
        theme = _build_theme()

        responses = {
            "ceo": "指示", "tl": "分解", "researcher": "調査",
            "writer": "提案", "cfo": "APPROVED", "cdo": "APPROVED",
        }
        mock_act, history = _make_deterministic_agent_act(responses)

        with patch("orgbench.orchestrator.agent_act", side_effect=mock_act):
            await run_single(template, theme, replication=1)

        first_call = history[0]
        assert first_call["agent"] == "ceo"
        assert "テスト用ビジネス提案" in first_call["instruction"]


# ============================================================
# E2E: フルフロー（レビュー差し戻しパス）
# ============================================================

class TestE2ERejectedPath:
    @pytest.mark.asyncio
    async def test_cfo_rejection_triggers_writer_revision(self):
        """CFOが不合格 → Writerに差し戻し"""
        template = _build_full_template()
        theme = _build_theme()

        call_count = {"writer": 0, "ceo": 0}

        async def mock_act(agent_def, instruction, context, theme_id, temperature=0.7):
            name = agent_def.name
            if name in call_count:
                call_count[name] += 1

            responses = {
                "ceo": "指示",
                "tl": "分解",
                "researcher": "調査結果",
                "cfo": "修正が必要: 損益分岐点の根拠が不明",  # 不合格
                "cdo": "APPROVED",
            }
            if name == "writer":
                text = f"ドラフトv{call_count['writer']}"
            else:
                text = responses.get(name, "output")

            return text, [LLMCall(
                agent=name, model="m", input_tokens=100, output_tokens=50,
                cost_usd=0.001, duration_ms=300, timestamp=datetime.now(),
                purpose=agent_def.role, prompt_summary="", response_summary="",
            )]

        with patch("orgbench.orchestrator.agent_act", side_effect=mock_act):
            result = await run_single(template, theme, replication=1)

        # Writer: 初回 + CFO差し戻し = 2回
        assert call_count["writer"] >= 2
        # 差し戻し分でLLM呼び出しが増える
        assert result.total_llm_calls > 7


# ============================================================
# E2E: シングルエージェント
# ============================================================

class TestE2ESingleAgent:
    @pytest.mark.asyncio
    async def test_single_agent_e2e(self, single_agent_template, make_theme):
        """シングルエージェントのE2Eフロー"""
        theme = make_theme(task_prompt="シングルエージェントテスト")
        responses = {"single": "# 完全な提案\n\n6セクション全てカバー"}
        mock_act, history = _make_deterministic_agent_act(responses)

        with patch("orgbench.orchestrator.agent_act", side_effect=mock_act):
            result = await run_single(single_agent_template, theme, replication=1)

        assert result.total_llm_calls == 1
        assert result.output_text == "# 完全な提案\n\n6セクション全てカバー"
        assert len(history) == 1


# ============================================================
# E2E: Save → Judge → Analysis パイプライン
# ============================================================

class TestE2EPipeline:
    @pytest.mark.asyncio
    async def test_save_judge_analyze_pipeline(self, tmp_path):
        """Save → Judge → Analysis のフルパイプライン"""
        # 1. 実行結果を作成・保存
        results = []
        for config in ["anchor", "single_agent"]:
            for rep in range(1, 4):
                r = RunResult(
                    config_name=config, theme_id="t01", replication=rep,
                    output_text=f"# {config}の提案 rep{rep}",
                    messages=[
                        Message("theme", "ceo", MessageType.DELEGATE_TASK, "指示"),
                        Message("ceo", "writer", MessageType.TASK_RESULT, "結果"),
                    ],
                    llm_calls=[], total_cost_usd=0.01, total_duration_sec=5.0,
                    total_llm_calls=3, total_input_tokens=1000, total_output_tokens=500,
                )
                results.append(r)
                with patch("orgbench.runner.RESULTS_DIR", tmp_path):
                    _save_result(r)

        # 結果ファイルの存在確認
        assert (tmp_path / "runs" / "anchor_t01_rep1" / "output.md").exists()
        assert (tmp_path / "runs" / "single_agent_t01_rep3" / "run_meta.json").exists()

        # 2. Judge（モック）
        scores = []
        import random
        random.seed(42)
        score_base = {"anchor": 4.0, "single_agent": 2.5}
        for r in results:
            for judge_run in [1, 2]:
                v = score_base[r.config_name] + random.uniform(-0.2, 0.2)
                scores.append(JudgeScore(
                    config_name=r.config_name, theme_id=r.theme_id,
                    replication=r.replication, judge_run=judge_run,
                    feasibility=v, novelty=v, market_insight=v,
                    financial_rigor=v, technical_depth=v, overall_quality=v,
                    rationale=f"{r.config_name} evaluation",
                ))

        with patch("orgbench.runner.RESULTS_DIR", tmp_path):
            _save_scores(scores)

        assert (tmp_path / "judge" / "scores.csv").exists()

        # 3. 操作チェック
        with patch("orgbench.analysis.RESULTS_DIR", tmp_path):
            mc = manipulation_check()

        assert mc["total_runs"] == 6  # 2 configs × 3 reps

        # 4. 効果量推定
        with patch("orgbench.analysis.RESULTS_DIR", tmp_path):
            es = estimate_effect_sizes()

        assert "feasibility" in es
        # anchor=4.0 vs single_agent=2.5 → 明確な差
        assert es["feasibility"]["eta_squared"] > 0
        assert es["feasibility"]["cohens_d_single_vs_best"] > 0

    @pytest.mark.asyncio
    async def test_idempotent_skip(self, tmp_path):
        """既存結果のスキップ（冪等性）"""
        # 1回目の結果を保存
        result = RunResult(
            config_name="anchor", theme_id="t01", replication=1,
            output_text="最初の結果", messages=[], llm_calls=[],
            total_cost_usd=0.05, total_duration_sec=10.0,
            total_llm_calls=7, total_input_tokens=5000, total_output_tokens=2000,
        )
        with patch("orgbench.runner.RESULTS_DIR", tmp_path):
            _save_result(result)

        # run_meta.json が存在することを確認
        meta_path = tmp_path / "runs" / "anchor_t01_rep1" / "run_meta.json"
        assert meta_path.exists()

        # 復元テスト
        meta = json.loads(meta_path.read_text())
        with patch("orgbench.runner.RESULTS_DIR", tmp_path):
            stub = _meta_to_stub(meta)

        assert stub.config_name == "anchor"
        assert stub.output_text == "最初の結果"
        assert stub.total_cost_usd == 0.05


# ============================================================
# E2E: 構成間の差異検証
# ============================================================

class TestE2EConfigDifferences:
    @pytest.mark.asyncio
    async def test_hub_vs_mesh_message_counts(self, simple_template, mesh_template, make_theme):
        """Hub vs Mesh で生成されるメッセージ数の比較"""
        theme = make_theme()

        async def generic_mock(agent_def, instruction, context, theme_id, temperature=0.7):
            return f"{agent_def.name}_output", [LLMCall(
                agent=agent_def.name, model="m", input_tokens=100, output_tokens=50,
                cost_usd=0.001, duration_ms=300, timestamp=datetime.now(),
                purpose=agent_def.role, prompt_summary="", response_summary="",
            )]

        with patch("orgbench.orchestrator.agent_act", side_effect=generic_mock):
            hub_result = await run_single(simple_template, theme, replication=1)

        with patch("orgbench.orchestrator.agent_act", side_effect=generic_mock):
            mesh_result = await run_single(mesh_template, theme, replication=1)

        # メッシュは同じフロー順序だが、ピアコンテキストが注入される
        # メッセージ数自体はフローステップ数 × 2 で同じはず
        assert len(hub_result.messages) == len(simple_template.flow) * 2
        assert len(mesh_result.messages) == len(mesh_template.flow) * 2

    @pytest.mark.asyncio
    async def test_review_vs_noreview_llm_calls(self, simple_template, review_template, make_theme):
        """レビューあり vs なし のLLM呼び出し数比較"""
        theme = make_theme()

        async def approved_mock(agent_def, instruction, context, theme_id, temperature=0.7):
            text = "APPROVED" if agent_def.name == "cfo" else f"{agent_def.name}_output"
            return text, [LLMCall(
                agent=agent_def.name, model="m", input_tokens=100, output_tokens=50,
                cost_usd=0.001, duration_ms=300, timestamp=datetime.now(),
                purpose=agent_def.role, prompt_summary="", response_summary="",
            )]

        with patch("orgbench.orchestrator.agent_act", side_effect=approved_mock):
            no_review = await run_single(simple_template, theme, replication=1)

        with patch("orgbench.orchestrator.agent_act", side_effect=approved_mock):
            with_review = await run_single(review_template, theme, replication=1)

        # レビューありの方がLLM呼び出しが多い
        assert with_review.total_llm_calls > no_review.total_llm_calls
