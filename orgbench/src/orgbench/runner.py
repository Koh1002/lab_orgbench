"""実験ランナー: バッチ実行制御、進捗表示、結果永続化"""
from __future__ import annotations
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
    phase: str = "pilot",
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
