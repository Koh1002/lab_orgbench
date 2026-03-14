# 研究全体計画: B (Information Theory) → A (Dynamic Organizational Adaptation)

> 作成日: 2026-03-14
> 著者: Wataru Shinoda
> 現状: OrgBench v0.1（パイロット実験275回完了、論文ドラフトv0.1）

---

## 全体像

```
[現在] OrgBench v0.1 (実証ベンチマーク、パイロット完了)
    │
    ▼
[Phase B] 情報理論的フレームワークの構築
    │  理論 + 実証検証
    │  目標: NeurIPS 2027 / ICML 2027 / AAMAS 2027
    │
    ▼
[Phase A] 動的組織適応
    │  Bの理論を基盤にした適応アルゴリズム
    │  目標: ICLR 2028 / NeurIPS 2027 Workshop
    │
    ▼
[統合] OrgBench v2: 静的比較 + 情報理論 + 動的適応を統合したフレームワーク
```

---

## Phase B: Information Theory of Agent Organizations

### B.0 理論的動機

現在のOrgBenchは「どの構造が良いか」を実証的に示すが、「なぜ良いか」の因果的説明がない。情報理論はこのギャップを埋める:

- 深い階層 → メッセージが多段中継 → 各段で情報歪み（information distortion）が蓄積
- メッシュ通信 → 冗長経路 → エラー訂正能力が高いがノイズも増加
- レビューゲート → フィルタリングチャネル → 情報量削減 vs 品質向上のトレードオフ

**核心的問い: What is the information-theoretic cost of organizational depth, and what is the optimal topology for information preservation?**

### B.1 理論構築 (理論パート)

#### B.1.1 エージェントネットワークの情報処理グラフモデル

マルチエージェント組織を **情報処理グラフ** G = (V, E, C) として形式化:

- **V**: エージェントノード集合。各ノード v_i は情報処理関数 f_i: X → Y
- **E**: 有向通信エッジ集合。エッジ e_ij はエージェント i から j への通信チャネル
- **C**: 各エッジのチャネル容量 C(e_ij)

各エージェントを **有限容量の情報処理チャネル** としてモデル化:
- 入力: コンテキストウィンドウに入るトークン列（情報源）
- 出力: 生成されたトークン列（符号化された情報）
- チャネル容量: コンテキストウィンドウサイズ、モデル能力で決まる上限

#### B.1.2 Information Distortion の定式化

**定義**: エージェントチェーン A₁ → A₂ → ... → Aₙ における情報歪みを、入力情報と最終出力の間の相互情報量の減衰として定義:

```
D(n) = I(X; Y₁) - I(X; Yₙ)
```

ここで X は原情報（タスク要件 + 検索結果）、Yₖ はk番目のエージェントの出力。

**仮説 (Information Distortion Theorem)**:
- 各エージェントが独立なノイズチャネルの場合、Data Processing Inequality により I(X; Yₙ) ≤ I(X; Yₙ₋₁) ≤ ... ≤ I(X; Y₁)
- 階層が深いほど情報は単調に失われる
- LLMは単純なノイズチャネルではない（要約・推論で情報を「圧縮」しつつ新情報を付加しうる）ため、DPIの等号条件がいつ成立するかが研究問題

#### B.1.3 チャネル容量と組織トポロジー

**トポロジー別の理論的予測**:

| トポロジー | 情報経路長 | 冗長度 | 理論的予測 |
|-----------|-----------|--------|-----------|
| Hub-and-spoke (star) | max 2 | 低 | 低歪み、ボトルネックリスク（中心ノードの容量制約） |
| Deep hierarchy (chain) | max N | 低 | 高歪み、逐次的情報損失 |
| Mesh (complete) | 1 | 高 | 低歪み、ノイズ混入リスク（情報過多） |
| Flat (star, 1層) | 2 | 低 | Hub-and-spokeと同等だが権限集中なし |

**Rate-Distortion理論の適用**:
- 各エージェントの出力を、入力の有損失圧縮とみなす
- 組織全体のRate-Distortion関数 R(D) を導出し、最適トポロジーが与えるR(D)の下界を求める

#### B.1.4 レビューゲートの情報理論的解釈

レビューゲートを **フィードバック付きチャネル** としてモデル化:
- レビューなし: オープンループチャネル → 容量 C
- レビューあり: フィードバック付きチャネル → 容量は離散無記憶チャネルでは変わらない（Shannon, 1956）が、誤り確率は改善
- LLMチャネルは離散無記憶ではない → フィードバックが容量自体を向上させる可能性

### B.2 実証的検証 (実験パート)

#### B.2.1 情報量の操作的測定

LLMの入出力間の情報量を直接計算することは困難なため、以下のプロキシ指標を定義:

| 指標 | 計算方法 | 測定対象 |
|------|---------|---------|
| **Semantic Similarity Decay** | 入力テーマのembeddingと各ステップ出力のembeddingのコサイン類似度の減衰率 | 情報保存度 |
| **Entity Preservation Rate** | 入力に含まれるNER抽出エンティティが最終出力に残存する割合 | 具体的情報の保持 |
| **Numerical Fidelity** | 入力の数値データ（市場規模等）が最終出力で正確に引用される割合 | 定量情報の歪み |
| **Compression Ratio** | 入力トークン数 / 出力トークン数 | 情報圧縮率 |
| **Mutual Information Estimate** | 入出力ペアのembeddingからMINE等で推定 | 相互情報量の近似 |

#### B.2.2 実験設計

**既存データの再分析** (コスト: $0):
- パイロット275回の実行ログ（全メッセージ、全LLM呼び出し記録）を再分析
- 各ステップのinput/outputペアから上記プロキシ指標を計算
- 階層深度 × 情報歪み指標の相関を検証

**追加実験** (コスト: ~$100):
- 情報歪みの測定に特化した実験設計
  - 同一タスクを chain長 2/3/4/5/6 で実行（情報歪みの階層依存性）
  - 同一タスクを star/chain/mesh/tree で実行（トポロジー依存性）
  - 各条件5テーマ×3反復 = 60-100回
- **Controlled Information Injection**: 入力に特定の「トレーサー情報」（架空の統計値、固有名詞）を埋め込み、各ステップでの生存率を追跡

#### B.2.3 分析手法

1. **Information Distortion Curve**: 階層深度 d に対する各情報指標のプロット → 減衰モデル（線形/指数/対数）のフィッティング
2. **Topology × Information Preservation**: トポロジー別の最終出力における情報保存度の比較（Kruskal-Wallis検定）
3. **Channel Capacity Estimation**: 各エージェントの入出力ペアからチャネル容量の経験的推定
4. **Theoretical Prediction vs Empirical Result**: B.1の理論予測と実測値の一致度

### B.3 実装計画

#### B.3.1 新規モジュール

```
orgbench/src/orgbench/
├── info_theory/              # 新規
│   ├── __init__.py
│   ├── metrics.py            # 情報理論的指標の計算
│   │   ├── semantic_similarity_decay()
│   │   ├── entity_preservation_rate()
│   │   ├── numerical_fidelity()
│   │   ├── compression_ratio()
│   │   └── mutual_information_estimate()
│   ├── channel_model.py      # エージェントのチャネルモデル
│   │   ├── AgentChannel class
│   │   ├── estimate_capacity()
│   │   └── compute_distortion()
│   ├── topology_analysis.py  # トポロジーの情報理論的分析
│   │   ├── information_flow_graph()
│   │   ├── bottleneck_detection()
│   │   └── optimal_topology_bound()
│   └── visualization.py      # 情報フロー可視化
│       ├── plot_distortion_curve()
│       ├── plot_info_flow_graph()
│       └── plot_channel_capacity_heatmap()
```

#### B.3.2 既存コードへの変更

**orchestrator.py の拡張**:
- 各ステップの入出力ペアを `RunResult` に保存する（現在は先頭500文字のみ → 全文保存オプション追加）
- ステップ間の情報フローメタデータ（入力トークン数、出力トークン数、共有コンテキストサイズ）を記録

**models.py の拡張**:
- `FlowStep` に `input_text` / `output_text` フィールドを追加（全文保存用）
- `RunResult` に `step_traces: list[StepTrace]` を追加

**analysis.py の拡張**:
- 情報理論指標の集計・統計検定関数を追加

### B.4 論文構成案

**タイトル案**: "The Information-Theoretic Cost of Hierarchy: Modeling LLM Multi-Agent Organizations as Communication Networks"

**構成**:
1. Introduction: なぜ情報理論か（因果的説明の欠如）
2. Related Work: 情報理論 × 組織論（Galbraith再訪）、Data Processing Inequality、LLMの情報処理
3. Theoretical Framework: 情報処理グラフモデル、歪み定式化、トポロジー別予測
4. Experimental Setup: OrgBench + 追加実験
5. Results: 理論予測 vs 実測
6. Discussion: LLMはDPIに従うか？レビューのフィードバック効果
7. Implications: 組織設計への定量的指針

**ターゲット会議**:
- 第1候補: AAMAS 2027 (〆切 2026年10月頃)
- 第2候補: NeurIPS 2027 (〆切 2027年5月頃)
- 第3候補: ICML 2027 Workshop

### B.5 スケジュール

| 期間 | マイルストーン | 成果物 |
|------|-------------|--------|
| Week 1-2 (3/14-3/28) | 理論構築・文献調査 | 理論フレームワークの数学的定式化、関連論文の精読 |
| Week 3-4 (3/29-4/11) | 情報指標モジュール実装 | `info_theory/metrics.py` 完成、ユニットテスト |
| Week 5-6 (4/12-4/25) | 既存データ再分析 | パイロット275回の情報理論的分析結果 |
| Week 7-8 (4/26-5/9) | 追加実験（chain長変化、トポロジー比較） | 追加60-100回の実行、~$100 |
| Week 9-10 (5/10-5/23) | 理論 vs 実証の突き合わせ | 理論予測と実測の一致度分析 |
| Week 11-14 (5/24-6/20) | 論文執筆 | ドラフト完成 |
| Week 15-16 (6/21-7/4) | 内部レビュー・修正 | 投稿準備完了 |

---

## Phase A: Dynamic Organizational Adaptation

### A.0 Phase Bからの接続

Phase Bで確立する情報理論的フレームワークが、Phase Aの**理論的基盤**となる:

- **適応トリガーの理論的根拠**: 「information processing demand が現在のトポロジーのchannel capacity を超えたとき、構造を変更すべき」
- **適応先の理論的最適解**: 「現在のタスクの情報要求に対し、information distortion を最小化するトポロジーに切り替える」
- **適応の効果測定**: 「適応前後での information preservation rate の変化」

Bなしでは「なぜ適応するか」「何に適応するか」が場当たり的になる。Bがあれば理論駆動の適応アルゴリズムを設計できる。

### A.1 研究問題

**RQ-A1**: Can LLM agent organizations detect when their current structure is suboptimal for the task at hand?
→ 情報理論的指標（information bottleneck検出、channel saturation検出）による自動検知

**RQ-A2**: Can LLM agent organizations self-reconfigure to improve collective output quality?
→ agent spawn、role reassignment、hierarchy flattening の効果測定

**RQ-A3**: Does adaptive organization outperform the best fixed organization?
→ OrgBench静的比較のベストと動的適応の比較

### A.2 適応メカニズムの設計

#### A.2.1 適応トリガー（いつ適応するか）

Phase Bの指標をリアルタイムでモニタリングし、以下の条件で適応を発火:

| トリガー | 検出方法 | 適応アクション |
|---------|---------|--------------|
| **Information Bottleneck** | 中心ノード（CEO）のinput token数がcontext windowの80%超 | hierarchy flattening（中間層を追加して負荷分散） |
| **Information Starvation** | 末端エージェントの出力が入力の20%未満（過度な情報損失） | 直接通信チャネルの追加（mesh化） |
| **Redundancy Overload** | mesh通信で同一情報が3経路以上で重複 | hub-and-spoke への切り替え（情報集約） |
| **Quality Plateau** | 中間レビューのスコアが2ステップ連続で改善なし | role reassignment（レビュアー交代） |
| **Task Complexity Spike** | サブタスクの出力長が想定の2倍超 | agent spawn（専門エージェント追加） |

#### A.2.2 適応アクション（何を変えるか）

| アクション | 実装方法 | 情報理論的根拠 |
|-----------|---------|--------------|
| **Agent Spawn** | 新エージェントを動的にインスタンス化し、フローに挿入 | チャネル並列化による総容量増加 |
| **Role Reassignment** | エージェントのsystem promptを動的に変更 | チャネル特性の変更（汎用→専門） |
| **Hierarchy Flattening** | 中間層をバイパスし、直接報告に切り替え | 中継段数削減による情報歪み軽減 |
| **Hierarchy Deepening** | 新たな中間層を挿入し、情報を事前フィルタリング | ボトルネックノードの負荷分散 |
| **Communication Rewiring** | 通信トポロジーの動的変更 | Rate-Distortion最適トポロジーへの遷移 |

#### A.2.3 メタコントローラー設計

適応判断を行う **Meta-Controller** の2つの設計選択肢:

**Option 1: Rule-Based Controller**
- Phase Bで導出した閾値に基づく決定木
- 解釈可能・再現可能だが、柔軟性に欠ける
- 論文としての貢献は「理論駆動の適応ルール」

**Option 2: LLM-Based Controller**
- 専用のLLM（メタエージェント）が現在の情報フロー状態を分析し、適応を決定
- 柔軟だが、メタエージェント自体のコスト・信頼性が課題
- 論文としての貢献は「自己認識型エージェント組織」

**推奨**: まずOption 1で理論的にクリーンな結果を出し、Option 2はablation studyとして追加。

### A.3 実験設計

#### A.3.1 ベースライン

| ベースライン | 説明 |
|------------|------|
| OrgBench-Best-Static | Phase B/既存実験での最良固定構造 |
| Single-Agent-Strong | 現在の単一エージェントベースライン |
| Random Adaptation | ランダムタイミングでランダムな適応を行う |
| Oracle Adaptation | 各タスクに対し事後的に最適構造を選択（性能上限） |

#### A.3.2 タスク設計

動的適応の価値を示すには、**タスク中に複雑度が変化する**シナリオが必要:

| タスクタイプ | 説明 | 適応の必要性 |
|------------|------|-------------|
| **Complexity Escalation** | 簡単な市場調査→技術的に困難な実装計画 | 途中で技術専門エージェントの追加が必要 |
| **Domain Shift** | FinTechの提案中にヘルスケア規制の問題が発覚 | 役割の再割り当てが必要 |
| **Information Explosion** | Web検索結果が大量に返ってくるテーマ | 情報フィルタリング層の追加が必要 |
| **Multi-Phase** | Phase 1: リサーチ → Phase 2: 統合 → Phase 3: レビュー | 各フェーズで最適構造が異なる |

#### A.3.3 評価指標

既存のOrgBench指標に加え:

| 指標 | 定義 |
|------|------|
| **Adaptation Frequency** | 1回の実行あたりの適応回数 |
| **Adaptation Latency** | 問題検出から適応完了までの時間/トークン数 |
| **Adaptation Effectiveness** | 適応前後での情報保存率/品質スコアの変化 |
| **Adaptation Overhead** | 適応判断に消費した追加コスト（トークン/$） |
| **Net Benefit** | (品質向上) - (適応コスト) の純効果 |

### A.4 実装計画

#### A.4.1 新規モジュール

```
orgbench/src/orgbench/
├── adaptive/                  # 新規
│   ├── __init__.py
│   ├── monitor.py             # リアルタイム情報フローモニタリング
│   │   ├── InfoFlowMonitor class
│   │   ├── detect_bottleneck()
│   │   ├── detect_starvation()
│   │   └── detect_plateau()
│   ├── controller.py          # 適応判断ロジック
│   │   ├── RuleBasedController class
│   │   ├── LLMController class
│   │   └── AdaptationDecision dataclass
│   ├── actions.py             # 適応アクションの実行
│   │   ├── spawn_agent()
│   │   ├── reassign_role()
│   │   ├── flatten_hierarchy()
│   │   ├── deepen_hierarchy()
│   │   └── rewire_communication()
│   └── adaptive_orchestrator.py  # 動的オーケストレータ（orchestrator.pyの拡張）
│       └── AdaptiveOrchestrator class
```

#### A.4.2 既存コードへの変更

**orchestrator.py**:
- `run_single()` にモニタリングフック追加（各ステップ後にmonitor呼び出し）
- 適応アクション発火時にフローを動的に書き換える機能

**models.py**:
- `TemplateConfig` を immutable → mutable に変更（動的フロー変更対応）
- `AdaptationEvent` dataclass追加（適応ログ記録用）
- `RunResult` に `adaptations: list[AdaptationEvent]` 追加

### A.5 論文構成案

**タイトル案**: "Self-Reconfiguring Agent Organizations: Information-Theoretic Triggers for Dynamic Structural Adaptation in LLM Multi-Agent Systems"

**構成**:
1. Introduction: 固定 vs 適応組織、人間組織のアナロジー
2. Background: OrgBench（Phase B参照）、情報理論的フレームワーク（Phase B参照）
3. Adaptive Organization Framework: トリガー、アクション、メタコントローラー
4. Experimental Setup: タスク設計、ベースライン
5. Results: 適応 vs 固定、適応パターンの分析
6. Analysis: いつ適応が有効か（タスク特性との関係）
7. Discussion & Future Work

**ターゲット会議**:
- 第1候補: ICLR 2028 (〆切 2027年9月頃)
- 第2候補: NeurIPS 2027 Workshop (〆切 2027年8月頃、Phase Bと同時投稿可能)
- 第3候補: AAMAS 2028

### A.6 スケジュール

| 期間 | マイルストーン | 成果物 |
|------|-------------|--------|
| Week 17-18 (7/5-7/18) | 適応メカニズム設計の詳細化 | 設計書、トリガー閾値のPhase B結果からの導出 |
| Week 19-22 (7/19-8/15) | adaptive/ モジュール実装 | monitor, controller, actions 完成、ユニットテスト |
| Week 23-24 (8/16-8/29) | AdaptiveOrchestrator統合テスト | E2E動作確認（smoke test） |
| Week 25-28 (8/30-9/26) | 本実験実行 | 適応実験200-300回、~$50-100 |
| Week 29-30 (9/27-10/10) | 結果分析 | 適応 vs 固定の比較、適応パターン分析 |
| Week 31-34 (10/11-11/7) | 論文執筆 | ドラフト完成 |
| Week 35-36 (11/8-11/21) | 内部レビュー・修正 | 投稿準備完了 |

---

## 予算・リソース計画

| 項目 | Phase B | Phase A | 合計 |
|------|---------|---------|------|
| 追加実験LLM API | ~$100 | ~$100 | ~$200 |
| Embedding API（情報指標計算） | ~$20 | ~$10 | ~$30 |
| Judge API | ~$30 | ~$30 | ~$60 |
| 合計 | ~$150 | ~$140 | ~$290 |

※ 既存パイロット275回のデータ再分析はコスト$0

---

## リスクと対策

| リスク | 影響度 | 対策 |
|--------|-------|------|
| **情報歪みが統計的に有意でない** | 高 | 既存データの予備分析を最初に行い、効果量を確認。不十分なら指標の改善 or chain長を極端に変化させた実験を追加 |
| **LLMがDPIに従わない**（情報を付加する） | 中 | これ自体が興味深い知見。「LLMチャネルの特殊性」として論文の貢献に |
| **動的適応のオーバーヘッドが利得を上回る** | 中 | Net Benefit指標で定量化。「適応が有効な条件」の同定に論文を軸足移動 |
| **適応トリガーの閾値設定が恣意的** | 中 | Phase Bの理論から導出 + 感度分析。複数閾値での結果を報告 |
| **既存OrgBenchの結果と矛盾** | 低 | 情報理論的説明で既存結果を再解釈。矛盾は新たな知見として報告 |

---

## 投稿戦略まとめ

| 論文 | 内容 | ターゲット | 〆切目安 | 準備期間 |
|------|------|-----------|---------|---------|
| **論文0** (現行) | OrgBench v0.1 ベンチマーク | AAMAS 2027 | 2026年10月 | 現在〜 |
| **論文1** (Phase B) | 情報理論的フレームワーク | NeurIPS 2027 or ICML 2027 | 2027年1-5月 | 2026年3月〜7月 |
| **論文2** (Phase A) | 動的組織適応 | ICLR 2028 | 2027年9月 | 2026年7月〜11月 |

**論文0と論文1は部分的に並行作業可能**: 論文0の仕上げ（Full実験5,500回）をしながらPhase Bの理論構築を進める。

---

## 次のアクション (今週中)

1. [ ] Phase Bの文献調査開始: Data Processing Inequality、Rate-Distortion Theory、情報理論×組織論の既存研究
2. [ ] 既存パイロット275回のデータから情報歪みプロキシ指標の予備計算（semantic similarity decay）
3. [ ] `info_theory/metrics.py` の骨格実装
4. [ ] 理論フレームワークのLaTeXドラフト開始
