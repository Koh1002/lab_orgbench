# Phase 1 論文: 未解決課題・検討事項・TODO一覧

> 論文ドラフト `paper_draft_v0.1.tex` の [TODO] タグから抽出
> 作成日: 2026-03-14

---

## カテゴリ別整理

### A. 理論的検討事項（論文の核心）

| # | 課題 | 重要度 | 現状 | 対応方針案 |
|---|------|--------|------|-----------|
| A1 | ~~DPI違反の条件整理・D_k/A_kの操作的定義~~ | ✅完了 | TIU（Task Information Unit）ベースで定義確定。D_k = Pres(k-1)\\Pres(k)の正規化、A_k = 新規タスク関連情報の正規化。D_k = D_filter + D_noise の分解、A_k = A_prior + A_tool + A_reason の分解。理論ノート: `theory/01_Dk_Ak_definition.md`、論文Sec3.3に反映済み |
| A2 | **チャネル飽和閾値の理論的モデル**: 飽和が起きるinput tokens数を予測する理論 | 高 | 予備分析でGPT-4o-mini: 3,000-5,000, Haiku: 12,000+と推定 | モデルのcontext window × attention efficiency factorとして定式化？ or 純粋に経験的にbreakpoint回帰で同定？ |
| A3 | **Bottleneck Principleの形式的証明**: max-flow min-cutとの対応の厳密化 | 中 | Propositionとして提示したが証明がない | LLMチャネルはクラシカルなネットワークフローと異なる（情報は「流体」ではなく「テキスト」）。厳密な証明は困難。代わりに実証的検証に焦点を当てるべきか？ |
| A4 | **3モード（保存/圧縮/増幅）の境界条件**: CRの閾値でモードを分類しているが、それは妥当か？ | 中 | CR > 1.2: augmentation, 0.2 < CR < 0.8: compression, CR < 0.1: saturation と暫定定義 | 情報の「質」（semantic similarity）も考慮すべき。CR=0.35でも重要情報を選択的に保持していれば「圧縮」であって「損失」ではない |

### B. 実験設計の検討事項

| # | 課題 | 重要度 | 現状 | 対応方針案 |
|---|------|--------|------|-----------|
| B1 | **orchestrator.pyの修正仕様**: StepTrace全文保存の実装詳細 | 最高 | models.pyにStepTrace追加、orchestrator.pyで各ステップ後に記録、step_traces.jsonlに保存 | 実装は比較的単純。output.mdと同等の全文をステップごとに保存。ただしファイルサイズ注意（1回あたり~50KBと推定） |
| B2 | **Chain長変化実験のテンプレート設計**: chain_2〜6の具体的フロー定義 | 高 | 概念設計のみ | chain_2: CEO→Writer、chain_3: CEO→TL→Writer、...と単純に中間層を追加。ただし各chainで「情報入力量」が異なる問題（chain_2のWriterは直接テーマを受け取るが、chain_6のWriterはフィルタ済み情報を受け取る） → これ自体がDPIの検証 |
| B3 | **トレーサー設計の具体化**: 何をどう埋め込むか | 高 | 種別（架空固有名詞/数値/事実/制約）は決定、具体的なトレーサー内容は未作成 | テーマごとに自然に見える10個のトレーサーを作成。検出方法: exact string match + 数値の±10%一致。ステップごとの生存をbool vectorで記録 |
| B4 | **日本語テキストのNER精度問題**: M5 (Entity Preservation Rate) の実装 | 中 | 日本語のNER精度はspaCyで限定的 | 代替案: (1) テキストを英訳してからNER、(2) LLMベースのNER（コスト高）、(3) トレーサー実験(M7)でNERを代替 → M7がcleanerなのでM5は補助指標とする |
| B5 | **MI推定手法の選定**: M4 (Cross-Step MI) の計算方法 | 中 | KSG estimator, MINE, embedding cosine の3候補 | embedding cosineをproxyとし、厳密MI推定はappendixのablationに回す。理由: サンプル数が少ない（各条件15-75回）ためKSG/MINEは不安定 |

### C. 分析の検討事項

| # | 課題 | 重要度 | 現状 | 対応方針案 |
|---|------|--------|------|-----------|
| C1 | ~~min(CR) vs OQ の相関分析~~ | ✅完了 | **結果**: depth(r=-0.255***)が最強、CEO input(r=+0.207**)が2番目。min(CR)は誤解を招く（レビュアー飽和が駆動）。Bottleneck PrincipleをDepth-Distortion Principleに修正済み。詳細: `analysis/bottleneck_analysis.md` |
| C2 | **減衰モデルのフィッティング**: Information Distortion Curveの形状 | 高 | 実験B完了後 | 線形/指数/対数の3モデルをフィッティングし、AIC/BICで選択。仮説: 指数減衰 f(d) = a·exp(-b·d) が最適 |
| C3 | **情報指標 vs 品質の回帰分析**: どの指標が品質を最もよく予測するか | 高 | 実験A/B/C完了後 | 回帰: OQ ~ M1 + M2 + ... + M7。変数選択: LASSO or stepwise。構造指標（graph metrics）との予測力比較 |
| C4 | **Researcher（外部情報源）のDPI違反分析**: augmentation modeの特徴づけ | 中 | ResearcherのCRは構成により大きく変動（0.07-1.76） | Researcher前後のsemantic similarityの変化を測定。Web検索結果の情報がfinal outputにどの程度反映されるか |

### D. 文献調査TODO

| # | 調査対象 | 重要度 | 理由 |
|---|---------|--------|------|
| D1 | ~~LLMの情報理論的分析~~ | ✅完了 | Ton et al. (ICML 2025), Nagle et al. (NeurIPS 2024), Cheng et al. (2025) を追加。Related Work反映済み |
| D2 | ~~Information Bottleneck理論~~ | ✅完了 | Lei et al. (ICLR 2026 submitted) を確認。IB-aware reasoning。今後の深掘り候補 |
| D3 | ~~計算組織論~~ | ✅完了 | Malone (1987), Carley (PNAS 2002) を追加。Related Work反映済み |
| D4 | ~~Lost in the Middle~~ | ✅完了 | Liu et al. (2024) は既に引用済み。飽和の理論的背景として |
| D5 | ~~CoT/Self-Reflection~~ | ✅完了 | Ton et al. がCoTの情報理論分析を提供。我々のマルチエージェント版として位置づけ |

### E. 論文の書き方・構成の検討

| # | 課題 | 対応方針案 |
|---|------|-----------|
| E1 | **AbstractのTODO数値埋め**: 実験完了後 | 最後に対応 |
| E2 | ~~Modified DPIの位置づけ~~ | ✅解決: accounting identity と認め、予測力は D_k/A_k の empirical regularities にあると明記。Proposition ではなく Definition + empirical claims として扱う |
| E3 | **予備分析(Sec 5)と本実験(Sec 6)の関係**: 予備分析が長すぎないか | 予備分析は1ページ以内に抑え、「なぜ追加実験が必要か」の動機づけに特化 |
| E4 | **ターゲット会議の選定**: どこに出すか | AAMAS 2027（マルチエージェント特化）, NeurIPS 2027（理論重視）, ICML 2027（ML理論）。理論の完成度次第 |
| E5 | **Phase 0論文との関係**: 同一データの再利用をどう正当化するか | 「予備分析」として既存データを使い、本実験は新規データ。Phase 0とは独立投稿可能。引用で接続 |

---

## 優先順位付きアクションリスト（2026-03-14 更新）

### ✅ 完了（3/14実施）
1. ~~[C1] min(CR) vs OQ の相関分析~~ → Depth-Distortion Principle に修正
2. ~~[A1] D_k/A_k の操作的定義~~ → TIUベースで確定
3. ~~[D1-D5] 文献調査~~ → 9本追加、Related Work 拡充済み
4. ~~Shen et al. (2025) の差別化分析~~ → ほぼ完全に非重複を確認
5. ~~理論の再定位~~ → accounting identity と認め、予測力は empirical regularities にあると修正
6. ~~Testable Predictions (H1-H6)~~ → 反直感的予測3つ含む6つの検証可能予測を追加
7. ~~TL pass-through テンプレート~~ → `configs/templates/deep_passthrough.yaml` 作成
8. ~~H3 検証（既存データ）~~ → homo_haiku(depth=4)=flat_hub(depth=3) で支持
9. ~~H5 検証（既存データ）~~ → Technical Depth +0.34, Feasibility +0.20 で部分支持

### 来週やるべきこと（3/15-3/21）

1. **[B1] orchestrator.py修正（StepTrace全文保存）** — 実装
2. **[B2] chain_2〜6のYAMLテンプレート作成** — 実験B準備
3. **[B3] トレーサーの具体的内容作成** — 実験C準備（テーマごとに10個のトレーサー設計）
4. **[B5] MI推定手法の最終決定** — embedding cosine を proxy とし、KSG は appendix

### 再来週（3/22-3/28）

5. **実験A実行（全文保存再実験60回）**
6. **実験D実行（TL pass-through 15回）** ← **最重要実験**
7. **実験B実行（chain長変化75回）**
8. **実験C実行（トレーサー注入36回）**

### その後（3/29-4/11）

9. 情報指標（M2-M7）計算
10. 全分析実行（H1-H6の検証）
11. MI推定（embedding-based）
12. Results/Discussion 執筆
11. **情報指標モジュール（metrics.py）の実装完了**

---

## 論文の強み・弱みの自己評価

### 強み
- **novelty明確**: LLMエージェントネットワークの情報理論的分析は先行研究なし
- **理論と実証の両輪**: 数理モデル→予測→検証のサイクルが明快
- **実データに根差した理論**: 予備分析の発見（3モード、飽和、ボトルネック）が理論を動機づけ
- **実務的示唆が具体的**: 「最弱リンクを排除せよ」は即座に適用可能な設計指針

### 弱み（査読で指摘されそうな点）
- **理論の厳密性**: Propositionに証明がない。形式的にはheuristicな命題群
  - 対策: "Empirically-motivated theoretical framework"と位置づけ、実証検証を主軸にする
- **指標の妥当性**: CRやcosine similarityはMIの粗い代理
  - 対策: 複数指標の整合性を示す（全指標が同一方向を支持すれば robustness argument）
- **タスクの限定性**: ビジネス提案のみ
  - 対策: Limitation節で明記。他タスクへの一般化はFuture Work
- **モデル依存性**: 飽和閾値がモデル固有
  - 対策: モデル能力をパラメータとした一般的フレームワークとして提示
