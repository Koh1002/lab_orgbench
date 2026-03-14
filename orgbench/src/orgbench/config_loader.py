"""YAML構成ファイルの読み込みとバリデーション"""
from __future__ import annotations
from pathlib import Path
import yaml
from .models import (
    AgentDef, FlowStep, TemplateConfig, ThemeConfig,
    AuthorityType, CommunicationType, ReviewType, ModelPreset,
)


def load_template(path: str | Path) -> TemplateConfig:
    """テンプレートYAMLを読み込みTemplateConfigに変換。"""
    path = Path(path)
    data = yaml.safe_load(path.read_text(encoding="utf-8"))

    # プロンプトファイルの読み込み
    agents = []
    for a in data["agents"]:
        prompt_file_str = a.get("prompt_file", "")
        prompt_file = Path(prompt_file_str) if prompt_file_str else None
        if prompt_file and prompt_file.is_file():
            system_prompt = prompt_file.read_text(encoding="utf-8")
        else:
            system_prompt = f"あなたは{a['role']}です。"

        agents.append(AgentDef(
            name=a["name"],
            role=a["role"],
            model=a["model"],
            system_prompt=system_prompt,
            reports_to=a.get("reports_to", []),
            manages=a.get("manages", []),
            peers=a.get("peers", []),
            can_communicate_with=a.get("can_communicate_with", []),
            has_review_authority_over=a.get("has_review_authority_over", []),
            tools=a.get("tools", []),
        ))

    flow = []
    for f in data["flow"]:
        flow.append(FlowStep(
            agent=f["agent"],
            input_from=f.get("input_from"),
            action=f["action"],
            output_to=f.get("output_to"),
            gate=f.get("gate"),
        ))

    authority = AuthorityType(data["authority"]) if data.get("authority") else None
    communication = CommunicationType(data["communication"]) if data.get("communication") else None
    review = ReviewType(data["review"]) if data.get("review") else None
    model_preset = ModelPreset(data["model_preset"]) if data.get("model_preset") else None

    return TemplateConfig(
        name=data["name"],
        authority=authority,
        communication=communication,
        review=review,
        model_preset=model_preset,
        agents=agents,
        flow=flow,
        max_review_rounds=data.get("max_review_rounds", 2),
    )


def load_theme(path: str | Path) -> ThemeConfig:
    """テーマYAMLを読み込みThemeConfigに変換。"""
    path = Path(path)
    data = yaml.safe_load(path.read_text(encoding="utf-8"))

    return ThemeConfig(
        id=data["id"],
        title=data["title"],
        domain=data["domain"],
        uncertainty_group=data["uncertainty_group"],
        task_prompt=data["task_prompt"],
        search_queries=data.get("search_queries", []),
    )


def load_experiment(path: str | Path) -> dict:
    """実験全体設定YAMLを読み込み。"""
    path = Path(path)
    data = yaml.safe_load(path.read_text(encoding="utf-8"))

    templates = [load_template(t) for t in data["templates"]]
    themes = [load_theme(t) for t in data["themes"]]

    return {
        "phase": data.get("phase", "pilot"),
        "templates": templates,
        "themes": themes,
        "replications": data.get("replications", 5),
        "temperature": data.get("temperature", 0.7),
        "timeout_sec": data.get("timeout_sec", 600),
    }
