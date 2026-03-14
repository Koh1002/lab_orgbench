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
    """Cohen's d（pooled SD版）を計算。"""
    n1, n2 = len(group1), len(group2)
    if n1 < 2 or n2 < 2:
        return 0.0
    m1, m2 = _mean(group1), _mean(group2)
    v1, v2 = _var(group1), _var(group2)
    pooled_sd = math.sqrt(((n1 - 1) * v1 + (n2 - 1) * v2) / (n1 + n2 - 2))
    return (m2 - m1) / pooled_sd if pooled_sd > 0 else 0.0
