"""judge.py のテスト — JSON解析、スコアパース、バッチ評価"""
from __future__ import annotations
import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from orgbench.judge import _parse_judge_output, judge_single, judge_batch, JUDGE_MODEL
from orgbench.models import JudgeScore, RunResult, LLMCall


# ============================================================
# _parse_judge_output のテスト
# ============================================================

class TestParseJudgeOutput:
    def test_json_in_code_block(self):
        """```json ... ``` 内のJSONを正しく抽出"""
        text = """評価結果は以下の通りです。

```json
{
  "feasibility": 4,
  "novelty": 3,
  "market_insight": 5,
  "financial_rigor": 2,
  "technical_depth": 4,
  "overall_quality": 3.5,
  "rationale": "技術面は良いが財務面に課題"
}
```
"""
        result = _parse_judge_output(text)
        assert result["feasibility"] == 4.0
        assert result["novelty"] == 3.0
        assert result["market_insight"] == 5.0
        assert result["financial_rigor"] == 2.0
        assert result["technical_depth"] == 4.0
        assert result["overall_quality"] == 3.5
        assert result["rationale"] == "技術面は良いが財務面に課題"

    def test_json_without_code_block(self):
        """コードブロックなしの素のJSON"""
        text = '{"feasibility": 4, "novelty": 3, "market_insight": 5, "financial_rigor": 2, "technical_depth": 4, "overall_quality": 3, "rationale": "test"}'
        result = _parse_judge_output(text)
        assert result["feasibility"] == 4.0

    def test_json_with_surrounding_text(self):
        """前後にテキストがあるJSON"""
        text = 'Here is my evaluation: {"feasibility": 5, "novelty": 4, "market_insight": 3, "financial_rigor": 2, "technical_depth": 1, "overall_quality": 3, "rationale": "ok"} End.'
        result = _parse_judge_output(text)
        assert result["feasibility"] == 5.0
        assert result["technical_depth"] == 1.0

    def test_missing_fields_default_to_3(self):
        """欠落フィールドはデフォルト値3.0"""
        text = '{"feasibility": 5}'
        result = _parse_judge_output(text)
        assert result["feasibility"] == 5.0
        assert result["novelty"] == 3.0  # デフォルト
        assert result["market_insight"] == 3.0
        assert result["financial_rigor"] == 3.0
        assert result["technical_depth"] == 3.0
        assert result["overall_quality"] == 3.0
        assert result["rationale"] == ""

    def test_completely_invalid_json(self):
        """完全に無効なテキスト → 全てデフォルト"""
        text = "This is not JSON at all"
        result = _parse_judge_output(text)
        assert all(result[d] == 3.0 for d in [
            "feasibility", "novelty", "market_insight",
            "financial_rigor", "technical_depth", "overall_quality",
        ])
        assert result["rationale"] == ""

    def test_empty_string(self):
        result = _parse_judge_output("")
        assert result["feasibility"] == 3.0

    def test_malformed_json(self):
        """壊れたJSON"""
        text = '{"feasibility": 4, "novelty": }'
        result = _parse_judge_output(text)
        # json.loads失敗 → デフォルト
        assert result["feasibility"] == 3.0

    def test_float_scores(self):
        """小数点スコア"""
        text = '{"feasibility": 3.7, "novelty": 4.2, "market_insight": 2.1, "financial_rigor": 1.5, "technical_depth": 4.9, "overall_quality": 3.3, "rationale": "mid"}'
        result = _parse_judge_output(text)
        assert result["feasibility"] == pytest.approx(3.7)
        assert result["novelty"] == pytest.approx(4.2)

    def test_integer_scores_converted_to_float(self):
        """整数スコアがfloatに変換される"""
        text = '{"feasibility": 4, "novelty": 3, "market_insight": 5, "financial_rigor": 2, "technical_depth": 4, "overall_quality": 3, "rationale": "ok"}'
        result = _parse_judge_output(text)
        assert isinstance(result["feasibility"], float)

    def test_json_with_whitespace_in_code_block(self):
        """コードブロック内の空白やインデント"""
        text = """```json
  {
    "feasibility": 4,
    "novelty": 3,
    "market_insight": 5,
    "financial_rigor": 2,
    "technical_depth": 4,
    "overall_quality": 3,
    "rationale": "評価テスト"
  }
```"""
        result = _parse_judge_output(text)
        assert result["feasibility"] == 4.0

    def test_extra_fields_ignored(self):
        """余分なフィールドは無視される"""
        text = '{"feasibility": 4, "novelty": 3, "market_insight": 5, "financial_rigor": 2, "technical_depth": 4, "overall_quality": 3, "rationale": "ok", "extra_field": 999}'
        result = _parse_judge_output(text)
        assert "extra_field" not in result


# ============================================================
# judge_single のテスト
# ============================================================

class TestJudgeSingle:
    @pytest.mark.asyncio
    async def test_basic_judge(self, tmp_path):
        """基本的な評価実行"""
        rubric_path = tmp_path / "rubric.md"
        rubric_path.write_text("テスト用ルーブリック", encoding="utf-8")

        judge_response = json.dumps({
            "feasibility": 4, "novelty": 3, "market_insight": 5,
            "financial_rigor": 2, "technical_depth": 4, "overall_quality": 3.5,
            "rationale": "良い提案"
        })

        mock_call_log = LLMCall(
            agent="judge", model=JUDGE_MODEL, input_tokens=500, output_tokens=100,
            cost_usd=0.001, duration_ms=1000, timestamp=datetime.now(),
            purpose="judge_run1", prompt_summary="", response_summary="",
        )

        with patch("orgbench.judge.RUBRIC_PATH", rubric_path):
            with patch("orgbench.judge.call_llm", new_callable=AsyncMock,
                       return_value=(judge_response, mock_call_log)):
                score = await judge_single(
                    output_text="テスト提案",
                    config_name="anchor",
                    theme_id="t01",
                    replication=1,
                    judge_run=1,
                )

        assert isinstance(score, JudgeScore)
        assert score.config_name == "anchor"
        assert score.theme_id == "t01"
        assert score.replication == 1
        assert score.judge_run == 1
        assert score.feasibility == 4.0
        assert score.overall_quality == 3.5
        assert score.rationale == "良い提案"

    @pytest.mark.asyncio
    async def test_judge_uses_gemini_flash(self, tmp_path):
        """JudgeがGemini Flashモデルを使用する"""
        rubric_path = tmp_path / "rubric.md"
        rubric_path.write_text("rubric", encoding="utf-8")

        mock_log = LLMCall(
            agent="judge", model=JUDGE_MODEL, input_tokens=0, output_tokens=0,
            cost_usd=0, duration_ms=0, timestamp=datetime.now(),
            purpose="", prompt_summary="", response_summary="",
        )

        with patch("orgbench.judge.RUBRIC_PATH", rubric_path):
            with patch("orgbench.judge.call_llm", new_callable=AsyncMock,
                       return_value=('{"feasibility":3}', mock_log)) as mock_call:
                await judge_single("test", "cfg", "t01", 1, 1)

        assert mock_call.call_args.kwargs["model"] == "gemini/gemini-2.5-flash"

    @pytest.mark.asyncio
    async def test_judge_low_temperature(self, tmp_path):
        """評価は低温(0.3)で実行される"""
        rubric_path = tmp_path / "rubric.md"
        rubric_path.write_text("rubric", encoding="utf-8")

        mock_log = LLMCall(
            agent="judge", model=JUDGE_MODEL, input_tokens=0, output_tokens=0,
            cost_usd=0, duration_ms=0, timestamp=datetime.now(),
            purpose="", prompt_summary="", response_summary="",
        )

        with patch("orgbench.judge.RUBRIC_PATH", rubric_path):
            with patch("orgbench.judge.call_llm", new_callable=AsyncMock,
                       return_value=('{}', mock_log)) as mock_call:
                await judge_single("test", "cfg", "t01", 1, 1)

        assert mock_call.call_args.kwargs["temperature"] == 0.3


# ============================================================
# judge_batch のテスト
# ============================================================

class TestJudgeBatch:
    @pytest.mark.asyncio
    async def test_batch_two_runs_per_result(self, tmp_path, make_run_result):
        """各結果に対して2回の独立評価が実行される"""
        rubric_path = tmp_path / "rubric.md"
        rubric_path.write_text("rubric", encoding="utf-8")

        results = [
            make_run_result(config_name="anchor", theme_id="t01", replication=1),
            make_run_result(config_name="flat_hub", theme_id="t01", replication=1),
        ]

        call_count = 0
        async def mock_judge(output_text, config_name, theme_id, replication, judge_run):
            nonlocal call_count
            call_count += 1
            return JudgeScore(
                config_name=config_name, theme_id=theme_id,
                replication=replication, judge_run=judge_run,
                feasibility=4, novelty=3, market_insight=4,
                financial_rigor=3, technical_depth=4, overall_quality=3.5,
                rationale="test",
            )

        with patch("orgbench.judge.judge_single", side_effect=mock_judge):
            scores = await judge_batch(results)

        assert len(scores) == 4  # 2結果 × 2回
        assert call_count == 4

        # judge_run 1 と 2 が含まれる
        judge_runs = {s.judge_run for s in scores}
        assert judge_runs == {1, 2}

    @pytest.mark.asyncio
    async def test_batch_empty_results(self):
        """空の結果リストでもクラッシュしない"""
        scores = await judge_batch([])
        assert scores == []

    @pytest.mark.asyncio
    async def test_batch_preserves_config_info(self, make_run_result):
        """バッチ評価が構成情報を保持する"""
        results = [
            make_run_result(config_name="anchor", theme_id="t01", replication=1),
            make_run_result(config_name="anchor", theme_id="t02", replication=2),
        ]

        async def mock_judge(output_text, config_name, theme_id, replication, judge_run):
            return JudgeScore(
                config_name=config_name, theme_id=theme_id,
                replication=replication, judge_run=judge_run,
                feasibility=3, novelty=3, market_insight=3,
                financial_rigor=3, technical_depth=3, overall_quality=3,
                rationale="",
            )

        with patch("orgbench.judge.judge_single", side_effect=mock_judge):
            scores = await judge_batch(results)

        configs = {(s.config_name, s.theme_id, s.replication) for s in scores}
        assert ("anchor", "t01", 1) in configs
        assert ("anchor", "t02", 2) in configs
