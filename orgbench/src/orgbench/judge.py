"""LLM-as-Judge 評価パイプライン"""
from __future__ import annotations
import asyncio
import json
import re
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
        max_tokens=4096,
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
