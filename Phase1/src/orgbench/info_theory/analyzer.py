"""
Phase 1 バッチ分析: step_traces.jsonl から情報理論的指標を計算。

使い方:
    python -m orgbench.info_theory.analyzer --results-dir results/runs
"""
from __future__ import annotations
import json
import csv
from pathlib import Path
from collections import defaultdict
from .metrics import (
    compression_ratio, information_density, numerical_fidelity,
    extract_numbers, Tracer, tracer_survival,
)


def analyze_run_traces(run_dir: Path) -> dict | None:
    """1回の実行の step_traces.jsonl を分析。"""
    traces_path = run_dir / "step_traces.jsonl"
    meta_path = run_dir / "run_meta.json"

    if not traces_path.exists():
        return None

    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}

    traces = []
    with open(traces_path, encoding="utf-8") as f:
        for line in f:
            traces.append(json.loads(line))

    if not traces:
        return None

    # 各ステップの指標計算
    step_results = []
    first_input = traces[0]["input_text"] if traces else ""

    for t in traces:
        cr = compression_ratio(t["input_tokens"], t["output_tokens"])
        id_val = information_density(t["output_text"])
        nf = numerical_fidelity(t["input_text"], t["output_text"])

        step_results.append({
            "step_index": t["step_index"],
            "agent": t["agent"],
            "role": t["role"],
            "compression_ratio": cr,
            "information_density": id_val,
            "numerical_fidelity": nf,
            "input_tokens": t["input_tokens"],
            "output_tokens": t["output_tokens"],
        })

    return {
        "run": run_dir.name,
        "config": meta.get("config_name", ""),
        "theme_id": meta.get("theme_id", ""),
        "replication": meta.get("replication", 0),
        "steps": step_results,
        "n_steps": len(traces),
    }


def analyze_tracer_run(run_dir: Path, tracers: list[Tracer]) -> dict | None:
    """トレーサー付き実行の各ステップでのトレーサー生存率を計算。"""
    traces_path = run_dir / "step_traces.jsonl"
    if not traces_path.exists():
        return None

    meta_path = run_dir / "run_meta.json"
    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}

    traces = []
    with open(traces_path, encoding="utf-8") as f:
        for line in f:
            traces.append(json.loads(line))

    step_survivals = []
    for t in traces:
        rate, per_tracer = tracer_survival(t["output_text"], tracers)
        step_survivals.append({
            "step_index": t["step_index"],
            "agent": t["agent"],
            "survival_rate": rate,
            "per_tracer": per_tracer,
        })

    # 最終出力でのトレーサー生存
    final_output_path = run_dir / "output.md"
    if final_output_path.exists():
        final_text = final_output_path.read_text(encoding="utf-8")
        final_rate, final_per = tracer_survival(final_text, tracers)
    else:
        final_rate = step_survivals[-1]["survival_rate"] if step_survivals else 0.0
        final_per = step_survivals[-1]["per_tracer"] if step_survivals else []

    return {
        "run": run_dir.name,
        "config": meta.get("config_name", ""),
        "theme_id": meta.get("theme_id", ""),
        "step_survivals": step_survivals,
        "final_survival_rate": final_rate,
        "final_per_tracer": final_per,
    }


def batch_analyze(results_dir: Path, output_dir: Path) -> None:
    """全実行を分析し、CSVに出力。"""
    output_dir.mkdir(parents=True, exist_ok=True)

    # ステップ別指標
    rows = []
    for run_dir in sorted(results_dir.iterdir()):
        if not run_dir.is_dir():
            continue
        result = analyze_run_traces(run_dir)
        if result is None:
            continue
        for s in result["steps"]:
            rows.append({
                "run": result["run"],
                "config": result["config"],
                "theme_id": result["theme_id"],
                **s,
            })

    if rows:
        out_path = output_dir / "step_metrics.csv"
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        print(f"Wrote {len(rows)} step metrics to {out_path}")
    else:
        print("No step_traces.jsonl found in any run directory.")
