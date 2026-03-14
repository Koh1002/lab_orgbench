"""
情報理論的指標の計算 (M1-M7)

M1: Compression Ratio (CR) — トークンベース
M2: Information Density (ID) — n-gram多様性
M3: Semantic Similarity Decay (SSD) — embeddingベース
M4: Cross-Step MI Estimate (CSMI) — embeddingベースMI近似
M5: Entity Preservation Rate (EPR) — NERベース
M6: Numerical Fidelity (NF) — 数値の正確な引き継ぎ
M7: Tracer Survival Rate (TSR) — トレーサー検出
"""
from __future__ import annotations
import re
from dataclasses import dataclass, field


@dataclass
class StepMetrics:
    """1ステップの情報理論的指標"""
    step_index: int
    agent: str
    compression_ratio: float        # M1
    information_density: float      # M2
    semantic_similarity: float      # M3 (vs original task)
    numerical_fidelity: float       # M6
    tracer_survival_rate: float     # M7
    entities_in: int = 0
    entities_out: int = 0
    entity_preservation_rate: float = 0.0  # M5


@dataclass
class RunInfoMetrics:
    """1回の実行全体の情報理論的指標"""
    config_name: str
    theme_id: str
    replication: int
    step_metrics: list[StepMetrics] = field(default_factory=list)
    final_tsr: float = 0.0
    final_ssd: float = 0.0
    min_cr_critical: float = 0.0
    mean_cr: float = 0.0
    critical_depth: int = 0


# ============================================================
# M1: Compression Ratio
# ============================================================

def compression_ratio(input_tokens: int, output_tokens: int) -> float:
    """M1: output_tokens / input_tokens"""
    return output_tokens / input_tokens if input_tokens > 0 else 0.0


# ============================================================
# M2: Information Density
# ============================================================

def information_density(text: str, n: int = 3) -> float:
    """M2: unique n-grams / total tokens. 高いほど多様（低い繰り返し）。"""
    tokens = text.split()
    if len(tokens) < n:
        return 1.0
    ngrams = set()
    for i in range(len(tokens) - n + 1):
        ngrams.add(tuple(tokens[i:i + n]))
    return len(ngrams) / len(tokens) if tokens else 0.0


# ============================================================
# M6: Numerical Fidelity
# ============================================================

_NUM_PATTERN = re.compile(r'[\d,]+\.?\d*')


def extract_numbers(text: str) -> set[str]:
    """テキストから数値を抽出し、正規化した文字列のセットを返す。"""
    raw = _NUM_PATTERN.findall(text)
    normalized = set()
    for r in raw:
        cleaned = r.replace(',', '')
        if cleaned and cleaned != '.':
            try:
                val = float(cleaned)
                if val != 0:
                    normalized.add(cleaned)
            except ValueError:
                pass
    return normalized


def numerical_fidelity(input_text: str, output_text: str) -> float:
    """M6: 入力の数値が出力に正確に保存されている割合。"""
    input_nums = extract_numbers(input_text)
    if not input_nums:
        return 1.0
    output_nums = extract_numbers(output_text)
    preserved = input_nums & output_nums
    return len(preserved) / len(input_nums)


# ============================================================
# M7: Tracer Survival Rate
# ============================================================

@dataclass
class Tracer:
    """追跡対象のトレーサー情報"""
    id: str
    type: str           # numerical, entity, fact, constraint
    content: str        # 元の内容
    detection: str      # 検出パターン（exact match用）


def tracer_survival(text: str, tracers: list[Tracer]) -> tuple[float, list[bool]]:
    """
    M7: テキスト中のトレーサー検出率。

    Returns:
        (survival_rate, per_tracer_detected)
    """
    if not tracers:
        return 1.0, []
    detected = []
    for t in tracers:
        found = t.detection in text
        detected.append(found)
    rate = sum(detected) / len(detected)
    return rate, detected


def tracer_survival_by_step(
    step_outputs: list[str],
    tracers: list[Tracer],
) -> list[tuple[float, list[bool]]]:
    """各ステップでのトレーサー生存率を計算。"""
    return [tracer_survival(output, tracers) for output in step_outputs]


# ============================================================
# M3: Semantic Similarity Decay (stub — requires embedding API)
# ============================================================

async def semantic_similarity(
    text_a: str,
    text_b: str,
    model: str = "text-embedding-3-small",
) -> float:
    """
    M3: 2テキスト間のコサイン類似度（embeddingベース）。

    NOTE: 実際のembedding APIを使用。litellm経由でOpenAI/その他のembeddingモデルに対応。
    """
    try:
        import litellm
        resp = await litellm.aembedding(
            model=model,
            input=[text_a[:8000], text_b[:8000]],  # トークン上限対策
        )
        emb_a = resp.data[0]["embedding"]
        emb_b = resp.data[1]["embedding"]
        # コサイン類似度
        dot = sum(a * b for a, b in zip(emb_a, emb_b))
        norm_a = sum(a * a for a in emb_a) ** 0.5
        norm_b = sum(b * b for b in emb_b) ** 0.5
        return dot / (norm_a * norm_b) if norm_a > 0 and norm_b > 0 else 0.0
    except Exception:
        return 0.0


async def semantic_similarity_decay(
    task_prompt: str,
    step_outputs: list[str],
    model: str = "text-embedding-3-small",
) -> list[float]:
    """M3: タスクプロンプトと各ステップ出力の類似度推移。"""
    similarities = []
    for output in step_outputs:
        sim = await semantic_similarity(task_prompt, output, model)
        similarities.append(sim)
    return similarities
