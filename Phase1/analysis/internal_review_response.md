# 内部レビュー対応記録

> 日付: 2026-03-15
> レビュー結果: Weak Accept (5/10) → Must-fix 5件 + Should-fix 5件

---

## Must-fix (blocking) と対応

### 1. P0/P1 スコア不整合 → H2分解を P1 データのみで再計算

**問題**: H2分解が Phase 0 flat_hub(3.22) と Phase 1 deep_passthrough(3.10) の cross-phase 比較。P1 flat_hub は 3.02 なので、P1内で計算すると depth成分が -0.08（passthrough が flat_hub を上回る）。

**対応**: H2分解を P1 データのみで再計算し、論文を修正。

### 2. Proposition 2 → Empirical Finding に改称

**対応**: 論文内の "Proposition" を "Empirical Finding" に変更。

### 3. 3点相関 r=-0.996 → per-run相関に変更

**対応**: chain_2/3/4 の各run（15×3=45 runs）のOQとdepthの相関を計算。

### 4. Judge評価手法の記述追加

**対応**: Sec 6 に Judge model, rubric, 評価回数, 評価方法を明記。

### 5. TODOコメント/日本語コメントの除去

**対応**: 全ての draft artifact を除去。
