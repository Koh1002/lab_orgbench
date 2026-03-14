"""共通フィクスチャ — 全テストから利用"""
from __future__ import annotations
import json
import asyncio
import pytest
from pathlib import Path
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import asdict

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from orgbench.models import (
    AgentDef, FlowStep, TemplateConfig, ThemeConfig,
    Message, MessageType, LLMCall, RunResult, JudgeScore,
    AuthorityType, CommunicationType, ReviewType, ModelPreset,
)


# ============================================================
# pytest-asyncio 設定
# ============================================================

@pytest.fixture(scope="session")
def event_loop():
    """セッション全体で共有するイベントループ"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ============================================================
# 基本データファクトリ
# ============================================================

@pytest.fixture
def make_agent_def():
    """AgentDef ファクトリ"""
    def _make(
        name: str = "test_agent",
        role: str = "テストエージェント",
        model: str = "gpt-4o-mini",
        system_prompt: str = "あなたはテスト用エージェントです。",
        tools: list[str] | None = None,
        peers: list[str] | None = None,
        reports_to: list[str] | None = None,
        manages: list[str] | None = None,
    ) -> AgentDef:
        return AgentDef(
            name=name,
            role=role,
            model=model,
            system_prompt=system_prompt,
            tools=tools or [],
            peers=peers or [],
            reports_to=reports_to or [],
            manages=manages or [],
        )
    return _make


@pytest.fixture
def make_flow_step():
    """FlowStep ファクトリ"""
    def _make(
        agent: str = "test_agent",
        input_from: str | None = None,
        action: str = "テスト行動",
        output_to: str | None = None,
        gate: str | None = None,
    ) -> FlowStep:
        return FlowStep(
            agent=agent,
            input_from=input_from,
            action=action,
            output_to=output_to,
            gate=gate,
        )
    return _make


@pytest.fixture
def make_theme():
    """ThemeConfig ファクトリ"""
    def _make(
        id: str = "t_test",
        title: str = "テストテーマ",
        domain: str = "Test",
        uncertainty_group: str = "low",
        task_prompt: str = "テスト用ビジネス提案を作成してください。",
        search_queries: list[str] | None = None,
    ) -> ThemeConfig:
        return ThemeConfig(
            id=id, title=title, domain=domain,
            uncertainty_group=uncertainty_group,
            task_prompt=task_prompt,
            search_queries=search_queries or [],
        )
    return _make


@pytest.fixture
def make_llm_call():
    """LLMCall ファクトリ"""
    def _make(
        agent: str = "test_agent",
        model: str = "gpt-4o-mini",
        input_tokens: int = 100,
        output_tokens: int = 50,
        cost_usd: float = 0.001,
        duration_ms: int = 500,
        purpose: str = "test",
        metadata: dict | None = None,
    ) -> LLMCall:
        return LLMCall(
            agent=agent, model=model,
            input_tokens=input_tokens, output_tokens=output_tokens,
            cost_usd=cost_usd, duration_ms=duration_ms,
            timestamp=datetime.now(), purpose=purpose,
            prompt_summary="test prompt", response_summary="test response",
            metadata=metadata or {},
        )
    return _make


@pytest.fixture
def make_run_result():
    """RunResult ファクトリ"""
    def _make(
        config_name: str = "anchor",
        theme_id: str = "t_test",
        replication: int = 1,
        output_text: str = "# テスト提案\n\nテスト内容",
        messages: list | None = None,
        llm_calls: list | None = None,
        total_cost_usd: float = 0.01,
        total_duration_sec: float = 5.0,
        total_llm_calls: int = 3,
        timeout: bool = False,
        error: str | None = None,
    ) -> RunResult:
        return RunResult(
            config_name=config_name,
            theme_id=theme_id,
            replication=replication,
            output_text=output_text,
            messages=messages or [],
            llm_calls=llm_calls or [],
            total_cost_usd=total_cost_usd,
            total_duration_sec=total_duration_sec,
            total_llm_calls=total_llm_calls,
            total_input_tokens=1000,
            total_output_tokens=500,
            timeout=timeout,
            error=error,
        )
    return _make


@pytest.fixture
def make_judge_score():
    """JudgeScore ファクトリ"""
    def _make(
        config_name: str = "anchor",
        theme_id: str = "t_test",
        replication: int = 1,
        judge_run: int = 1,
        feasibility: float = 4.0,
        novelty: float = 3.5,
        market_insight: float = 4.0,
        financial_rigor: float = 3.0,
        technical_depth: float = 4.5,
        overall_quality: float = 4.0,
        rationale: str = "テスト評価",
    ) -> JudgeScore:
        return JudgeScore(
            config_name=config_name,
            theme_id=theme_id,
            replication=replication,
            judge_run=judge_run,
            feasibility=feasibility,
            novelty=novelty,
            market_insight=market_insight,
            financial_rigor=financial_rigor,
            technical_depth=technical_depth,
            overall_quality=overall_quality,
            rationale=rationale,
        )
    return _make


# ============================================================
# テンプレート構成フィクスチャ
# ============================================================

@pytest.fixture
def simple_template(make_agent_def, make_flow_step):
    """最小限の2エージェント・テンプレート"""
    ceo = make_agent_def(name="ceo", role="CEO", model="claude-haiku-4-5-20251001")
    writer = make_agent_def(name="writer", role="Writer", model="gpt-4o-mini")
    return TemplateConfig(
        name="simple_test",
        authority=AuthorityType.DEEP_HIERARCHY,
        communication=CommunicationType.HUB_AND_SPOKE,
        review=ReviewType.NONE,
        model_preset=ModelPreset.HETEROGENEOUS,
        agents=[ceo, writer],
        flow=[
            make_flow_step(agent="ceo", input_from=None, action="指示を出す", output_to="writer"),
            make_flow_step(agent="writer", input_from="ceo", action="提案を書く", output_to=None),
        ],
        max_review_rounds=0,
    )


@pytest.fixture
def review_template(make_agent_def, make_flow_step):
    """レビューゲート付きテンプレート"""
    ceo = make_agent_def(name="ceo", role="CEO", model="claude-haiku-4-5-20251001")
    writer = make_agent_def(name="writer", role="Writer", model="gpt-4o-mini")
    cfo = make_agent_def(name="cfo", role="CFO", model="gpt-4o-mini")
    return TemplateConfig(
        name="review_test",
        authority=AuthorityType.DEEP_HIERARCHY,
        communication=CommunicationType.HUB_AND_SPOKE,
        review=ReviewType.BALANCED,
        model_preset=ModelPreset.HETEROGENEOUS,
        agents=[ceo, writer, cfo],
        flow=[
            make_flow_step(agent="ceo", input_from=None, action="指示を出す", output_to="writer"),
            make_flow_step(agent="writer", input_from="ceo", action="提案を書く", output_to="cfo"),
            make_flow_step(agent="cfo", input_from="writer", action="レビュー",
                          output_to="writer", gate="review_gate"),
            make_flow_step(agent="ceo", input_from="__all__", action="統合する", output_to=None),
        ],
        max_review_rounds=1,
    )


@pytest.fixture
def mesh_template(make_agent_def, make_flow_step):
    """メッシュ通信テンプレート"""
    ceo = make_agent_def(name="ceo", role="CEO", model="claude-haiku-4-5-20251001", peers=["cfo"])
    writer = make_agent_def(name="writer", role="Writer", model="gpt-4o-mini", peers=["researcher"])
    researcher = make_agent_def(
        name="researcher", role="Researcher",
        model="gemini/gemini-2.5-flash", tools=["web_search"], peers=["writer"],
    )
    cfo = make_agent_def(name="cfo", role="CFO", model="gpt-4o-mini", peers=["ceo"])
    return TemplateConfig(
        name="mesh_test",
        authority=AuthorityType.DEEP_HIERARCHY,
        communication=CommunicationType.MESH,
        review=ReviewType.NONE,
        model_preset=ModelPreset.HETEROGENEOUS,
        agents=[ceo, researcher, writer, cfo],
        flow=[
            make_flow_step(agent="ceo", input_from=None, action="指示", output_to="researcher"),
            make_flow_step(agent="researcher", input_from="ceo", action="調査", output_to="writer"),
            make_flow_step(agent="writer", input_from="researcher", action="執筆", output_to="cfo"),
            make_flow_step(agent="cfo", input_from="writer", action="レビュー", output_to=None),
        ],
        max_review_rounds=0,
    )


@pytest.fixture
def single_agent_template(make_agent_def, make_flow_step):
    """シングルエージェント・テンプレート"""
    single = make_agent_def(
        name="single", role="統合エージェント",
        model="claude-haiku-4-5-20251001", tools=["web_search"],
    )
    return TemplateConfig(
        name="single_agent",
        authority=None,
        communication=None,
        review=None,
        model_preset=None,
        agents=[single],
        flow=[
            make_flow_step(agent="single", input_from=None, action="全てを実行", output_to=None),
        ],
        max_review_rounds=0,
    )


# ============================================================
# モック LLM レスポンスヘルパー
# ============================================================

def make_mock_llm_response(
    content: str = "テスト出力",
    input_tokens: int = 100,
    output_tokens: int = 50,
    tool_calls: list | None = None,
):
    """litellm.acompletion の戻り値をモック"""
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


def make_mock_tool_call_response(
    query: str = "テスト検索",
    tool_call_id: str = "call_123",
):
    """tool_calls付きレスポンスをモック"""
    tc = MagicMock()
    tc.id = tool_call_id
    tc.function.name = "web_search"
    tc.function.arguments = json.dumps({"query": query})

    return make_mock_llm_response(
        content=None,
        tool_calls=[tc],
    )


def make_empty_choices_response():
    """Gemini empty choices レスポンス"""
    response = MagicMock()
    response.choices = []
    return response


# ============================================================
# 一時ディレクトリ用
# ============================================================

@pytest.fixture
def tmp_results(tmp_path):
    """一時results/ディレクトリを作成"""
    runs = tmp_path / "runs"
    runs.mkdir()
    judge = tmp_path / "judge"
    judge.mkdir()
    analysis = tmp_path / "analysis"
    analysis.mkdir()
    cache = tmp_path / "cache"
    cache.mkdir()
    return tmp_path
