"""runner.py のテスト — 結果保存/読込、冪等スキップ、メタデータ復元"""
from __future__ import annotations
import json
import csv
import pytest
from pathlib import Path
from datetime import datetime
from dataclasses import asdict
from unittest.mock import patch

from orgbench.runner import _save_result, _save_scores, _run_dir, _meta_to_stub, RESULTS_DIR
from orgbench.models import (
    RunResult, Message, MessageType, LLMCall, JudgeScore,
)


# ============================================================
# _run_dir のテスト
# ============================================================

class TestRunDir:
    def test_format(self):
        d = _run_dir("anchor", "t01_ai_accounting", 3)
        assert d == RESULTS_DIR / "runs" / "anchor_t01_ai_accounting_rep3"

    def test_different_reps(self):
        d1 = _run_dir("anchor", "t01", 1)
        d2 = _run_dir("anchor", "t01", 2)
        assert d1 != d2

    def test_different_configs(self):
        d1 = _run_dir("anchor", "t01", 1)
        d2 = _run_dir("flat_hub", "t01", 1)
        assert d1 != d2


# ============================================================
# _save_result のテスト
# ============================================================

class TestSaveResult:
    def test_saves_output_md(self, tmp_path):
        result = RunResult(
            config_name="test_cfg", theme_id="t01", replication=1,
            output_text="# テスト提案\n\n内容", messages=[], llm_calls=[],
            total_cost_usd=0.01, total_duration_sec=5.0,
            total_llm_calls=3, total_input_tokens=1000, total_output_tokens=500,
        )
        with patch("orgbench.runner.RESULTS_DIR", tmp_path):
            _save_result(result)

        run_dir = tmp_path / "runs" / "test_cfg_t01_rep1"
        assert (run_dir / "output.md").exists()
        assert (run_dir / "output.md").read_text(encoding="utf-8") == "# テスト提案\n\n内容"

    def test_saves_meta_json(self, tmp_path):
        result = RunResult(
            config_name="test_cfg", theme_id="t01", replication=1,
            output_text="out", messages=[], llm_calls=[],
            total_cost_usd=0.01, total_duration_sec=5.0,
            total_llm_calls=3, total_input_tokens=1000, total_output_tokens=500,
            timeout=False, error=None,
        )
        with patch("orgbench.runner.RESULTS_DIR", tmp_path):
            _save_result(result)

        run_dir = tmp_path / "runs" / "test_cfg_t01_rep1"
        meta = json.loads((run_dir / "run_meta.json").read_text())
        assert meta["config_name"] == "test_cfg"
        assert meta["theme_id"] == "t01"
        assert meta["replication"] == 1
        assert meta["total_cost_usd"] == 0.01
        assert meta["total_llm_calls"] == 3
        assert meta["timeout"] is False
        assert meta["error"] is None
        assert "timestamp" in meta

    def test_saves_messages_jsonl(self, tmp_path):
        messages = [
            Message("ceo", "writer", MessageType.DELEGATE_TASK, "指示内容"),
            Message("writer", "ceo", MessageType.TASK_RESULT, "提案内容"),
        ]
        result = RunResult(
            config_name="test_cfg", theme_id="t01", replication=1,
            output_text="out", messages=messages, llm_calls=[],
            total_cost_usd=0, total_duration_sec=0,
            total_llm_calls=0, total_input_tokens=0, total_output_tokens=0,
        )
        with patch("orgbench.runner.RESULTS_DIR", tmp_path):
            _save_result(result)

        run_dir = tmp_path / "runs" / "test_cfg_t01_rep1"
        lines = (run_dir / "messages.jsonl").read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 2
        msg0 = json.loads(lines[0])
        assert msg0["from_agent"] == "ceo"
        assert msg0["msg_type"] == "delegate_task"

    def test_saves_llm_calls_jsonl(self, tmp_path):
        llm_calls = [
            LLMCall(
                agent="ceo", model="gpt-4o-mini",
                input_tokens=100, output_tokens=50,
                cost_usd=0.001, duration_ms=500,
                timestamp=datetime.now(), purpose="test",
                prompt_summary="prompt", response_summary="response",
            ),
        ]
        result = RunResult(
            config_name="test_cfg", theme_id="t01", replication=1,
            output_text="out", messages=[], llm_calls=llm_calls,
            total_cost_usd=0.001, total_duration_sec=0.5,
            total_llm_calls=1, total_input_tokens=100, total_output_tokens=50,
        )
        with patch("orgbench.runner.RESULTS_DIR", tmp_path):
            _save_result(result)

        run_dir = tmp_path / "runs" / "test_cfg_t01_rep1"
        lines = (run_dir / "llm_calls.jsonl").read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 1
        call0 = json.loads(lines[0])
        assert call0["agent"] == "ceo"
        assert call0["cost_usd"] == 0.001

    def test_creates_directories(self, tmp_path):
        """存在しないディレクトリが自動作成される"""
        result = RunResult(
            config_name="new_cfg", theme_id="new_theme", replication=99,
            output_text="out", messages=[], llm_calls=[],
            total_cost_usd=0, total_duration_sec=0,
            total_llm_calls=0, total_input_tokens=0, total_output_tokens=0,
        )
        with patch("orgbench.runner.RESULTS_DIR", tmp_path):
            _save_result(result)

        assert (tmp_path / "runs" / "new_cfg_new_theme_rep99").is_dir()

    def test_overwrites_existing(self, tmp_path):
        """既存結果を上書きする"""
        result1 = RunResult(
            config_name="cfg", theme_id="t01", replication=1,
            output_text="first", messages=[], llm_calls=[],
            total_cost_usd=0.01, total_duration_sec=1,
            total_llm_calls=1, total_input_tokens=100, total_output_tokens=50,
        )
        result2 = RunResult(
            config_name="cfg", theme_id="t01", replication=1,
            output_text="second", messages=[], llm_calls=[],
            total_cost_usd=0.02, total_duration_sec=2,
            total_llm_calls=2, total_input_tokens=200, total_output_tokens=100,
        )
        with patch("orgbench.runner.RESULTS_DIR", tmp_path):
            _save_result(result1)
            _save_result(result2)

        run_dir = tmp_path / "runs" / "cfg_t01_rep1"
        assert (run_dir / "output.md").read_text(encoding="utf-8") == "second"

    def test_error_result_saved(self, tmp_path):
        """エラー結果も正常に保存される"""
        result = RunResult(
            config_name="cfg", theme_id="t01", replication=1,
            output_text="", messages=[], llm_calls=[],
            total_cost_usd=0, total_duration_sec=0,
            total_llm_calls=0, total_input_tokens=0, total_output_tokens=0,
            timeout=True, error="Timeout after 600s",
        )
        with patch("orgbench.runner.RESULTS_DIR", tmp_path):
            _save_result(result)

        run_dir = tmp_path / "runs" / "cfg_t01_rep1"
        meta = json.loads((run_dir / "run_meta.json").read_text())
        assert meta["timeout"] is True
        assert meta["error"] == "Timeout after 600s"

    def test_japanese_content_saved(self, tmp_path):
        """日本語コンテンツが正しくUTF-8で保存される"""
        result = RunResult(
            config_name="cfg", theme_id="t01", replication=1,
            output_text="# ビジネス提案\n\n日本語のテスト内容🎉",
            messages=[Message("ceo", "writer", MessageType.DELEGATE_TASK, "日本語指示")],
            llm_calls=[], total_cost_usd=0, total_duration_sec=0,
            total_llm_calls=0, total_input_tokens=0, total_output_tokens=0,
        )
        with patch("orgbench.runner.RESULTS_DIR", tmp_path):
            _save_result(result)

        run_dir = tmp_path / "runs" / "cfg_t01_rep1"
        content = (run_dir / "output.md").read_text(encoding="utf-8")
        assert "ビジネス提案" in content
        assert "🎉" in content


# ============================================================
# _save_scores のテスト
# ============================================================

class TestSaveScores:
    def test_basic_csv_output(self, tmp_path):
        scores = [
            JudgeScore("anchor", "t01", 1, 1, 4.0, 3.0, 5.0, 2.0, 4.0, 3.5, "good"),
            JudgeScore("anchor", "t01", 1, 2, 3.5, 3.5, 4.0, 3.0, 3.5, 3.5, "ok"),
        ]
        with patch("orgbench.runner.RESULTS_DIR", tmp_path):
            _save_scores(scores)

        csv_path = tmp_path / "judge" / "scores.csv"
        assert csv_path.exists()

        with open(csv_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 2
        assert rows[0]["config_name"] == "anchor"
        assert float(rows[0]["feasibility"]) == 4.0
        assert rows[1]["rationale"] == "ok"

    def test_csv_headers(self, tmp_path):
        scores = [JudgeScore("cfg", "t01", 1, 1, 3, 3, 3, 3, 3, 3, "test")]
        with patch("orgbench.runner.RESULTS_DIR", tmp_path):
            _save_scores(scores)

        csv_path = tmp_path / "judge" / "scores.csv"
        with open(csv_path, encoding="utf-8") as f:
            reader = csv.reader(f)
            headers = next(reader)

        expected = [
            "config_name", "theme_id", "replication", "judge_run",
            "feasibility", "novelty", "market_insight",
            "financial_rigor", "technical_depth", "overall_quality",
            "rationale",
        ]
        assert headers == expected

    def test_empty_scores(self, tmp_path):
        """空のスコアリストでもCSVが作成される（ヘッダのみ）"""
        with patch("orgbench.runner.RESULTS_DIR", tmp_path):
            _save_scores([])

        csv_path = tmp_path / "judge" / "scores.csv"
        assert csv_path.exists()
        with open(csv_path, encoding="utf-8") as f:
            lines = f.readlines()
        assert len(lines) == 1  # ヘッダのみ


# ============================================================
# _meta_to_stub のテスト
# ============================================================

class TestMetaToStub:
    def test_basic_restoration(self, tmp_path):
        """メタデータからRunResultスタブを復元"""
        run_dir = tmp_path / "runs" / "anchor_t01_rep1"
        run_dir.mkdir(parents=True)
        (run_dir / "output.md").write_text("復元されたテキスト", encoding="utf-8")

        meta = {
            "config_name": "anchor",
            "theme_id": "t01",
            "replication": 1,
            "total_cost_usd": 0.05,
            "total_duration_sec": 10.0,
            "total_llm_calls": 7,
            "total_input_tokens": 5000,
            "total_output_tokens": 2000,
            "timeout": False,
            "error": None,
        }

        with patch("orgbench.runner.RESULTS_DIR", tmp_path):
            stub = _meta_to_stub(meta)

        assert stub.config_name == "anchor"
        assert stub.output_text == "復元されたテキスト"
        assert stub.total_cost_usd == 0.05
        assert stub.total_llm_calls == 7
        assert stub.messages == []
        assert stub.llm_calls == []

    def test_missing_output_file(self, tmp_path):
        """output.mdがない場合、空文字列"""
        run_dir = tmp_path / "runs" / "cfg_t01_rep1"
        run_dir.mkdir(parents=True)
        # output.md は作成しない

        meta = {
            "config_name": "cfg", "theme_id": "t01", "replication": 1,
            "total_cost_usd": 0, "total_duration_sec": 0,
            "total_llm_calls": 0, "total_input_tokens": 0, "total_output_tokens": 0,
        }

        with patch("orgbench.runner.RESULTS_DIR", tmp_path):
            stub = _meta_to_stub(meta)

        assert stub.output_text == ""

    def test_timeout_preserved(self, tmp_path):
        run_dir = tmp_path / "runs" / "cfg_t01_rep1"
        run_dir.mkdir(parents=True)

        meta = {
            "config_name": "cfg", "theme_id": "t01", "replication": 1,
            "total_cost_usd": 0, "total_duration_sec": 600,
            "total_llm_calls": 0, "total_input_tokens": 0, "total_output_tokens": 0,
            "timeout": True, "error": "Timeout",
        }

        with patch("orgbench.runner.RESULTS_DIR", tmp_path):
            stub = _meta_to_stub(meta)

        assert stub.timeout is True
        assert stub.error == "Timeout"


# ============================================================
# 冪等性テスト（save→load roundtrip）
# ============================================================

class TestIdempotency:
    def test_save_then_restore_roundtrip(self, tmp_path):
        """save → meta読込 → stub復元 のラウンドトリップ"""
        original = RunResult(
            config_name="anchor", theme_id="t01", replication=1,
            output_text="# 提案\n\n内容", messages=[], llm_calls=[],
            total_cost_usd=0.05, total_duration_sec=10.0,
            total_llm_calls=7, total_input_tokens=5000, total_output_tokens=2000,
            timeout=False, error=None,
        )

        with patch("orgbench.runner.RESULTS_DIR", tmp_path):
            _save_result(original)
            run_dir = tmp_path / "runs" / "anchor_t01_rep1"
            meta = json.loads((run_dir / "run_meta.json").read_text())
            restored = _meta_to_stub(meta)

        assert restored.config_name == original.config_name
        assert restored.theme_id == original.theme_id
        assert restored.replication == original.replication
        assert restored.output_text == original.output_text
        assert restored.total_cost_usd == original.total_cost_usd
        assert restored.total_llm_calls == original.total_llm_calls
