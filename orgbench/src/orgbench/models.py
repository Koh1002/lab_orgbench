"""OrgBench データモデル"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from typing import Any


# ============================================================
# メッセージ
# ============================================================

class MessageType(str, Enum):
    DELEGATE_TASK = "delegate_task"
    TASK_RESULT = "task_result"
    REVIEW_REQUEST = "review_request"
    REVIEW_RESPONSE = "review_response"
    INFO = "info"


@dataclass
class Message:
    from_agent: str
    to_agent: str
    msg_type: MessageType
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)


# ============================================================
# エージェント構成
# ============================================================

class AuthorityType(str, Enum):
    DEEP_HIERARCHY = "deep"
    FLAT = "flat"
    MATRIX = "matrix"


class CommunicationType(str, Enum):
    HUB_AND_SPOKE = "hub"
    MESH = "mesh"


class ReviewType(str, Enum):
    BALANCED = "balanced"
    FINANCE_HEAVY = "finance"
    TECH_HEAVY = "tech"
    NONE = "none"


class ModelPreset(str, Enum):
    HETEROGENEOUS = "hetero"
    HOMO_HAIKU = "homo_haiku"
    HOMO_GPT = "homo_gpt"


@dataclass
class AgentDef:
    """個別エージェントの定義"""
    name: str
    role: str
    model: str
    system_prompt: str
    reports_to: list[str] = field(default_factory=list)
    manages: list[str] = field(default_factory=list)
    peers: list[str] = field(default_factory=list)
    can_communicate_with: list[str] = field(default_factory=list)
    has_review_authority_over: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)


@dataclass
class FlowStep:
    """オーケストレータが実行する1ステップ"""
    agent: str                    # 実行するエージェント名
    input_from: str | None        # 入力を受け取るエージェント（Noneならテーマ）
    action: str                   # "research", "write", "review", "synthesize", "delegate"
    output_to: str | None         # 出力を渡すエージェント
    gate: str | None = None       # "review_gate" の場合、不合格で差し戻し


@dataclass
class TemplateConfig:
    """情報フロー設計テンプレート"""
    name: str
    authority: AuthorityType | None
    communication: CommunicationType | None
    review: ReviewType | None
    model_preset: ModelPreset | None
    agents: list[AgentDef]
    flow: list[FlowStep]          # オーケストレータが実行するフロー定義
    max_review_rounds: int = 2    # レビュー差し戻しの最大回数


# ============================================================
# テーマ
# ============================================================

@dataclass
class ThemeConfig:
    id: str                        # "t01_ai_accounting"
    title: str                     # "中小企業向けAI経理自動化"
    domain: str                    # "FinTech"
    uncertainty_group: str         # "low" / "medium" / "high"
    task_prompt: str               # ビジネス提案タスクの詳細プロンプト
    search_queries: list[str] = field(default_factory=list)


# ============================================================
# 実行結果
# ============================================================

@dataclass
class LLMCall:
    """1回のLLM呼び出し記録"""
    agent: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    duration_ms: int
    timestamp: datetime
    purpose: str                   # "research", "review", "synthesize" 等
    prompt_summary: str            # プロンプトの先頭200文字
    response_summary: str          # レスポンスの先頭200文字
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RunResult:
    """1回の実験実行の全記録"""
    config_name: str
    theme_id: str
    replication: int
    output_text: str               # 最終ビジネス提案（Markdown）
    messages: list[Message]        # 全メッセージ
    llm_calls: list[LLMCall]       # 全LLM呼び出し
    total_cost_usd: float
    total_duration_sec: float
    total_llm_calls: int
    total_input_tokens: int
    total_output_tokens: int
    timeout: bool = False
    error: str | None = None


# ============================================================
# 評価結果
# ============================================================

@dataclass
class JudgeScore:
    """1つの出力に対する評価スコア"""
    config_name: str
    theme_id: str
    replication: int
    judge_run: int                 # 1 or 2（2回独立評価）
    feasibility: float             # 1-5
    novelty: float
    market_insight: float
    financial_rigor: float
    technical_depth: float
    overall_quality: float
    rationale: str                 # 評価根拠（Judge出力テキスト）
