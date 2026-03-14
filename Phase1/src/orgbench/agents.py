"""エージェント: LLM呼び出し + 応答解析。状態は持たない純粋関数的設計。"""
from __future__ import annotations
import json
from .models import AgentDef, LLMCall
from .llm import call_llm
from .tools import search_web


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
            tools=tools,  # 全ラウンドでtools指定（履歴にtool_useがあるとAnthropicが要求）
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

        # tool結果をメッセージに追加（litellmが各プロバイダ形式に変換できるよう、
        # OpenAI形式のtool_callsオブジェクトを使用）
        raw_tool_calls = call_log.metadata.get("raw_tool_calls")
        if raw_tool_calls:
            # litellmの元オブジェクトをそのまま使用
            assistant_msg = {"role": "assistant", "content": None, "tool_calls": raw_tool_calls}
        else:
            # フォールバック
            assistant_msg = {"role": "assistant", "content": text}
        messages.append(assistant_msg)
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
