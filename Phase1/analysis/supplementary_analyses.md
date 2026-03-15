# 補足分析7件の結果

> 実行日: 2026-03-15

## 1. Chain 5/6 Review Recovery by Dimension

chain_4→5（+CFOレビュー）で最も改善する次元: Financial Rigor (+0.57), Novelty (+0.34)
chain_4→6（+CDOレビュー追加）で最も改善: Technical Depth (+0.37)
→ H5の拡張: レビュアーの専門性に対応する次元が改善。CFO→財務, CDO→技術

## 2. Depth × Theme Uncertainty

| Uncertainty | slope/step | 解釈 |
|------------|-----------|------|
| low | -0.46 | depth penaltyが最も大きい |
| medium | -0.25 | 中程度 |
| high | -0.42 | lowに近い |

低不確実性タスクほどdepth penaltyが大きい。仮説: 低不確実性タスクは「既知情報の正確な伝達」が重要 → 中継による歪みが致命的。高不確実性タスクは「創造的な情報付加」が重要 → augmentationが補償。

## 3. M3 (SSD) vs OQ: r=-0.73 (負の相関!)

タスクプロンプトに意味的に近い出力（chain系）は品質が低く、遠い出力（flat系）は品質が高い。
→ 高品質な出力はaugmentationにより元のタスクから「発展」しており、単なるタスクの繰り返しではない。M3は「情報保存」ではなく「情報変換の度合い」を測っている。

## 4. flat_mesh TSR step-by-step

| Step | flat_mesh | anchor | 差分 |
|------|-----------|--------|------|
| CEO初回 | 0.70 | 0.70 | 同じ |
| TL/Researcher | 0.30 | 0.20 | flat_meshにTLなし |
| Writer | **0.70** | 0.10 | **flat_meshではWriter がトレーサーを回復** |
| CEO統合 | **0.60** | 0.10 | **6倍の情報保持** |

flat_meshではTLを経由しないため、WriterがCEOの元の出力（トレーサー含む）にアクセスでき、情報を回復。anchor ではTLのフィルタリング後にWriter は2/10のトレーサーしか見えない。

## 5. Power Analysis

| Test | r | n | Power |
|------|---|---|-------|
| H1: depth vs OQ | -0.458 | 90 | 0.99 |
| H6: CEO input vs OQ | +0.317 | 150 | 0.97 |
| Prelim: depth vs OQ | -0.255 | 250 | 0.98 |
| Prelim: TL CR vs OQ | +0.169 | 150 | **0.54** |
| TSR: flat_mesh vs anchor | ~0.83 | 18 | 0.94 |

全て power > 0.94。唯一 TL CR vs OQ (power=0.54) は不十分 → この結果は慎重に解釈すべき。
