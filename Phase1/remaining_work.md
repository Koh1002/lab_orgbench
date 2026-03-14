# Phase 1 残作業リスト

> 更新日: 2026-03-15
> 論文ドラフト: paper_draft_v0.1.tex
> ステータス: Sec 1-5 完成、Sec 6 部分完成（実験D完了）、Sec 7-8 部分記述済み

---

## 論文セクション別の進捗

| セクション | 状態 | 残作業 |
|-----------|------|--------|
| Abstract | 80% | 実験数・結果数値を埋める（実験全完了後） |
| Sec 1 Introduction | ✅ 95% | minor polish のみ |
| Sec 2 Related Work | ✅ 90% | Shen et al. の差別化文を追加（1段落） |
| Sec 3 Theoretical Framework | ✅ 95% | 飽和閾値のTODOコメント整理 |
| Sec 4 Metrics | 70% | M2-M5の実装TODOコメントを結果反映に書き換え |
| Sec 5 Preliminary Analysis | ✅ 95% | minor polish |
| Sec 6 Experimental Design | ✅ 90% | 実験Dの記述完了。A/B/Cは設計記述済み |
| **Sec 7 Results** | **40%** | **H2, H3, H5 記述済み。H1, H4, H6 は実験A/B/C待ち** |
| **Sec 8 Discussion** | **60%** | **Depth dual mechanism、Guidelines、Limitations 記述済み。DPI議論とConclusion未** |

---

## 残り実験（実装済み・未実行）

| 実験 | 回数 | コスト | 目的 | 検証する仮説 |
|------|------|--------|------|-------------|
| **A: 全文保存再実験** | 60 | ~$3 | M2-M6計算用データ | H4(mesh vs hub), H6(CEO augmentation) |
| **B: Chain長変化** | 75 | ~$3 | Information Distortion Curve | **H1(depth vs TSR decay)** — 論文の中核結果 |
| **C: トレーサー注入** | 36 | ~$2 | 情報保存の直接測定 | **H1(tracer版)** — 最も客観的な検証 |
| Judge評価 (A+B+C) | 342 | ~$5 | 品質スコア | 全仮説の品質面検証 |
| **合計** | **171+342** | **~$13** | | |

## 残り分析（実験完了後に実施）

| 分析 | 依存する実験 | 内容 |
|------|-------------|------|
| Information Distortion Curve | B | chain長 d vs TSR/SSD/NF のフィッティング |
| Topology × Saturation分析 | A | mesh vs hub の情報指標比較（飽和分離） |
| 飽和閾値の同定 | A | 入力tokens vs CR のbreakpoint回帰 |
| トレーサー生存曲線 | C | ステップごとのTSR推移、構成別ヒートマップ |
| MI推定 | A | embeddingベースのMI近似値計算 |
| 回帰分析: OQ ~ M1-M7 | A+B+C | 情報指標の品質予測力 |

## 論文完成までのステップ

### Phase 1a: 実験実行（~1-2日）
1. [ ] 実験A実行（60回, ~$3, ~3時間）
2. [ ] 実験B実行（75回, ~$3, ~3時間）
3. [ ] 実験C実行（36回, ~$2, ~2時間）
4. [ ] Judge評価（171回×2, ~$5, ~1時間）

### Phase 1b: 分析（~2-3日）
5. [ ] Information Distortion Curve (H1)
6. [ ] Tracer Survival Analysis (H1)
7. [ ] Topology × Saturation (H4)
8. [ ] 飽和閾値の同定
9. [ ] MI推定（embeddingベース）
10. [ ] 回帰分析: OQ ~ 情報指標
11. [ ] Figure作成（6-8枚）

### Phase 1c: 論文仕上げ（~1週間）
12. [ ] Results セクション完成（H1, H4, H6）
13. [ ] Discussion: DPI議論
14. [ ] Conclusion
15. [ ] Abstract 最終化
16. [ ] Sec 2: Shen et al. 差別化段落追加
17. [ ] 全体のpolish、数値の整合性確認
18. [ ] 参考文献の正確性確認

### Phase 1d: レビュー・投稿（~1-2週間）
19. [ ] 内部レビュー（指導教員等）
20. [ ] 修正反映
21. [ ] 投稿先最終決定（AAMAS 2027 / NeurIPS 2027）
22. [ ] camera-ready準備
