"""models.py のテスト — 全データモデルの生成・シリアライズ・enum値の網羅的検証"""
from __future__ import annotations
import pytest
from datetime import datetime
from dataclasses import asdict, fields

from orgbench.models import (
    Message, MessageType,
    AgentDef, FlowStep, TemplateConfig, ThemeConfig,
    LLMCall, RunResult, JudgeScore,
    AuthorityType, CommunicationType, ReviewType, ModelPreset,
)


# ============================================================
# Enum の値と文字列変換
# ============================================================

class TestMessageType:
    def test_all_values(self):
        assert set(MessageType) == {
            MessageType.DELEGATE_TASK,
            MessageType.TASK_RESULT,
            MessageType.REVIEW_REQUEST,
            MessageType.REVIEW_RESPONSE,
            MessageType.INFO,
        }

    def test_string_values(self):
        assert MessageType.DELEGATE_TASK.value == "delegate_task"
        assert MessageType.TASK_RESULT.value == "task_result"
        assert MessageType.REVIEW_REQUEST.value == "review_request"
        assert MessageType.REVIEW_RESPONSE.value == "review_response"
        assert MessageType.INFO.value == "info"

    def test_from_string(self):
        assert MessageType("delegate_task") == MessageType.DELEGATE_TASK

    def test_is_string(self):
        """str Enum なので文字列比較可能"""
        assert MessageType.DELEGATE_TASK == "delegate_task"


class TestAuthorityType:
    def test_all_values(self):
        assert set(v.value for v in AuthorityType) == {"deep", "flat", "matrix"}

    def test_from_string(self):
        assert AuthorityType("deep") == AuthorityType.DEEP_HIERARCHY
        assert AuthorityType("flat") == AuthorityType.FLAT
        assert AuthorityType("matrix") == AuthorityType.MATRIX

    def test_invalid_value_raises(self):
        with pytest.raises(ValueError):
            AuthorityType("invalid")


class TestCommunicationType:
    def test_all_values(self):
        assert set(v.value for v in CommunicationType) == {"hub", "mesh"}

    def test_from_string(self):
        assert CommunicationType("hub") == CommunicationType.HUB_AND_SPOKE
        assert CommunicationType("mesh") == CommunicationType.MESH


class TestReviewType:
    def test_all_values(self):
        assert set(v.value for v in ReviewType) == {"balanced", "finance", "tech", "none"}

    def test_from_string(self):
        assert ReviewType("balanced") == ReviewType.BALANCED
        assert ReviewType("none") == ReviewType.NONE


class TestModelPreset:
    def test_all_values(self):
        assert set(v.value for v in ModelPreset) == {"hetero", "homo_haiku", "homo_gpt"}


# ============================================================
# Message
# ============================================================

class TestMessage:
    def test_creation(self):
        msg = Message(
            from_agent="ceo",
            to_agent="writer",
            msg_type=MessageType.DELEGATE_TASK,
            content="テスト指示",
        )
        assert msg.from_agent == "ceo"
        assert msg.to_agent == "writer"
        assert msg.msg_type == MessageType.DELEGATE_TASK
        assert msg.content == "テスト指示"
        assert isinstance(msg.timestamp, datetime)
        assert msg.metadata == {}

    def test_timestamp_auto_generated(self):
        msg1 = Message("a", "b", MessageType.INFO, "test1")
        msg2 = Message("a", "b", MessageType.INFO, "test2")
        assert msg1.timestamp <= msg2.timestamp

    def test_metadata_default_not_shared(self):
        """デフォルトのmutable引数が共有されないことの検証"""
        msg1 = Message("a", "b", MessageType.INFO, "test1")
        msg2 = Message("a", "b", MessageType.INFO, "test2")
        msg1.metadata["key"] = "value"
        assert "key" not in msg2.metadata

    def test_asdict(self):
        msg = Message("ceo", "writer", MessageType.DELEGATE_TASK, "test")
        d = asdict(msg)
        assert d["from_agent"] == "ceo"
        assert d["msg_type"] == "delegate_task"  # str Enum → string
        assert "timestamp" in d


# ============================================================
# AgentDef
# ============================================================

class TestAgentDef:
    def test_minimal_creation(self):
        agent = AgentDef(name="ceo", role="CEO", model="gpt-4o-mini", system_prompt="test")
        assert agent.name == "ceo"
        assert agent.reports_to == []
        assert agent.manages == []
        assert agent.peers == []
        assert agent.tools == []

    def test_full_creation(self):
        agent = AgentDef(
            name="tl", role="TL", model="gpt-4o-mini",
            system_prompt="test",
            reports_to=["ceo"],
            manages=["researcher", "writer"],
            peers=["cfo"],
            can_communicate_with=["ceo", "cfo"],
            has_review_authority_over=["writer"],
            tools=["web_search"],
        )
        assert agent.reports_to == ["ceo"]
        assert "researcher" in agent.manages
        assert "web_search" in agent.tools

    def test_default_lists_not_shared(self):
        a1 = AgentDef(name="a", role="r", model="m", system_prompt="p")
        a2 = AgentDef(name="b", role="r", model="m", system_prompt="p")
        a1.tools.append("web_search")
        assert a2.tools == []


# ============================================================
# FlowStep
# ============================================================

class TestFlowStep:
    def test_basic(self):
        step = FlowStep(agent="ceo", input_from=None, action="分析", output_to="tl")
        assert step.agent == "ceo"
        assert step.input_from is None
        assert step.gate is None

    def test_with_gate(self):
        step = FlowStep(agent="cfo", input_from="writer", action="レビュー",
                        output_to="writer", gate="review_gate")
        assert step.gate == "review_gate"

    def test_all_input(self):
        step = FlowStep(agent="ceo", input_from="__all__", action="統合",
                        output_to=None)
        assert step.input_from == "__all__"


# ============================================================
# TemplateConfig
# ============================================================

class TestTemplateConfig:
    def test_creation(self, simple_template):
        assert simple_template.name == "simple_test"
        assert simple_template.authority == AuthorityType.DEEP_HIERARCHY
        assert len(simple_template.agents) == 2
        assert len(simple_template.flow) == 2

    def test_nullable_enums(self, single_agent_template):
        """single_agent は authority/communication/review が全て None"""
        assert single_agent_template.authority is None
        assert single_agent_template.communication is None
        assert single_agent_template.review is None
        assert single_agent_template.model_preset is None

    def test_agents_accessible_by_name(self, simple_template):
        agents_by_name = {a.name: a for a in simple_template.agents}
        assert "ceo" in agents_by_name
        assert "writer" in agents_by_name

    def test_flow_order_preserved(self, review_template):
        flow_agents = [s.agent for s in review_template.flow]
        assert flow_agents == ["ceo", "writer", "cfo", "ceo"]


# ============================================================
# ThemeConfig
# ============================================================

class TestThemeConfig:
    def test_creation(self, make_theme):
        theme = make_theme()
        assert theme.id == "t_test"
        assert theme.uncertainty_group == "low"

    def test_search_queries_default(self, make_theme):
        theme = make_theme()
        assert theme.search_queries == []

    def test_search_queries_provided(self, make_theme):
        theme = make_theme(search_queries=["query1", "query2"])
        assert len(theme.search_queries) == 2


# ============================================================
# LLMCall
# ============================================================

class TestLLMCall:
    def test_creation(self, make_llm_call):
        call = make_llm_call()
        assert call.agent == "test_agent"
        assert call.cost_usd == 0.001
        assert call.metadata == {}

    def test_with_metadata(self, make_llm_call):
        call = make_llm_call(metadata={"tool_calls": True})
        assert call.metadata["tool_calls"] is True

    def test_asdict_serializable(self, make_llm_call):
        call = make_llm_call()
        d = asdict(call)
        assert isinstance(d["timestamp"], datetime)
        assert d["agent"] == "test_agent"


# ============================================================
# RunResult
# ============================================================

class TestRunResult:
    def test_creation(self, make_run_result):
        result = make_run_result()
        assert result.config_name == "anchor"
        assert result.timeout is False
        assert result.error is None

    def test_timeout(self, make_run_result):
        result = make_run_result(timeout=True, error="Timeout after 600s")
        assert result.timeout is True
        assert "Timeout" in result.error

    def test_error(self, make_run_result):
        result = make_run_result(error="API error")
        assert result.error == "API error"
        assert result.timeout is False


# ============================================================
# JudgeScore
# ============================================================

class TestJudgeScore:
    def test_creation(self, make_judge_score):
        score = make_judge_score()
        assert score.feasibility == 4.0
        assert score.judge_run == 1

    def test_asdict(self, make_judge_score):
        score = make_judge_score()
        d = asdict(score)
        assert set(d.keys()) == {
            "config_name", "theme_id", "replication", "judge_run",
            "feasibility", "novelty", "market_insight",
            "financial_rigor", "technical_depth", "overall_quality",
            "rationale",
        }

    def test_score_ranges(self, make_judge_score):
        """スコアは1-5の範囲（モデル上の制約はないが、意図を文書化）"""
        score = make_judge_score(feasibility=1.0, novelty=5.0)
        assert 1.0 <= score.feasibility <= 5.0
        assert 1.0 <= score.novelty <= 5.0
