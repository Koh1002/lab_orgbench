"""LLM呼び出しラッパー（litellm + コスト追跡）"""
from __future__ import annotations
import asyncio
import time
import litellm
from datetime import datetime
from .models import LLMCall

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

            # tool_callsがある場合は元のtool_callsオブジェクトもmetadataに保存
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
                call_log.metadata = {
                    "tool_calls": True,
                    "raw_tool_calls": choice.message.tool_calls,
                }

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
