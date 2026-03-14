"""analysis.py のテスト — 統計計算の正確性、操作チェック、効果量推定"""
from __future__ import annotations
import json
import csv
import math
import pytest
from pathlib import Path
from unittest.mock import patch

from orgbench.analysis import (
    manipulation_check, estimate_effect_sizes,
    _mean, _var, _compute_eta_squared, _cohens_d,
    RESULTS_DIR,
)


# ============================================================
# _mean のテスト
# ============================================================

class TestMean:
    def test_basic(self):
        assert _mean([1, 2, 3, 4, 5]) == pytest.approx(3.0)

    def test_single(self):
        assert _mean([42]) == pytest.approx(42.0)

    def test_empty(self):
        assert _mean([]) == 0.0

    def test_floats(self):
        assert _mean([1.5, 2.5, 3.5]) == pytest.approx(2.5)

    def test_negative(self):
        assert _mean([-1, 0, 1]) == pytest.approx(0.0)

    def test_all_same(self):
        assert _mean([4.0, 4.0, 4.0]) == pytest.approx(4.0)


# ============================================================
# _var のテスト
# ============================================================

class TestVar:
    def test_basic(self):
        """不偏分散の確認: [1,2,3,4,5] → var = 2.5"""
        assert _var([1, 2, 3, 4, 5]) == pytest.approx(2.5)

    def test_single_element(self):
        """1要素 → len < 2 → 0.0"""
        assert _var([42]) == pytest.approx(0.0)

    def test_empty(self):
        assert _var([]) == pytest.approx(0.0)

    def test_all_same(self):
        assert _var([3.0, 3.0, 3.0]) == pytest.approx(0.0)

    def test_two_elements(self):
        """[1, 3] → mean=2, var = ((1-2)²+(3-2)²)/(2-1) = 2.0"""
        assert _var([1, 3]) == pytest.approx(2.0)

    def test_known_values(self):
        """[2, 4, 4, 4, 5, 5, 7, 9] → 不偏分散 = 4.571..."""
        data = [2, 4, 4, 4, 5, 5, 7, 9]
        expected = sum((x - 5) ** 2 for x in data) / 7  # mean=5
        assert _var(data) == pytest.approx(expected)


# ============================================================
# _compute_eta_squared のテスト
# ============================================================

class TestComputeEtaSquared:
    def test_no_difference(self):
        """全グループ同値 → η² = 0"""
        groups = [[3, 3, 3], [3, 3, 3], [3, 3, 3]]
        assert _compute_eta_squared(groups) == pytest.approx(0.0)

    def test_complete_separation(self):
        """完全分離: 各グループ内分散=0 → η² = 1"""
        groups = [[1, 1, 1], [5, 5, 5], [9, 9, 9]]
        assert _compute_eta_squared(groups) == pytest.approx(1.0)

    def test_known_value(self):
        """手計算で確認可能なケース"""
        # Group A: [1, 2, 3] mean=2
        # Group B: [4, 5, 6] mean=5
        # Grand mean = 3.5
        # SS_between = 3*(2-3.5)² + 3*(5-3.5)² = 3*2.25 + 3*2.25 = 13.5
        # SS_total = Σ(xi - 3.5)² = 2.5²+1.5²+0.5²+0.5²+1.5²+2.5² = 17.5
        # η² = 13.5/17.5 ≈ 0.7714
        groups = [[1, 2, 3], [4, 5, 6]]
        eta = _compute_eta_squared(groups)
        assert eta == pytest.approx(13.5 / 17.5, rel=1e-4)

    def test_empty_groups(self):
        assert _compute_eta_squared([]) == pytest.approx(0.0)

    def test_single_group(self):
        """1グループ → SS_between = 0 → η² = 0"""
        groups = [[1, 2, 3, 4, 5]]
        assert _compute_eta_squared(groups) == pytest.approx(0.0)

    def test_unequal_group_sizes(self):
        """異なるグループサイズ"""
        groups = [[1, 2], [5, 6, 7, 8]]
        eta = _compute_eta_squared(groups)
        assert 0 <= eta <= 1

    def test_result_bounded_0_1(self):
        """η² は 0 ≤ η² ≤ 1"""
        import random
        random.seed(42)
        for _ in range(20):
            n_groups = random.randint(2, 5)
            groups = [[random.uniform(1, 5) for _ in range(random.randint(3, 10))]
                      for _ in range(n_groups)]
            eta = _compute_eta_squared(groups)
            assert 0 <= eta <= 1 + 1e-10


# ============================================================
# _cohens_d のテスト
# ============================================================

class TestCohensD:
    def test_identical_groups(self):
        """同一グループ → d = 0"""
        assert _cohens_d([3, 3, 3], [3, 3, 3]) == pytest.approx(0.0)

    def test_positive_effect(self):
        """group2 > group1 → d > 0"""
        d = _cohens_d([1, 2, 3], [4, 5, 6])
        assert d > 0

    def test_negative_effect(self):
        """group2 < group1 → d < 0"""
        d = _cohens_d([4, 5, 6], [1, 2, 3])
        assert d < 0

    def test_small_groups(self):
        """各グループ1要素 → 0.0"""
        assert _cohens_d([1], [5]) == pytest.approx(0.0)

    def test_known_value(self):
        """手計算:
        g1=[1,2,3] mean=2, var=1
        g2=[4,5,6] mean=5, var=1
        pooled_sd = sqrt((2*1 + 2*1)/4) = 1.0
        d = (5-2)/1.0 = 3.0
        """
        d = _cohens_d([1, 2, 3], [4, 5, 6])
        assert d == pytest.approx(3.0)

    def test_zero_variance(self):
        """分散0のグループ → pooled_sd=0 → d=0"""
        d = _cohens_d([5, 5], [5, 5])
        assert d == pytest.approx(0.0)

    def test_large_effect_size(self):
        """大きな効果量（d > 0.8 = large effect）"""
        # 分散が0だとpooled_sd=0 → d=0。ばらつきを少し入れる
        d = _cohens_d([1, 1.1, 0.9, 1], [5, 5.1, 4.9, 5])
        assert abs(d) > 0.8

    def test_symmetry(self):
        """d(g1, g2) = -d(g2, g1)"""
        d1 = _cohens_d([1, 2, 3], [4, 5, 6])
        d2 = _cohens_d([4, 5, 6], [1, 2, 3])
        assert d1 == pytest.approx(-d2)


# ============================================================
# manipulation_check のテスト
# ============================================================

class TestManipulationCheck:
    def test_basic(self, tmp_path):
        """基本的な操作チェック実行"""
        runs_dir = tmp_path / "runs"
        run1 = runs_dir / "anchor_t01_rep1"
        run1.mkdir(parents=True)

        meta = {"config_name": "anchor", "theme_id": "t01", "replication": 1}
        (run1 / "run_meta.json").write_text(json.dumps(meta))

        messages = [
            {"from_agent": "theme", "to_agent": "ceo", "msg_type": "delegate_task", "content": "x"},
            {"from_agent": "ceo", "to_agent": "writer", "msg_type": "task_result", "content": "y"},
            {"from_agent": "writer", "to_agent": "cfo", "msg_type": "delegate_task", "content": "z"},
            {"from_agent": "cfo", "to_agent": "writer", "msg_type": "task_result", "content": "w"},
        ]
        with open(run1 / "messages.jsonl", "w") as f:
            for m in messages:
                f.write(json.dumps(m) + "\n")

        (tmp_path / "analysis").mkdir(parents=True, exist_ok=True)

        with patch("orgbench.analysis.RESULTS_DIR", tmp_path):
            result = manipulation_check()

        assert result["total_runs"] == 1
        # CSV出力の確認
        csv_path = tmp_path / "analysis" / "manipulation_check.csv"
        assert csv_path.exists()

        with open(csv_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 1
        assert rows[0]["config"] == "anchor"
        assert int(rows[0]["message_count"]) == 4
        assert int(rows[0]["unique_edges"]) >= 2  # ユニークなエッジが存在

    def test_multiple_runs(self, tmp_path):
        """複数実行の操作チェック"""
        runs_dir = tmp_path / "runs"
        for config in ["anchor", "flat_hub"]:
            run_dir = runs_dir / f"{config}_t01_rep1"
            run_dir.mkdir(parents=True)
            (run_dir / "run_meta.json").write_text(json.dumps({"config_name": config}))
            messages = [
                {"from_agent": "a", "to_agent": "b", "msg_type": "delegate_task", "content": "x"},
            ]
            with open(run_dir / "messages.jsonl", "w") as f:
                for m in messages:
                    f.write(json.dumps(m) + "\n")

        (tmp_path / "analysis").mkdir(parents=True, exist_ok=True)

        with patch("orgbench.analysis.RESULTS_DIR", tmp_path):
            result = manipulation_check()

        assert result["total_runs"] == 2

    def test_review_messages_counted(self, tmp_path):
        """レビューメッセージが正しくカウントされる"""
        runs_dir = tmp_path / "runs"
        run1 = runs_dir / "test_rep1"
        run1.mkdir(parents=True)

        (run1 / "run_meta.json").write_text(json.dumps({"config_name": "test"}))
        messages = [
            {"from_agent": "writer", "to_agent": "cfo", "msg_type": "review_request", "content": "x"},
            {"from_agent": "cfo", "to_agent": "writer", "msg_type": "review_response", "content": "y"},
            {"from_agent": "a", "to_agent": "b", "msg_type": "delegate_task", "content": "z"},
        ]
        with open(run1 / "messages.jsonl", "w") as f:
            for m in messages:
                f.write(json.dumps(m) + "\n")

        (tmp_path / "analysis").mkdir(parents=True, exist_ok=True)

        with patch("orgbench.analysis.RESULTS_DIR", tmp_path):
            result = manipulation_check()

        csv_path = tmp_path / "analysis" / "manipulation_check.csv"
        with open(csv_path, encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        assert int(rows[0]["review_messages"]) == 2

    def test_empty_runs(self, tmp_path):
        """実行結果がない場合"""
        (tmp_path / "runs").mkdir(parents=True)
        (tmp_path / "analysis").mkdir(parents=True, exist_ok=True)

        with patch("orgbench.analysis.RESULTS_DIR", tmp_path):
            result = manipulation_check()

        assert result["total_runs"] == 0


# ============================================================
# estimate_effect_sizes のテスト
# ============================================================

class TestEstimateEffectSizes:
    def _write_scores_csv(self, tmp_path, rows):
        """ヘルパー: scores.csvを書き込む"""
        judge_dir = tmp_path / "judge"
        judge_dir.mkdir(parents=True, exist_ok=True)
        (tmp_path / "analysis").mkdir(parents=True, exist_ok=True)

        fields = [
            "config_name", "theme_id", "replication", "judge_run",
            "feasibility", "novelty", "market_insight",
            "financial_rigor", "technical_depth", "overall_quality",
            "rationale",
        ]
        with open(judge_dir / "scores.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            for row in rows:
                writer.writerow(row)

    def test_basic_effect_sizes(self, tmp_path):
        """基本的な効果量計算"""
        rows = []
        # anchor: 高スコア（ばらつきあり）
        import random
        random.seed(42)
        for i in range(5):
            rows.append({
                "config_name": "anchor", "theme_id": "t01", "replication": i+1,
                "judge_run": 1,
                "feasibility": 4 + random.uniform(-0.3, 0.3),
                "novelty": 4, "market_insight": 4,
                "financial_rigor": 4, "technical_depth": 4, "overall_quality": 4,
                "rationale": "good",
            })
        # single_agent: 低スコア（ばらつきあり）
        for i in range(5):
            rows.append({
                "config_name": "single_agent", "theme_id": "t01", "replication": i+1,
                "judge_run": 1,
                "feasibility": 2 + random.uniform(-0.3, 0.3),
                "novelty": 2, "market_insight": 2,
                "financial_rigor": 2, "technical_depth": 2, "overall_quality": 2,
                "rationale": "poor",
            })

        self._write_scores_csv(tmp_path, rows)

        with patch("orgbench.analysis.RESULTS_DIR", tmp_path):
            results = estimate_effect_sizes()

        assert "feasibility" in results
        # anchor=4, single=2 → 明確な差がある
        assert results["feasibility"]["eta_squared"] > 0.5
        assert results["feasibility"]["cohens_d_single_vs_best"] > 0

        # CSV出力の確認
        csv_path = tmp_path / "analysis" / "effect_sizes.csv"
        assert csv_path.exists()

    def test_no_single_agent(self, tmp_path):
        """single_agentが含まれない場合、Cohen's d = 0"""
        rows = []
        for config in ["anchor", "flat_hub"]:
            for i in range(3):
                rows.append({
                    "config_name": config, "theme_id": "t01", "replication": i+1,
                    "judge_run": 1,
                    "feasibility": 3, "novelty": 3, "market_insight": 3,
                    "financial_rigor": 3, "technical_depth": 3, "overall_quality": 3,
                    "rationale": "",
                })

        self._write_scores_csv(tmp_path, rows)

        with patch("orgbench.analysis.RESULTS_DIR", tmp_path):
            results = estimate_effect_sizes()

        assert results["feasibility"]["cohens_d_single_vs_best"] == 0.0

    def test_missing_scores_file(self, tmp_path):
        """scores.csvが存在しない場合"""
        with patch("orgbench.analysis.RESULTS_DIR", tmp_path):
            results = estimate_effect_sizes()

        assert "error" in results

    def test_all_configs_same_score(self, tmp_path):
        """全構成が同じスコア → η² = 0"""
        rows = []
        for config in ["anchor", "flat_hub", "single_agent"]:
            for i in range(5):
                rows.append({
                    "config_name": config, "theme_id": "t01", "replication": i+1,
                    "judge_run": 1,
                    "feasibility": 3, "novelty": 3, "market_insight": 3,
                    "financial_rigor": 3, "technical_depth": 3, "overall_quality": 3,
                    "rationale": "",
                })

        self._write_scores_csv(tmp_path, rows)

        with patch("orgbench.analysis.RESULTS_DIR", tmp_path):
            results = estimate_effect_sizes()

        assert results["feasibility"]["eta_squared"] == pytest.approx(0.0)
        assert results["feasibility"]["cohens_d_single_vs_best"] == pytest.approx(0.0)

    def test_effect_size_csv_output(self, tmp_path):
        """効果量CSVの出力フォーマット検証"""
        rows = []
        for config in ["anchor", "single_agent"]:
            for i in range(3):
                rows.append({
                    "config_name": config, "theme_id": "t01", "replication": i+1,
                    "judge_run": 1,
                    "feasibility": 4 if config == "anchor" else 2,
                    "novelty": 3, "market_insight": 3, "financial_rigor": 3,
                    "technical_depth": 3, "overall_quality": 3, "rationale": "",
                })

        self._write_scores_csv(tmp_path, rows)

        with patch("orgbench.analysis.RESULTS_DIR", tmp_path):
            estimate_effect_sizes()

        csv_path = tmp_path / "analysis" / "effect_sizes.csv"
        with open(csv_path, encoding="utf-8") as f:
            reader = csv.reader(f)
            headers = next(reader)
            rows_out = list(reader)

        assert headers == ["dimension", "eta_squared", "cohens_d_single_vs_best"]
        assert len(rows_out) == 6  # 6次元
        dims = [r[0] for r in rows_out]
        assert "feasibility" in dims
        assert "overall_quality" in dims
