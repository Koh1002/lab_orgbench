"""config_loader.py のテスト — YAML読込、バリデーション、エッジケース"""
from __future__ import annotations
import pytest
import yaml
from pathlib import Path

from orgbench.config_loader import load_template, load_theme, load_experiment
from orgbench.models import (
    AuthorityType, CommunicationType, ReviewType, ModelPreset,
    TemplateConfig, ThemeConfig,
)


# ============================================================
# load_template のテスト
# ============================================================

class TestLoadTemplate:
    def test_basic_template(self, tmp_path):
        """基本的なテンプレート読込"""
        yaml_content = {
            "name": "test_tmpl",
            "authority": "deep",
            "communication": "hub",
            "review": "balanced",
            "model_preset": "hetero",
            "agents": [
                {
                    "name": "ceo",
                    "role": "CEO",
                    "model": "gpt-4o-mini",
                    "tools": [],
                },
                {
                    "name": "writer",
                    "role": "Writer",
                    "model": "gpt-4o-mini",
                    "tools": [],
                },
            ],
            "flow": [
                {"agent": "ceo", "input_from": None, "action": "指示", "output_to": "writer"},
                {"agent": "writer", "input_from": "ceo", "action": "執筆", "output_to": None},
            ],
            "max_review_rounds": 1,
        }
        yaml_path = tmp_path / "template.yaml"
        yaml_path.write_text(yaml.dump(yaml_content, allow_unicode=True), encoding="utf-8")

        tmpl = load_template(yaml_path)

        assert isinstance(tmpl, TemplateConfig)
        assert tmpl.name == "test_tmpl"
        assert tmpl.authority == AuthorityType.DEEP_HIERARCHY
        assert tmpl.communication == CommunicationType.HUB_AND_SPOKE
        assert tmpl.review == ReviewType.BALANCED
        assert tmpl.model_preset == ModelPreset.HETEROGENEOUS
        assert len(tmpl.agents) == 2
        assert len(tmpl.flow) == 2
        assert tmpl.max_review_rounds == 1

    def test_null_enums(self, tmp_path):
        """single_agent: authority/communication/review が null"""
        yaml_content = {
            "name": "single",
            "authority": None,
            "communication": None,
            "review": None,
            "model_preset": None,
            "agents": [
                {"name": "single", "role": "All", "model": "gpt-4o-mini", "tools": ["web_search"]},
            ],
            "flow": [
                {"agent": "single", "action": "全実行"},
            ],
        }
        yaml_path = tmp_path / "single.yaml"
        yaml_path.write_text(yaml.dump(yaml_content, allow_unicode=True), encoding="utf-8")

        tmpl = load_template(yaml_path)
        assert tmpl.authority is None
        assert tmpl.communication is None
        assert tmpl.review is None
        assert tmpl.model_preset is None

    def test_prompt_file_loaded(self, tmp_path):
        """prompt_fileが存在する場合、その内容がsystem_promptにセットされる"""
        prompt_path = tmp_path / "ceo_prompt.md"
        prompt_path.write_text("あなたはCEOです。全体を統括してください。", encoding="utf-8")

        yaml_content = {
            "name": "test",
            "authority": "deep",
            "communication": "hub",
            "review": "balanced",
            "model_preset": "hetero",
            "agents": [
                {"name": "ceo", "role": "CEO", "model": "gpt-4o-mini",
                 "prompt_file": str(prompt_path), "tools": []},
            ],
            "flow": [{"agent": "ceo", "action": "test"}],
        }
        yaml_path = tmp_path / "template.yaml"
        yaml_path.write_text(yaml.dump(yaml_content, allow_unicode=True), encoding="utf-8")

        tmpl = load_template(yaml_path)
        assert tmpl.agents[0].system_prompt == "あなたはCEOです。全体を統括してください。"

    def test_prompt_file_missing_fallback(self, tmp_path):
        """prompt_fileが存在しない場合、デフォルトプロンプトが生成される"""
        yaml_content = {
            "name": "test",
            "authority": "deep",
            "communication": "hub",
            "review": "balanced",
            "model_preset": "hetero",
            "agents": [
                {"name": "ceo", "role": "CEO", "model": "gpt-4o-mini",
                 "prompt_file": "/nonexistent/path.md", "tools": []},
            ],
            "flow": [{"agent": "ceo", "action": "test"}],
        }
        yaml_path = tmp_path / "template.yaml"
        yaml_path.write_text(yaml.dump(yaml_content, allow_unicode=True), encoding="utf-8")

        tmpl = load_template(yaml_path)
        assert tmpl.agents[0].system_prompt == "あなたはCEOです。"

    def test_agent_relationships(self, tmp_path):
        """reports_to, manages, peers が正しく読み込まれる"""
        yaml_content = {
            "name": "test",
            "authority": "deep",
            "communication": "mesh",
            "review": "balanced",
            "model_preset": "hetero",
            "agents": [
                {
                    "name": "ceo",
                    "role": "CEO",
                    "model": "gpt-4o-mini",
                    "manages": ["tl"],
                    "peers": ["cfo"],
                    "tools": [],
                },
                {
                    "name": "tl",
                    "role": "TL",
                    "model": "gpt-4o-mini",
                    "reports_to": ["ceo"],
                    "manages": ["researcher"],
                    "tools": [],
                },
            ],
            "flow": [{"agent": "ceo", "action": "test"}],
        }
        yaml_path = tmp_path / "template.yaml"
        yaml_path.write_text(yaml.dump(yaml_content, allow_unicode=True), encoding="utf-8")

        tmpl = load_template(yaml_path)
        ceo = tmpl.agents[0]
        assert ceo.manages == ["tl"]
        assert ceo.peers == ["cfo"]
        tl = tmpl.agents[1]
        assert tl.reports_to == ["ceo"]

    def test_flow_with_gate(self, tmp_path):
        """review_gateが正しく読み込まれる"""
        yaml_content = {
            "name": "test",
            "authority": "deep",
            "communication": "hub",
            "review": "balanced",
            "model_preset": "hetero",
            "agents": [
                {"name": "cfo", "role": "CFO", "model": "gpt-4o-mini", "tools": []},
            ],
            "flow": [
                {"agent": "cfo", "input_from": "writer", "action": "レビュー",
                 "output_to": "writer", "gate": "review_gate"},
            ],
        }
        yaml_path = tmp_path / "template.yaml"
        yaml_path.write_text(yaml.dump(yaml_content, allow_unicode=True), encoding="utf-8")

        tmpl = load_template(yaml_path)
        assert tmpl.flow[0].gate == "review_gate"
        assert tmpl.flow[0].output_to == "writer"

    def test_default_max_review_rounds(self, tmp_path):
        """max_review_roundsが未指定の場合、デフォルト2"""
        yaml_content = {
            "name": "test",
            "authority": "deep",
            "communication": "hub",
            "review": "balanced",
            "model_preset": "hetero",
            "agents": [{"name": "a", "role": "A", "model": "m", "tools": []}],
            "flow": [{"agent": "a", "action": "test"}],
        }
        yaml_path = tmp_path / "template.yaml"
        yaml_path.write_text(yaml.dump(yaml_content, allow_unicode=True), encoding="utf-8")

        tmpl = load_template(yaml_path)
        assert tmpl.max_review_rounds == 2

    def test_all_review_types(self, tmp_path):
        """全てのレビュータイプが読み込める"""
        for review_val in ["balanced", "finance", "tech", "none"]:
            yaml_content = {
                "name": f"test_{review_val}",
                "authority": "deep", "communication": "hub",
                "review": review_val, "model_preset": "hetero",
                "agents": [{"name": "a", "role": "A", "model": "m", "tools": []}],
                "flow": [{"agent": "a", "action": "test"}],
            }
            yaml_path = tmp_path / f"template_{review_val}.yaml"
            yaml_path.write_text(yaml.dump(yaml_content, allow_unicode=True), encoding="utf-8")
            tmpl = load_template(yaml_path)
            assert tmpl.review == ReviewType(review_val)


# ============================================================
# load_theme のテスト
# ============================================================

class TestLoadTheme:
    def test_basic_theme(self, tmp_path):
        yaml_content = {
            "id": "t01_ai_accounting",
            "title": "中小企業向けAI経理自動化",
            "domain": "FinTech",
            "uncertainty_group": "low",
            "task_prompt": "ビジネス提案を作成してください。\n\n6セクション構成で。",
            "search_queries": ["query1", "query2"],
        }
        yaml_path = tmp_path / "theme.yaml"
        yaml_path.write_text(yaml.dump(yaml_content, allow_unicode=True), encoding="utf-8")

        theme = load_theme(yaml_path)
        assert isinstance(theme, ThemeConfig)
        assert theme.id == "t01_ai_accounting"
        assert theme.title == "中小企業向けAI経理自動化"
        assert theme.domain == "FinTech"
        assert theme.uncertainty_group == "low"
        assert "ビジネス提案を作成してください" in theme.task_prompt
        assert len(theme.search_queries) == 2

    def test_no_search_queries(self, tmp_path):
        yaml_content = {
            "id": "t01", "title": "Test", "domain": "Test",
            "uncertainty_group": "low", "task_prompt": "test",
        }
        yaml_path = tmp_path / "theme.yaml"
        yaml_path.write_text(yaml.dump(yaml_content, allow_unicode=True), encoding="utf-8")

        theme = load_theme(yaml_path)
        assert theme.search_queries == []

    def test_multiline_task_prompt(self, tmp_path):
        """マルチラインのtask_prompt"""
        yaml_content = {
            "id": "t01", "title": "Test", "domain": "Test",
            "uncertainty_group": "medium",
            "task_prompt": "Line 1\nLine 2\n\n- Point 1\n- Point 2",
        }
        yaml_path = tmp_path / "theme.yaml"
        yaml_path.write_text(yaml.dump(yaml_content, allow_unicode=True), encoding="utf-8")

        theme = load_theme(yaml_path)
        assert "\n" in theme.task_prompt


# ============================================================
# load_experiment のテスト
# ============================================================

class TestLoadExperiment:
    def _setup_experiment(self, tmp_path, n_templates=2, n_themes=2, replications=3):
        """テスト用実験設定を構築"""
        # テンプレート
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        template_paths = []
        for i in range(n_templates):
            tmpl = {
                "name": f"tmpl_{i}",
                "authority": "deep", "communication": "hub",
                "review": "balanced", "model_preset": "hetero",
                "agents": [{"name": "a", "role": "A", "model": "gpt-4o-mini", "tools": []}],
                "flow": [{"agent": "a", "action": "test"}],
            }
            p = templates_dir / f"tmpl_{i}.yaml"
            p.write_text(yaml.dump(tmpl, allow_unicode=True), encoding="utf-8")
            template_paths.append(str(p))

        # テーマ
        themes_dir = tmp_path / "themes"
        themes_dir.mkdir()
        theme_paths = []
        for i in range(n_themes):
            theme = {
                "id": f"t{i:02d}", "title": f"Theme {i}",
                "domain": "Test", "uncertainty_group": "low",
                "task_prompt": f"テーマ{i}の提案を作成",
            }
            p = themes_dir / f"t{i:02d}.yaml"
            p.write_text(yaml.dump(theme, allow_unicode=True), encoding="utf-8")
            theme_paths.append(str(p))

        # 実験設定
        exp = {
            "phase": "pilot",
            "templates": template_paths,
            "themes": theme_paths,
            "replications": replications,
            "temperature": 0.7,
            "timeout_sec": 300,
        }
        exp_path = tmp_path / "experiment.yaml"
        exp_path.write_text(yaml.dump(exp, allow_unicode=True), encoding="utf-8")
        return exp_path

    def test_basic_load(self, tmp_path):
        exp_path = self._setup_experiment(tmp_path)
        exp = load_experiment(exp_path)

        assert exp["phase"] == "pilot"
        assert len(exp["templates"]) == 2
        assert len(exp["themes"]) == 2
        assert exp["replications"] == 3
        assert exp["temperature"] == 0.7
        assert exp["timeout_sec"] == 300

    def test_templates_are_template_configs(self, tmp_path):
        exp_path = self._setup_experiment(tmp_path)
        exp = load_experiment(exp_path)

        for tmpl in exp["templates"]:
            assert isinstance(tmpl, TemplateConfig)

    def test_themes_are_theme_configs(self, tmp_path):
        exp_path = self._setup_experiment(tmp_path)
        exp = load_experiment(exp_path)

        for theme in exp["themes"]:
            assert isinstance(theme, ThemeConfig)

    def test_default_values(self, tmp_path):
        """デフォルト値のテスト"""
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        tmpl = {
            "name": "test", "authority": "flat", "communication": "hub",
            "review": "none", "model_preset": "hetero",
            "agents": [{"name": "a", "role": "A", "model": "m", "tools": []}],
            "flow": [{"agent": "a", "action": "test"}],
        }
        tp = templates_dir / "t.yaml"
        tp.write_text(yaml.dump(tmpl, allow_unicode=True), encoding="utf-8")

        themes_dir = tmp_path / "themes"
        themes_dir.mkdir()
        theme = {"id": "t00", "title": "T", "domain": "D", "uncertainty_group": "low", "task_prompt": "p"}
        thp = themes_dir / "t.yaml"
        thp.write_text(yaml.dump(theme, allow_unicode=True), encoding="utf-8")

        exp = {
            "templates": [str(tp)],
            "themes": [str(thp)],
        }
        exp_path = tmp_path / "exp.yaml"
        exp_path.write_text(yaml.dump(exp, allow_unicode=True), encoding="utf-8")

        result = load_experiment(exp_path)
        assert result["phase"] == "pilot"  # デフォルト
        assert result["replications"] == 5  # デフォルト
        assert result["temperature"] == 0.7
        assert result["timeout_sec"] == 600

    def test_total_run_count(self, tmp_path):
        """テンプレート数 × テーマ数 × 反復数の組み合わせ確認"""
        exp_path = self._setup_experiment(tmp_path, n_templates=3, n_themes=5, replications=7)
        exp = load_experiment(exp_path)

        total = len(exp["templates"]) * len(exp["themes"]) * exp["replications"]
        assert total == 3 * 5 * 7


# ============================================================
# 実際のYAMLファイル読込テスト
# ============================================================

class TestLoadRealConfigs:
    """実際のconfigs/ディレクトリのYAMLを読み込むテスト"""

    @pytest.fixture
    def configs_dir(self):
        """実際のconfigs/ディレクトリのパス"""
        d = Path(__file__).resolve().parent.parent / "configs"
        if not d.exists():
            pytest.skip("configs/ directory not found")
        return d

    def test_load_all_templates(self, configs_dir):
        """全11テンプレートが正常に読み込める"""
        templates_dir = configs_dir / "templates"
        if not templates_dir.exists():
            pytest.skip("templates/ directory not found")

        templates = list(templates_dir.glob("*.yaml"))
        assert len(templates) == 11

        for yaml_path in templates:
            tmpl = load_template(yaml_path)
            assert isinstance(tmpl, TemplateConfig)
            assert tmpl.name  # nameは空でない
            assert len(tmpl.agents) >= 1
            assert len(tmpl.flow) >= 1

    def test_load_all_themes(self, configs_dir):
        """全5テーマが正常に読み込める"""
        themes_dir = configs_dir / "themes"
        if not themes_dir.exists():
            pytest.skip("themes/ directory not found")

        themes = list(themes_dir.glob("*.yaml"))
        assert len(themes) == 5

        for yaml_path in themes:
            theme = load_theme(yaml_path)
            assert isinstance(theme, ThemeConfig)
            assert theme.id
            assert theme.task_prompt

    def test_anchor_template_structure(self, configs_dir):
        """Anchor構成の詳細検証"""
        anchor_path = configs_dir / "templates" / "anchor.yaml"
        if not anchor_path.exists():
            pytest.skip("anchor.yaml not found")

        tmpl = load_template(anchor_path)
        assert tmpl.name == "anchor"
        assert tmpl.authority == AuthorityType.DEEP_HIERARCHY
        assert tmpl.communication == CommunicationType.HUB_AND_SPOKE
        assert tmpl.review == ReviewType.BALANCED
        assert tmpl.model_preset == ModelPreset.HETEROGENEOUS

        agent_names = {a.name for a in tmpl.agents}
        assert agent_names == {"ceo", "tl", "researcher", "writer", "cfo", "cdo"}

        # Researcherだけweb_searchツールを持つ
        researcher = next(a for a in tmpl.agents if a.name == "researcher")
        assert "web_search" in researcher.tools

        # CEOはHaiku
        ceo = next(a for a in tmpl.agents if a.name == "ceo")
        assert "haiku" in ceo.model

        # フローにreview_gateが含まれる
        gates = [s for s in tmpl.flow if s.gate == "review_gate"]
        assert len(gates) >= 1

    def test_single_agent_template(self, configs_dir):
        """Single-Agent構成の検証"""
        path = configs_dir / "templates" / "single_agent.yaml"
        if not path.exists():
            pytest.skip("single_agent.yaml not found")

        tmpl = load_template(path)
        assert tmpl.name == "single_agent"
        assert tmpl.authority is None
        assert len(tmpl.agents) == 1
        assert len(tmpl.flow) == 1
        assert "web_search" in tmpl.agents[0].tools

    def test_homo_haiku_all_same_model(self, configs_dir):
        """Homo-Haiku構成: 全エージェントが同一モデル"""
        path = configs_dir / "templates" / "homo_haiku.yaml"
        if not path.exists():
            pytest.skip("homo_haiku.yaml not found")

        tmpl = load_template(path)
        models = {a.model for a in tmpl.agents}
        assert len(models) == 1  # 全て同じモデル
        assert "haiku" in list(models)[0]

    def test_mesh_template_has_peers(self, configs_dir):
        """Mesh構成: peersが設定されている"""
        path = configs_dir / "templates" / "deep_mesh.yaml"
        if not path.exists():
            pytest.skip("deep_mesh.yaml not found")

        tmpl = load_template(path)
        assert tmpl.communication == CommunicationType.MESH
        # 少なくとも1つのエージェントがpeersを持つ
        has_peers = any(len(a.peers) > 0 for a in tmpl.agents)
        assert has_peers

    def test_experiment_yaml_loads(self, configs_dir):
        """experiment.yaml が正常に読み込める"""
        exp_path = configs_dir.parent / "configs" / "experiment.yaml"
        if not exp_path.exists():
            pytest.skip("experiment.yaml not found")

        exp = load_experiment(exp_path)
        assert len(exp["templates"]) == 11
        assert len(exp["themes"]) == 5
        assert exp["replications"] == 5
