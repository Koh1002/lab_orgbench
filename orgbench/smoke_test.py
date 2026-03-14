"""スモークテスト: シングルエージェント1回だけ実行して動作確認"""
import asyncio
import os
import sys

# GOOGLE_API_KEY → GEMINI_API_KEY のエイリアス
if os.environ.get("GOOGLE_API_KEY") and not os.environ.get("GEMINI_API_KEY"):
    os.environ["GEMINI_API_KEY"] = os.environ["GOOGLE_API_KEY"]

sys.path.insert(0, "src")

from orgbench.config_loader import load_experiment
from orgbench.orchestrator import run_single


async def main():
    exp = load_experiment("configs/experiment_smoke.yaml")
    tmpl = exp["templates"][0]
    theme = exp["themes"][0]

    print(f"=== Smoke Test ===")
    print(f"構成: {tmpl.name}")
    print(f"テーマ: {theme.title}")
    print(f"エージェント数: {len(tmpl.agents)}")
    print(f"モデル: {tmpl.agents[0].model}")
    print(f"ツール: {tmpl.agents[0].tools}")
    print()

    result = await run_single(
        template=tmpl,
        theme=theme,
        replication=1,
        temperature=0.7,
        timeout_sec=300,
    )

    print(f"--- 結果 ---")
    print(f"LLM呼び出し数: {result.total_llm_calls}")
    print(f"入力トークン: {result.total_input_tokens}")
    print(f"出力トークン: {result.total_output_tokens}")
    print(f"コスト: ${result.total_cost_usd:.4f}")
    print(f"所要時間: {result.total_duration_sec:.1f}s")
    print(f"タイムアウト: {result.timeout}")
    print(f"エラー: {result.error}")
    print(f"\n--- 出力テキスト（先頭500文字）---")
    print(result.output_text[:500])
    print(f"\n... (全{len(result.output_text)}文字)")

    print(f"\n--- メッセージログ ---")
    for msg in result.messages:
        print(f"  {msg.from_agent} → {msg.to_agent} [{msg.msg_type.value}]: {msg.content[:80]}")

    print(f"\n--- LLM呼び出しログ ---")
    for call in result.llm_calls:
        print(f"  {call.agent} ({call.model}): {call.input_tokens}in/{call.output_tokens}out "
              f"${call.cost_usd:.4f} {call.duration_ms}ms")


if __name__ == "__main__":
    asyncio.run(main())
