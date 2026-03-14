# OrgBench 詳細設計書

**Version:** v1.0
**Date:** 2026-03-12
**関連:** pilot_experiment_design.md (v0.2)

---

## 1. 設計方針

### 1.1 PJ_Animaとの差異

PJ_Animaは常駐型マルチエージェントシステム（ファイルベース通信、自律モード、無期限実行）だが、OrgBenchは**バッチ実験システム**であり、以下の点で根本的に異なる設計が必要：

| 観点 | PJ_Anima | OrgBench |
|------|---------|----------|
| 実行モデル | 常駐・自律駆動 | バッチ・オーケストレータ駆動 |
| 通信 | ファイルシステムベース（ポーリング） | **インメモリ（同期的）** |
| メッセージフロー | エージェントが自律的に判断 | **オーケストレータが構成テンプレートに基づき制御** |
| 権限構造 | プロンプトで暗示 | **オーケストレータが強制（ハードゲート）** |
| 目的 | 汎用タスク実行 | 構成間比較のための制御実験 |

### 1.2 設計原則

1. **構成の外部化**: 情報フロー設計をYAMLテンプレートで完全に宣言。コード変更ゼロで構成切り替え
2. **決定論的オーケストレーション**: メッセージフローをオーケストレータが制御し、権限・レビューゲートをハードに強制（操作チェックの課題を構造的に解決）
3. **全データ記録**: 全LLM呼び出し、全メッセージ、コスト、時間を構造化ログに記録
4. **検索キャッシュ**: Tavily結果をテーマ単位でキャッシュし、構成間で同一情報を保証
5. **冪等性**: 同一(構成, テーマ, 反復番号)の再実行が安全に可能

---

## 2. ディレクトリ構成

```
orgbench/
├── pyproject.toml
├── README.md
│
├── configs/                          # 実験構成（YAML）
│   ├── templates/                    # 情報フロー設計テンプレート
│   │   ├── anchor.yaml               # Deep+Hub+Balanced+Hetero（基準）
│   │   ├── flat_hub.yaml
│   │   ├── matrix_hub.yaml
│   │   ├── deep_mesh.yaml
│   │   ├── flat_mesh.yaml
│   │   ├── deep_finance.yaml
│   │   ├── deep_tech.yaml
│   │   ├── deep_noreview.yaml
│   │   ├── homo_haiku.yaml
│   │   ├── homo_gpt.yaml
│   │   └── single_agent.yaml
│   ├── themes/                       # タスクテーマ定義
│   │   ├── t01_ai_accounting.yaml
│   │   ├── t02_legal_review.yaml
│   │   └── ...
│   ├── prompts/                      # 役割別システムプロンプト
│   │   ├── ceo.md
│   │   ├── tl.md
│   │   ├── cfo.md
│   │   ├── cdo.md
│   │   ├── researcher.md
│   │   ├── writer.md
│   │   └── single_agent.md
│   ├── judge/                        # 評価ルーブリック
│   │   └── rubric.md
│   └── experiment.yaml               # 実験全体設定（テーマリスト、反復数等）
│
├── src/
│   └── orgbench/
│       ├── __init__.py
│       ├── models.py                 # データモデル（Message, AgentConfig, RunResult等）
│       ├── llm.py                    # LLM呼び出し（litellm wrapper、コスト追跡）
│       ├── tools.py                  # Tavily検索（キャッシュ付き）
│       ├── agents.py                 # エージェント（LLM呼び出し+応答解析）
│       ├── orchestrator.py           # オーケストレータ（フロー制御の中核）
│       ├── judge.py                  # LLM-as-Judge評価パイプライン
│       ├── runner.py                 # 実験ランナー（バッチ実行制御）
│       ├── analysis.py               # 操作チェック・効果量推定・統計分析
│       └── config_loader.py          # YAML読み込み・バリデーション
│
├── results/                          # 実験結果（gitignore、自動生成）
│   ├── runs/                         # 個別実行結果
│   │   └── {config}_{theme}_{rep}/
│   │       ├── output.md             # 最終ビジネス提案
│   │       ├── messages.jsonl        # 全メッセージログ
│   │       ├── llm_calls.jsonl       # 全LLM呼び出しログ
│   │       └── run_meta.json         # メタデータ（コスト、時間、構成情報）
│   ├── cache/                        # Tavily検索キャッシュ
│   │   └── {theme_id}/
│   │       └── {query_hash}.json
│   ├── judge/                        # 評価結果
│   │   └── scores.csv
│   └── analysis/                     # 分析結果
│       ├── manipulation_check.csv
│       ├── effect_sizes.csv
│       └── figures/
│
└── tests/
    ├── test_models.py
    ├── test_orchestrator.py
    ├── test_judge.py
    └── test_config_loader.py
```

---

## 3. データモデル (`models.py`)

```python
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
    authority: AuthorityType
    communication: CommunicationType
    review: ReviewType
    model_preset: ModelPreset
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
    search_queries: list[str]      # 不確実性指標用の検索クエリ


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
```

---

## 4. LLM呼び出し (`llm.py`)

```python
"""LLM呼び出しラッパー（litellm + コスト追跡）"""
from __future__ import annotations
import time
import litellm
from dataclasses import dataclass
from .models import LLMCall
from datetime import datetime

# litellmのログを抑制
litellm.suppress_debug_info = True

PRICING: dict[str, tuple[float, float]] = {
    # (input_per_1M, output_per_1M)
    "claude-haiku-4-5-20251001": (1.00, 5.00),
    "gpt-4o-mini": (0.15, 0.60),
    "gemini/gemini-2.5-flash": (0.15, 0.60),
}

MAX_RETRIES = 3
RETRY_DELAY = 2.0


async def call_llm(
    model: str,
    messages: list[dict],
    temperature: float = 0.7,
    max_tokens: int = 2048,
    agent_name: str = "",
    purpose: str = "",
    tools: list[dict] | None = None,
) -> tuple[str, LLMCall]:
    """
    LLMを呼び出し、レスポンステキストとLLMCallログを返す。

    Returns:
        (response_text, llm_call_log)
    """
    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            start = time.monotonic()
            kwargs = dict(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            if tools:
                kwargs["tools"] = tools

            response = await litellm.acompletion(**kwargs)
            duration_ms = int((time.monotonic() - start) * 1000)

            # Gemini empty choices対策
            if not response.choices:
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(RETRY_DELAY)
                    continue
                return "", _make_call_log(
                    agent_name, model, 0, 0, 0, duration_ms, purpose, "", ""
                )

            choice = response.choices[0]
            text = choice.message.content or ""
            usage = response.usage

            input_tokens = usage.prompt_tokens if usage else 0
            output_tokens = usage.completion_tokens if usage else 0
            cost = _calc_cost(model, input_tokens, output_tokens)

            call_log = _make_call_log(
                agent_name, model, input_tokens, output_tokens,
                cost, duration_ms, purpose,
                messages[-1].get("content", "")[:200],
                text[:200],
            )

            # tool_callsがある場合はJSON形式で返す
            if choice.message.tool_calls:
                import json
                tool_data = []
                for tc in choice.message.tool_calls:
                    tool_data.append({
                        "id": tc.id,
                        "name": tc.function.name,
                        "arguments": json.loads(tc.function.arguments),
                    })
                text = json.dumps(tool_data)
                call_log.metadata = {"tool_calls": True}

            return text, call_log

        except litellm.RateLimitError as e:
            retry_after = 60.0
            if hasattr(e, "response") and e.response:
                retry_after = float(
                    e.response.headers.get("Retry-After", 60)
                )
            await asyncio.sleep(retry_after)
            last_error = e
        except Exception as e:
            last_error = e
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(RETRY_DELAY)

    raise RuntimeError(f"LLM call failed after {MAX_RETRIES} retries: {last_error}")


def _calc_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    for key, (inp_price, out_price) in PRICING.items():
        if key in model:
            return (input_tokens * inp_price + output_tokens * out_price) / 1_000_000
    return 0.0


def _make_call_log(
    agent: str, model: str, inp: int, out: int,
    cost: float, dur: int, purpose: str, prompt: str, resp: str,
) -> LLMCall:
    return LLMCall(
        agent=agent, model=model,
        input_tokens=inp, output_tokens=out,
        cost_usd=cost, duration_ms=dur,
        timestamp=datetime.now(), purpose=purpose,
        prompt_summary=prompt, response_summary=resp,
    )
```

---

## 5. ツール（Tavily検索キャッシュ） (`tools.py`)

```python
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
```

---

## 6. エージェント (`agents.py`)

```python
"""エージェント: LLM呼び出し + 応答解析。状態は持たない純粋関数的設計。"""
from __future__ import annotations
from .models import AgentDef, LLMCall, Message, MessageType
from .llm import call_llm
from .tools import search_web
import json


async def agent_act(
    agent_def: AgentDef,
    instruction: str,
    context: str,
    theme_id: str,
    temperature: float = 0.7,
    max_tokens: int = 2048,
) -> tuple[str, list[LLMCall]]:
    """
    エージェントが1回行動する。

    Args:
        agent_def: エージェント定義
        instruction: 今回の指示（オーケストレータから）
        context: これまでの文脈（他エージェントの出力等）
        theme_id: テーマID（検索キャッシュ用）

    Returns:
        (output_text, llm_call_logs)
    """
    calls: list[LLMCall] = []

    system_msg = agent_def.system_prompt
    user_msg = _build_user_message(instruction, context)

    messages = [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_msg},
    ]

    # Researcher のみ検索ツールを使用
    if "web_search" in agent_def.tools:
        output, tool_calls_log = await _act_with_search(
            agent_def, messages, theme_id, temperature, max_tokens,
        )
        calls.extend(tool_calls_log)
    else:
        text, call_log = await call_llm(
            model=agent_def.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            agent_name=agent_def.name,
            purpose=agent_def.role,
        )
        calls.append(call_log)
        output = text

    return output, calls


async def _act_with_search(
    agent_def: AgentDef,
    messages: list[dict],
    theme_id: str,
    temperature: float,
    max_tokens: int,
) -> tuple[str, list[LLMCall]]:
    """検索ツール付きのエージェント行動。最大2ラウンドのtool use。"""
    calls = []
    tools = [_search_tool_schema()]

    for round_num in range(3):  # 最大3ラウンド（初回+2回tool use）
        text, call_log = await call_llm(
            model=agent_def.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            agent_name=agent_def.name,
            purpose=f"{agent_def.role}_round{round_num}",
            tools=tools if round_num < 2 else None,  # 最終ラウンドはツールなし
        )
        calls.append(call_log)

        # tool_callsがなければ完了
        if not call_log.metadata.get("tool_calls"):
            return text, calls

        # tool_callsを実行
        tool_calls = json.loads(text)
        tool_results = []
        for tc in tool_calls:
            if tc["name"] == "web_search":
                result = await search_web(
                    query=tc["arguments"]["query"],
                    theme_id=theme_id,
                )
                tool_results.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": result,
                })

        # tool結果をメッセージに追加
        messages.append({"role": "assistant", "content": text, "tool_calls": tool_calls})
        messages.extend(tool_results)

    return text, calls


def _build_user_message(instruction: str, context: str) -> str:
    parts = []
    if context:
        parts.append(f"## これまでの情報\n\n{context}")
    parts.append(f"## 指示\n\n{instruction}")
    parts.append(
        "\n## 出力形式\n"
        "Markdown形式で回答してください。"
    )
    return "\n\n".join(parts)


def _search_tool_schema() -> dict:
    return {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Web検索を行い、最新の情報を取得する",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "検索クエリ",
                    }
                },
                "required": ["query"],
            },
        },
    }
```

---

## 7. オーケストレータ (`orchestrator.py`) — 中核モジュール

```python
"""
オーケストレータ: 情報フロー設計テンプレートに基づきエージェント間のメッセージフローを制御。

PJ_Animaとの最大の違い:
- エージェントが自律的にメッセージを送るのではなく、オーケストレータがフローを駆動
- 権限構造・レビューゲートはオーケストレータがハードに強制
- メッセージは全てインメモリ（ファイルI/Oなし）
"""
from __future__ import annotations
import asyncio
import time
from datetime import datetime
from .models import (
    TemplateConfig, ThemeConfig, FlowStep, AgentDef,
    Message, MessageType, LLMCall, RunResult,
)
from .agents import agent_act


async def run_single(
    template: TemplateConfig,
    theme: ThemeConfig,
    replication: int,
    temperature: float = 0.7,
    timeout_sec: float = 600.0,
) -> RunResult:
    """
    1回の実験実行。テンプレートのフロー定義に従い、エージェントを順次実行する。

    フロー例（Deep + Hub + Balanced）:
      1. CEO: テーマを受け取り、Researcher/Writerへの指示を生成
      2. Researcher: 市場調査・技術調査を実施（Web検索あり）
      3. Writer: 調査結果を基にビジネス提案ドラフトを作成
      4. CFO: 財務レビュー（review_gate）
      5. CDO: 技術レビュー（review_gate）
      6. CEO: レビュー結果を踏まえ最終提案を統合
    """
    start_time = time.monotonic()
    all_messages: list[Message] = []
    all_llm_calls: list[LLMCall] = []
    agent_outputs: dict[str, str] = {}  # agent_name -> latest output
    agents_by_name: dict[str, AgentDef] = {a.name: a for a in template.agents}

    try:
        result = await asyncio.wait_for(
            _execute_flow(
                template, theme, agents_by_name,
                agent_outputs, all_messages, all_llm_calls,
                temperature,
            ),
            timeout=timeout_sec,
        )
        timeout = False
        error = None
    except asyncio.TimeoutError:
        result = agent_outputs.get("ceo", "（タイムアウトにより未完了）")
        timeout = True
        error = f"Timeout after {timeout_sec}s"
    except Exception as e:
        result = agent_outputs.get("ceo", "")
        timeout = False
        error = str(e)

    elapsed = time.monotonic() - start_time

    return RunResult(
        config_name=template.name,
        theme_id=theme.id,
        replication=replication,
        output_text=result,
        messages=all_messages,
        llm_calls=all_llm_calls,
        total_cost_usd=sum(c.cost_usd for c in all_llm_calls),
        total_duration_sec=elapsed,
        total_llm_calls=len(all_llm_calls),
        total_input_tokens=sum(c.input_tokens for c in all_llm_calls),
        total_output_tokens=sum(c.output_tokens for c in all_llm_calls),
        timeout=timeout,
        error=error,
    )


async def _execute_flow(
    template: TemplateConfig,
    theme: ThemeConfig,
    agents: dict[str, AgentDef],
    outputs: dict[str, str],
    messages: list[Message],
    llm_calls: list[LLMCall],
    temperature: float,
) -> str:
    """フロー定義に従いステップを順次実行。"""

    for step in template.flow:
        agent_def = agents[step.agent]

        # 入力コンテキストの構築
        if step.input_from is None:
            # 最初のステップ: テーマプロンプトが入力
            context = ""
            instruction = theme.task_prompt
        elif step.input_from == "__all__":
            # 全エージェントの出力を統合（CEO統合ステップ）
            context = _merge_outputs(outputs, agents, template)
            instruction = step.action
        else:
            context = outputs.get(step.input_from, "")
            instruction = step.action

        # メッシュ通信: ピアの出力も文脈に追加
        if template.communication == "mesh" and agent_def.peers:
            peer_context = "\n\n".join(
                f"### {p}の出力:\n{outputs[p]}"
                for p in agent_def.peers if p in outputs
            )
            if peer_context:
                context = f"{context}\n\n## 他メンバーの知見\n{peer_context}"

        # エージェント実行
        output, calls = await agent_act(
            agent_def=agent_def,
            instruction=instruction,
            context=context,
            theme_id=theme.id,
            temperature=temperature,
        )

        llm_calls.extend(calls)
        outputs[step.agent] = output

        # メッセージログ記録
        messages.append(Message(
            from_agent=step.input_from or "theme",
            to_agent=step.agent,
            msg_type=MessageType.DELEGATE_TASK,
            content=instruction[:500],
        ))
        messages.append(Message(
            from_agent=step.agent,
            to_agent=step.output_to or "orchestrator",
            msg_type=MessageType.TASK_RESULT,
            content=output[:500],
        ))

        # レビューゲート処理
        if step.gate == "review_gate":
            passed = _check_review_pass(output)
            if not passed:
                # 差し戻し: 元のエージェントを再実行（最大max_review_rounds回）
                # 簡略化: レビューコメントを付けて1回だけ再実行
                revision_instruction = (
                    f"以下のレビューコメントを踏まえて修正してください:\n\n{output}"
                )
                target = step.output_to
                if target and target in agents:
                    revised, rev_calls = await agent_act(
                        agent_def=agents[target],
                        instruction=revision_instruction,
                        context=outputs.get(target, ""),
                        theme_id=theme.id,
                        temperature=temperature,
                    )
                    llm_calls.extend(rev_calls)
                    outputs[target] = revised

    # 最終出力はフローの最後のステップのエージェントから
    final_agent = template.flow[-1].agent
    return outputs.get(final_agent, "")


def _merge_outputs(
    outputs: dict[str, str],
    agents: dict[str, AgentDef],
    template: TemplateConfig,
) -> str:
    """全エージェントの出力を役割別にマージ。"""
    sections = []
    for agent_def in template.agents:
        if agent_def.name in outputs and agent_def.name != "ceo":
            sections.append(
                f"## {agent_def.role}（{agent_def.name}）の報告\n\n"
                f"{outputs[agent_def.name]}"
            )
    return "\n\n---\n\n".join(sections)


def _check_review_pass(review_output: str) -> bool:
    """レビュー結果から合格/不合格を判定。"""
    lower = review_output.lower()
    # レビュアーに「APPROVED」「承認」を含めるようプロンプトで指示
    return "approved" in lower or "承認" in lower
```

---

## 8. LLM-as-Judge (`judge.py`)

```python
"""LLM-as-Judge 評価パイプライン"""
from __future__ import annotations
from pathlib import Path
from .models import JudgeScore, RunResult
from .llm import call_llm


RUBRIC_PATH = Path("configs/judge/rubric.md")

JUDGE_MODEL = "gemini/gemini-2.5-flash"

JUDGE_SYSTEM_PROMPT = """あなたはビジネス提案の品質を評価する専門評価者です。
以下のルーブリックに基づき、提出されたビジネス提案を6つの次元で1-5のスケールで評価してください。

{rubric}

## 出力形式
必ず以下のJSON形式で出力してください:
```json
{{
  "feasibility": <1-5>,
  "novelty": <1-5>,
  "market_insight": <1-5>,
  "financial_rigor": <1-5>,
  "technical_depth": <1-5>,
  "overall_quality": <1-5>,
  "rationale": "<評価根拠を200文字以内で>"
}}
```
"""


async def judge_single(
    output_text: str,
    config_name: str,
    theme_id: str,
    replication: int,
    judge_run: int,
) -> JudgeScore:
    """1つの出力を評価する。"""
    rubric = RUBRIC_PATH.read_text(encoding="utf-8")
    system = JUDGE_SYSTEM_PROMPT.replace("{rubric}", rubric)

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": f"## 評価対象のビジネス提案\n\n{output_text}"},
    ]

    text, _ = await call_llm(
        model=JUDGE_MODEL,
        messages=messages,
        temperature=0.3,  # 評価は低温で安定させる
        max_tokens=1024,
        agent_name="judge",
        purpose=f"judge_run{judge_run}",
    )

    scores = _parse_judge_output(text)

    return JudgeScore(
        config_name=config_name,
        theme_id=theme_id,
        replication=replication,
        judge_run=judge_run,
        **scores,
    )


def _parse_judge_output(text: str) -> dict:
    """Judge出力からスコアを抽出。"""
    import json
    import re

    # JSON部分を抽出
    match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        raw = match.group(1)
    else:
        # バックティックなしのJSON
        match = re.search(r"\{.*\}", text, re.DOTALL)
        raw = match.group(0) if match else "{}"

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        data = {}

    dims = ["feasibility", "novelty", "market_insight",
            "financial_rigor", "technical_depth", "overall_quality"]
    result = {d: float(data.get(d, 3.0)) for d in dims}
    result["rationale"] = data.get("rationale", "")
    return result


async def judge_batch(results: list[RunResult]) -> list[JudgeScore]:
    """全結果を2回ずつ評価。"""
    import asyncio

    tasks = []
    for r in results:
        for judge_run in [1, 2]:
            tasks.append(judge_single(
                output_text=r.output_text,
                config_name=r.config_name,
                theme_id=r.theme_id,
                replication=r.replication,
                judge_run=judge_run,
            ))

    # 並列度を制限（API rate limit対策）
    semaphore = asyncio.Semaphore(5)

    async def limited(coro):
        async with semaphore:
            return await coro

    return await asyncio.gather(*[limited(t) for t in tasks])
```

---

## 9. 実験ランナー (`runner.py`)

```python
"""実験ランナー: バッチ実行制御、進捗表示、結果永続化"""
from __future__ import annotations
import asyncio
import json
from pathlib import Path
from datetime import datetime
from dataclasses import asdict

from .models import RunResult, TemplateConfig, ThemeConfig
from .orchestrator import run_single
from .judge import judge_batch, JudgeScore
from .config_loader import load_experiment


RESULTS_DIR = Path("results")


async def run_experiment(
    experiment_yaml: str = "configs/experiment.yaml",
    phase: str = "pilot",  # "pilot" or "main"
) -> None:
    """実験全体を実行する。"""
    exp = load_experiment(experiment_yaml)

    templates: list[TemplateConfig] = exp["templates"]
    themes: list[ThemeConfig] = exp["themes"]
    replications: int = exp["replications"]
    temperature: float = exp.get("temperature", 0.7)
    timeout: float = exp.get("timeout_sec", 600.0)

    total_runs = len(templates) * len(themes) * replications
    print(f"=== OrgBench {phase} ===")
    print(f"構成数: {len(templates)}, テーマ数: {len(themes)}, "
          f"反復: {replications}, 総実行数: {total_runs}")

    all_results: list[RunResult] = []
    completed = 0
    total_cost = 0.0

    for tmpl in templates:
        for theme in themes:
            for rep in range(1, replications + 1):
                # スキップ判定（既存結果があればスキップ）
                run_dir = _run_dir(tmpl.name, theme.id, rep)
                if (run_dir / "run_meta.json").exists():
                    print(f"  [skip] {tmpl.name}/{theme.id}/rep{rep}")
                    # 既存結果を読み込み
                    meta = json.loads((run_dir / "run_meta.json").read_text())
                    all_results.append(_meta_to_stub(meta))
                    completed += 1
                    continue

                # 実行
                result = await run_single(
                    template=tmpl,
                    theme=theme,
                    replication=rep,
                    temperature=temperature,
                    timeout_sec=timeout,
                )

                # 結果保存
                _save_result(result)
                all_results.append(result)

                completed += 1
                total_cost += result.total_cost_usd

                status = "✓" if not result.timeout and not result.error else "✗"
                print(
                    f"  [{status}] {tmpl.name}/{theme.id}/rep{rep} "
                    f"| ${result.total_cost_usd:.4f} "
                    f"| {result.total_duration_sec:.1f}s "
                    f"| {result.total_llm_calls} calls "
                    f"| [{completed}/{total_runs}] "
                    f"| 累計${total_cost:.3f}"
                )

    print(f"\n=== 実行完了: {completed}/{total_runs} runs, 総コスト${total_cost:.3f} ===")

    # LLM-as-Judge 評価
    print("\n=== LLM-as-Judge 評価開始 ===")
    valid_results = [r for r in all_results if not r.timeout and not r.error]
    scores = await judge_batch(valid_results)
    _save_scores(scores)
    print(f"=== 評価完了: {len(scores)} scores ===")


def _run_dir(config: str, theme: str, rep: int) -> Path:
    return RESULTS_DIR / "runs" / f"{config}_{theme}_rep{rep}"


def _save_result(result: RunResult) -> None:
    """実行結果をファイルに保存。"""
    run_dir = _run_dir(result.config_name, result.theme_id, result.replication)
    run_dir.mkdir(parents=True, exist_ok=True)

    # 最終提案
    (run_dir / "output.md").write_text(result.output_text, encoding="utf-8")

    # メッセージログ
    with open(run_dir / "messages.jsonl", "w", encoding="utf-8") as f:
        for msg in result.messages:
            f.write(json.dumps(asdict(msg), default=str, ensure_ascii=False) + "\n")

    # LLM呼び出しログ
    with open(run_dir / "llm_calls.jsonl", "w", encoding="utf-8") as f:
        for call in result.llm_calls:
            f.write(json.dumps(asdict(call), default=str, ensure_ascii=False) + "\n")

    # メタデータ
    meta = {
        "config_name": result.config_name,
        "theme_id": result.theme_id,
        "replication": result.replication,
        "total_cost_usd": result.total_cost_usd,
        "total_duration_sec": result.total_duration_sec,
        "total_llm_calls": result.total_llm_calls,
        "total_input_tokens": result.total_input_tokens,
        "total_output_tokens": result.total_output_tokens,
        "timeout": result.timeout,
        "error": result.error,
        "timestamp": datetime.now().isoformat(),
    }
    (run_dir / "run_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _save_scores(scores: list[JudgeScore]) -> None:
    """評価スコアをCSVに保存。"""
    import csv
    score_dir = RESULTS_DIR / "judge"
    score_dir.mkdir(parents=True, exist_ok=True)

    path = score_dir / "scores.csv"
    fields = [
        "config_name", "theme_id", "replication", "judge_run",
        "feasibility", "novelty", "market_insight",
        "financial_rigor", "technical_depth", "overall_quality",
        "rationale",
    ]

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for s in scores:
            writer.writerow(asdict(s))


def _meta_to_stub(meta: dict) -> RunResult:
    """メタデータからRunResultスタブを復元（Judge用）。"""
    run_dir = _run_dir(meta["config_name"], meta["theme_id"], meta["replication"])
    output = (run_dir / "output.md").read_text(encoding="utf-8") if (run_dir / "output.md").exists() else ""
    return RunResult(
        config_name=meta["config_name"],
        theme_id=meta["theme_id"],
        replication=meta["replication"],
        output_text=output,
        messages=[], llm_calls=[],
        total_cost_usd=meta["total_cost_usd"],
        total_duration_sec=meta["total_duration_sec"],
        total_llm_calls=meta["total_llm_calls"],
        total_input_tokens=meta["total_input_tokens"],
        total_output_tokens=meta["total_output_tokens"],
        timeout=meta.get("timeout", False),
        error=meta.get("error"),
    )
```

---

## 10. 分析モジュール (`analysis.py`)

```python
"""操作チェック・効果量推定・統計分析"""
from __future__ import annotations
import json
import csv
from pathlib import Path
from collections import defaultdict
import math

RESULTS_DIR = Path("results")


# ============================================================
# P1: 操作チェック
# ============================================================

def manipulation_check() -> dict:
    """全実行のメッセージログを分析し、操作チェックメトリクスを算出。"""
    runs_dir = RESULTS_DIR / "runs"
    results = []

    for run_dir in sorted(runs_dir.iterdir()):
        if not run_dir.is_dir():
            continue
        meta_path = run_dir / "run_meta.json"
        msg_path = run_dir / "messages.jsonl"
        if not meta_path.exists() or not msg_path.exists():
            continue

        meta = json.loads(meta_path.read_text())
        messages = []
        with open(msg_path, encoding="utf-8") as f:
            for line in f:
                messages.append(json.loads(line))

        config = meta["config_name"]

        # 通信グラフの構築（実際のメッセージフロー）
        actual_edges = set()
        for msg in messages:
            actual_edges.add((msg["from_agent"], msg["to_agent"]))

        # レビュー実行の確認
        review_msgs = [m for m in messages if m["msg_type"] in ("review_request", "review_response")]

        results.append({
            "run": run_dir.name,
            "config": config,
            "message_count": len(messages),
            "unique_edges": len(actual_edges),
            "review_messages": len(review_msgs),
            "edges": list(actual_edges),
        })

    # CSV出力
    out_path = RESULTS_DIR / "analysis" / "manipulation_check.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["run", "config", "message_count", "unique_edges", "review_messages"])
        writer.writeheader()
        for r in results:
            writer.writerow({k: v for k, v in r.items() if k != "edges"})

    return {"total_runs": len(results), "output": str(out_path)}


# ============================================================
# P2: 効果量推定
# ============================================================

def estimate_effect_sizes() -> dict:
    """Judge スコアから構成間の効果量を推定。"""
    scores_path = RESULTS_DIR / "judge" / "scores.csv"
    if not scores_path.exists():
        return {"error": "scores.csv not found"}

    # スコア読み込み
    config_scores: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    with open(scores_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            config = row["config_name"]
            for dim in ["feasibility", "novelty", "market_insight",
                        "financial_rigor", "technical_depth", "overall_quality"]:
                config_scores[config][dim].append(float(row[dim]))

    dims = ["feasibility", "novelty", "market_insight",
            "financial_rigor", "technical_depth", "overall_quality"]

    results = {}
    for dim in dims:
        # 全構成のスコアを収集
        groups = {}
        for config, scores_dict in config_scores.items():
            groups[config] = scores_dict[dim]

        # η² (one-way ANOVA effect size) の計算
        eta_sq = _compute_eta_squared(list(groups.values()))

        # Single-Agent vs Best-Multi の Cohen's d
        if "single_agent" in groups:
            single_scores = groups["single_agent"]
            multi_configs = {k: v for k, v in groups.items() if k != "single_agent"}
            if multi_configs:
                best_multi_name = max(multi_configs, key=lambda k: _mean(multi_configs[k]))
                d = _cohens_d(single_scores, multi_configs[best_multi_name])
            else:
                d = 0.0
        else:
            d = 0.0

        results[dim] = {"eta_squared": eta_sq, "cohens_d_single_vs_best": d}

    # CSV出力
    out_path = RESULTS_DIR / "analysis" / "effect_sizes.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["dimension", "eta_squared", "cohens_d_single_vs_best"])
        for dim, vals in results.items():
            writer.writerow([dim, f"{vals['eta_squared']:.4f}", f"{vals['cohens_d_single_vs_best']:.4f}"])

    return results


def _mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def _var(xs: list[float]) -> float:
    m = _mean(xs)
    return sum((x - m) ** 2 for x in xs) / (len(xs) - 1) if len(xs) > 1 else 0.0


def _compute_eta_squared(groups: list[list[float]]) -> float:
    """One-way ANOVA の η² を計算。"""
    all_vals = [x for g in groups for x in g]
    if not all_vals:
        return 0.0
    grand_mean = _mean(all_vals)
    ss_between = sum(len(g) * (_mean(g) - grand_mean) ** 2 for g in groups if g)
    ss_total = sum((x - grand_mean) ** 2 for x in all_vals)
    return ss_between / ss_total if ss_total > 0 else 0.0


def _cohens_d(group1: list[float], group2: list[float]) -> float:
    """Cohen's d（Welch版）を計算。"""
    n1, n2 = len(group1), len(group2)
    if n1 < 2 or n2 < 2:
        return 0.0
    m1, m2 = _mean(group1), _mean(group2)
    v1, v2 = _var(group1), _var(group2)
    pooled_sd = math.sqrt(((n1 - 1) * v1 + (n2 - 1) * v2) / (n1 + n2 - 2))
    return (m2 - m1) / pooled_sd if pooled_sd > 0 else 0.0
```

---

## 11. YAML構成例

### 11.1 実験全体設定 (`configs/experiment.yaml`)

```yaml
# OrgBench 実験設定
phase: pilot  # "pilot" or "main"

templates:
  - configs/templates/anchor.yaml
  - configs/templates/flat_hub.yaml
  - configs/templates/matrix_hub.yaml
  - configs/templates/deep_mesh.yaml
  - configs/templates/flat_mesh.yaml
  - configs/templates/deep_finance.yaml
  - configs/templates/deep_tech.yaml
  - configs/templates/deep_noreview.yaml
  - configs/templates/homo_haiku.yaml
  - configs/templates/homo_gpt.yaml
  - configs/templates/single_agent.yaml

themes:
  - configs/themes/t01_ai_accounting.yaml
  - configs/themes/t02_legal_review.yaml
  - configs/themes/t03_gov_chatbot.yaml
  - configs/themes/t04_elderly_fitness.yaml
  - configs/themes/t05_insurance_ai.yaml

replications: 5
temperature: 0.7
timeout_sec: 600
```

### 11.2 テンプレート例：Anchor構成 (`configs/templates/anchor.yaml`)

```yaml
name: anchor
authority: deep
communication: hub
review: balanced
model_preset: hetero

agents:
  - name: ceo
    role: "最高経営責任者 - 全体統括・最終意思決定"
    model: "claude-haiku-4-5-20251001"
    prompt_file: "configs/prompts/ceo.md"
    manages: [tl]
    tools: []

  - name: tl
    role: "テクニカルリード - 調査・執筆の管理"
    model: "gpt-4o-mini"
    prompt_file: "configs/prompts/tl.md"
    reports_to: [ceo]
    manages: [researcher, writer]
    tools: []

  - name: researcher
    role: "リサーチャー - 市場調査・技術調査"
    model: "gemini/gemini-2.5-flash"
    prompt_file: "configs/prompts/researcher.md"
    reports_to: [tl]
    tools: [web_search]

  - name: writer
    role: "ライター - ビジネス提案の執筆"
    model: "gpt-4o-mini"
    prompt_file: "configs/prompts/writer.md"
    reports_to: [tl]
    tools: []

  - name: cfo
    role: "最高財務責任者 - 財務レビュー"
    model: "gpt-4o-mini"
    prompt_file: "configs/prompts/cfo.md"
    reports_to: [ceo]
    tools: []

  - name: cdo
    role: "最高技術責任者 - 技術レビュー"
    model: "gpt-4o-mini"
    prompt_file: "configs/prompts/cdo.md"
    reports_to: [ceo]
    tools: []

# 実行フロー（オーケストレータがこの順序で実行）
flow:
  - agent: ceo
    input_from: null          # テーマプロンプトを受け取る
    action: "テーマを分析し、Researcherへの調査指示とWriterへの執筆指示を生成してください"
    output_to: tl

  - agent: tl
    input_from: ceo
    action: "CEOの指示を具体的な調査タスクと執筆タスクに分解してください"
    output_to: researcher

  - agent: researcher
    input_from: tl
    action: "指示に基づき市場調査・技術調査・競合分析を実施してください。Web検索を活用してください"
    output_to: writer

  - agent: writer
    input_from: researcher
    action: "調査結果を基に、6セクション構成のビジネス提案ドラフトを作成してください"
    output_to: cfo

  - agent: cfo
    input_from: writer
    action: "ビジネス提案の財務面をレビューしてください。問題がなければ「APPROVED」、修正が必要なら具体的な指摘を記載してください"
    output_to: cdo
    gate: review_gate

  - agent: cdo
    input_from: writer
    action: "ビジネス提案の技術面をレビューしてください。問題がなければ「APPROVED」、修正が必要なら具体的な指摘を記載してください"
    output_to: ceo
    gate: review_gate

  - agent: ceo
    input_from: __all__
    action: "全メンバーの報告とレビュー結果を統合し、最終的なビジネス提案を完成させてください"
    output_to: null

max_review_rounds: 1
```

### 11.3 テンプレート例：Single-Agent (`configs/templates/single_agent.yaml`)

```yaml
name: single_agent
authority: null
communication: null
review: null
model_preset: null

agents:
  - name: single
    role: "統合エージェント - 全役割を1体で実行"
    model: "claude-haiku-4-5-20251001"
    prompt_file: "configs/prompts/single_agent.md"
    tools: [web_search]

flow:
  - agent: single
    input_from: null
    action: "以下のビジネステーマについて、市場調査→技術分析→財務分析→リスク評価→提案執筆→セルフレビューの順で、6セクション構成のビジネス提案を作成してください"
    output_to: null

max_review_rounds: 0
```

### 11.4 テンプレート例：Mesh構成 (`configs/templates/deep_mesh.yaml`)

```yaml
name: deep_mesh
authority: deep
communication: mesh        # ← Hubとの違い
review: balanced
model_preset: hetero

agents:
  - name: ceo
    role: "最高経営責任者"
    model: "claude-haiku-4-5-20251001"
    prompt_file: "configs/prompts/ceo.md"
    manages: [tl]
    peers: [cfo, cdo]       # ← Mesh: C-Suite同士がピア
    tools: []

  - name: tl
    role: "テクニカルリード"
    model: "gpt-4o-mini"
    prompt_file: "configs/prompts/tl.md"
    reports_to: [ceo]
    manages: [researcher, writer]
    peers: [cfo, cdo]       # ← Mesh: TLもレビュアーとピア
    tools: []

  - name: researcher
    role: "リサーチャー"
    model: "gemini/gemini-2.5-flash"
    prompt_file: "configs/prompts/researcher.md"
    reports_to: [tl]
    peers: [writer]          # ← Mesh: ワーカー同士がピア
    tools: [web_search]

  - name: writer
    role: "ライター"
    model: "gpt-4o-mini"
    prompt_file: "configs/prompts/writer.md"
    reports_to: [tl]
    peers: [researcher]      # ← Mesh
    tools: []

  - name: cfo
    role: "最高財務責任者"
    model: "gpt-4o-mini"
    prompt_file: "configs/prompts/cfo.md"
    reports_to: [ceo]
    peers: [cdo, tl]         # ← Mesh
    tools: []

  - name: cdo
    role: "最高技術責任者"
    model: "gpt-4o-mini"
    prompt_file: "configs/prompts/cdo.md"
    reports_to: [ceo]
    peers: [cfo, tl]         # ← Mesh
    tools: []

flow:
  # Hub構成と同一のフローだが、各ステップでピアの出力がコンテキストに自動注入される
  - agent: ceo
    input_from: null
    action: "テーマを分析し、調査・執筆の方針を策定してください"
    output_to: tl

  - agent: tl
    input_from: ceo
    action: "CEOの方針を具体タスクに分解してください"
    output_to: researcher

  - agent: researcher
    input_from: tl
    action: "市場調査・技術調査を実施してください。Web検索を活用してください"
    output_to: writer

  - agent: writer
    input_from: researcher
    action: "調査結果を基にビジネス提案ドラフトを作成してください"
    output_to: cfo

  - agent: cfo
    input_from: writer
    action: "財務面をレビューしてください。「APPROVED」または修正指摘を記載"
    output_to: cdo
    gate: review_gate

  - agent: cdo
    input_from: writer
    action: "技術面をレビューしてください。「APPROVED」または修正指摘を記載"
    output_to: ceo
    gate: review_gate

  - agent: ceo
    input_from: __all__
    action: "全報告とレビュー結果を統合し最終提案を完成させてください"
    output_to: null

max_review_rounds: 1
```

### 11.5 テーマ例 (`configs/themes/t01_ai_accounting.yaml`)

```yaml
id: t01_ai_accounting
title: "中小企業向けAI経理自動化"
domain: "FinTech"
uncertainty_group: "low"

task_prompt: |
  あなたは「中小企業向けAI経理自動化サービス」のビジネス提案を作成してください。

  以下の6セクションを必ず含めてください：

  1. **エグゼクティブサマリー**: 課題と提案ソリューション
  2. **市場分析**: ターゲット市場規模、競争環境、顧客セグメント
  3. **技術的アプローチ**: コア技術、開発ロードマップ、技術的リスク
  4. **財務予測**: 収益モデル、コスト構造、損益分岐点分析、3年間の予測
  5. **リスク評価**: 市場・技術・財務・規制リスクと緩和策
  6. **実施計画**: マイルストーン、必要リソース、タイムライン

  具体的な数値、固有名詞、実在する競合企業名を可能な限り含めてください。

search_queries:
  - "中小企業 AI 経理自動化 市場規模"
  - "AI accounting automation SME business model"
  - "freee マネーフォワード 競合分析"
  - "AI bookkeeping technology stack"
  - "経理自動化 規制 電子帳簿保存法"
```

---

## 12. エントリポイント

```python
# orgbench/__main__.py
"""
使用方法:
  python -m orgbench pilot          # パイロット実行
  python -m orgbench main           # 本実験実行
  python -m orgbench judge          # 評価のみ実行
  python -m orgbench analyze        # 分析のみ実行
"""
import asyncio
import sys

from .runner import run_experiment
from .analysis import manipulation_check, estimate_effect_sizes


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m orgbench [pilot|main|judge|analyze]")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "pilot":
        asyncio.run(run_experiment(
            experiment_yaml="configs/experiment.yaml",
            phase="pilot",
        ))
    elif cmd == "main":
        asyncio.run(run_experiment(
            experiment_yaml="configs/experiment_main.yaml",
            phase="main",
        ))
    elif cmd == "analyze":
        print("=== 操作チェック ===")
        mc = manipulation_check()
        print(f"  {mc}")
        print("\n=== 効果量推定 ===")
        es = estimate_effect_sizes()
        for dim, vals in es.items():
            if isinstance(vals, dict):
                print(f"  {dim}: η²={vals['eta_squared']:.4f}, "
                      f"d(single vs best)={vals['cohens_d_single_vs_best']:.4f}")
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
```

---

## 13. 依存関係 (`pyproject.toml`)

```toml
[project]
name = "orgbench"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "litellm>=1.40",
    "tavily-python>=0.3",
    "pyyaml>=6.0",
    "aiofiles>=23.0",
]

[project.optional-dependencies]
analysis = [
    "pandas>=2.0",
    "scipy>=1.11",
    "matplotlib>=3.8",
    "seaborn>=0.13",
]

[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.backends._legacy:_Backend"
```

---

## 14. 実装優先順位

| 優先度 | モジュール | 工数 | 依存 |
|--------|----------|------|------|
| **1** | `models.py` | 0.5日 | なし |
| **2** | `llm.py` | 0.5日 | models |
| **3** | `tools.py` | 0.5日 | なし |
| **4** | `config_loader.py` | 0.5日 | models |
| **5** | `agents.py` | 1日 | llm, tools, models |
| **6** | `orchestrator.py` | 1.5日 | agents, models |
| **7** | `runner.py` | 1日 | orchestrator, config_loader |
| **8** | YAML構成11種 + プロンプト7種 + テーマ5種 | 1.5日 | — |
| **9** | `judge.py` | 0.5日 | llm |
| **10** | `analysis.py` | 1日 | — |
| | **合計** | **~8.5日** | |

**クリティカルパス:** models → llm → agents → orchestrator → runner → YAML構成 → パイロット実行

---

*End of Detailed Design v1.0*
