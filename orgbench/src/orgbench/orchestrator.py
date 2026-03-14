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
        if template.communication and template.communication.value == "mesh" and agent_def.peers:
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
                # 差し戻し: 元のエージェントを再実行（1回だけ）
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
    return "approved" in lower or "承認" in lower
