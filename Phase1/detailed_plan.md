# Phase 1 詳細実行計画: Information Theory of Agent Organizations

> 作成日: 2026-03-14
> 著者: Koh Shinoda

---

## 0. 現状の制約と前提

### 0.1 既存データの制約

Phase 0のパイロット275回の実行ログには以下の制約がある:

| データ | 保存状態 | Phase 1での利用可否 |
|--------|---------|-------------------|
| `output.md` | 最終出力の全文 | ✅ 利用可能 |
| `messages.jsonl` | 各メッセージの先頭500文字 | ⚠️ 切り詰められている。概要分析には使えるが、full text分析には不十分 |
| `llm_calls.jsonl` | `prompt_summary`(先頭200文字), `response_summary`(先頭200文字), トークン数, コスト | ⚠️ テキスト切り詰め。トークン数は正確 |
| `run_meta.json` | 総コスト、総トークン数、総LLM呼び出し数 | ✅ 利用可能 |

**結論**: 情報理論的分析にはステップ間の**全文テキスト**が必要。以下の2つのアプローチで対処する:

1. **オーケストレータ修正**: `orchestrator.py`を拡張し、各ステップの入出力全文を保存する
2. **追加実験**: 修正後のオーケストレータで、情報理論特化の実験を実行（~60-100回）

### 0.2 利用できる既存データ（追加実験不要）

既存データからでも以下の分析は可能:
- **トークン数ベースのCompression Ratio**: 各ステップの入力トークン数/出力トークン数（llm_calls.jsonlに正確な数値あり）
- **構成間のメッセージ数・エッジ数の差異**: messages.jsonlのメタデータから
- **最終出力の品質 vs 中継段数**: run_meta.json + Judgeスコアの相関

---

## 1. 理論構築

### 1.1 Step 1: 情報処理グラフモデルの定式化

**目標**: エージェント組織を情報処理グラフとして形式的に定義する

**定義**:

```
G = (V, E, f, C)

V = {v₁, ..., vₙ}          エージェントノード集合
E ⊆ V × V                   有向通信エッジ集合
f: V → (X → Y)              各ノードの情報処理関数（LLM）
C: E → ℝ⁺                   各エッジのチャネル容量
```

各エージェント vᵢ をチャネルとしてモデル化:
- 入力 Xᵢ: 前段エージェントの出力 + system prompt + タスク情報
- 出力 Yᵢ: LLMの生成テキスト
- チャネル遷移確率: P(Yᵢ | Xᵢ) — LLMの条件付き生成確率

**成果物**: `Phase1/theory/01_graph_model.md`

### 1.2 Step 2: Information Distortion の定式化

**目標**: 多段中継による情報歪みを数理的に定義し、理論的予測を導出する

**Data Processing Inequality (DPI) の適用**:

チェーン X → Y₁ → Y₂ → ... → Yₙ において:
```
I(X; Yₙ) ≤ I(X; Yₙ₋₁) ≤ ... ≤ I(X; Y₁) ≤ H(X)
```

ここで I(X; Y) は相互情報量、H(X) はエントロピー。

**LLMチャネルの特殊性**:

LLMは単純なノイズチャネルではない。以下の3つのモードがある:
1. **情報保存** (lossless relay): 入力情報をそのまま出力に含める（e.g., 数値の引用）
2. **情報圧縮** (lossy compression): 入力を要約し、重要情報を抽出（e.g., CEO統合ステップ）
3. **情報付加** (information augmentation): 学習済み知識やWeb検索結果から新情報を追加（e.g., Researcher）

DPIは (1)(2) には適用可能だが、(3) ではI(X; Yₖ) < I(X; Yₖ₊₁) となりうる（中継で情報が**増える**）。

**研究問題**: LLMエージェントチェーンにおいて、どの条件でDPIが成立し、どの条件で破れるか？

**理論的予測**:

| 予測 | 根拠 | 検証方法 |
|------|------|---------|
| P1: 情報保存率はchain長に対して単調減少する | DPI | chain長2,3,4,5,6での情報指標比較 |
| P2: mesh通信はchain通信より情報保存率が高い | 冗長経路によるエラー訂正 | 同一タスクでのトポロジー別比較 |
| P3: レビューゲートは情報保存率を改善する | フィードバックチャネルの効果 | レビューあり/なしの比較 |
| P4: 情報付加（Researcher）はDPIの例外を生む | 外部情報源アクセス | Researcher有無のablation |
| P5: Hubノード（CEO）にはボトルネック効果がある | チャネル容量制約 | CEOのinputトークン数 vs 品質 |

**成果物**: `Phase1/theory/02_information_distortion.md`

### 1.3 Step 3: トポロジー別の最適性条件

**目標**: 各トポロジーが最適となる理論的条件を導出する

**Rate-Distortion理論の適用**:

各エージェントの処理を有損失圧縮とみなすと、入力Xに対する再現Ŷの歪みD(X, Ŷ)が、レート R（出力の情報量）との間に:
```
R(D) = min_{P(Ŷ|X): E[d(X,Ŷ)]≤D} I(X; Ŷ)
```

組織全体の歪みは:
- **Chain**: D_total = D₁ + D₂ + ... + Dₙ（各段の歪みが加算的に蓄積）
- **Star**: D_total = max(D_hub, max_i(D_spoke_i))（ハブがボトルネック）
- **Mesh**: D_total = min_path(D_path)（最良経路の歪み）

**成果物**: `Phase1/theory/03_topology_optimality.md`

### 1.4 Step 4: レビューのフィードバック情報理論

**目標**: レビューゲートの効果をフィードバック付きチャネルとして定式化

Shannon (1956) は離散無記憶チャネルのフィードバックが容量を増やさないことを示した。しかしLLMチャネルは:
- **記憶あり** (stateful): system prompt + 会話履歴を保持
- **離散無記憶ではない**: 前の出力が次の入力に影響

→ フィードバック（レビュー差し戻し）が実質的にチャネル容量を増やす可能性がある。

**成果物**: `Phase1/theory/04_review_feedback.md`

---

## 2. 情報指標の設計と実装

### 2.1 指標一覧

| # | 指標名 | 何を測るか | 計算方法 | 必要データ | 難易度 |
|---|--------|-----------|---------|-----------|--------|
| M1 | **Compression Ratio** | 入出力の長さ比 | output_tokens / input_tokens | llm_calls.jsonl ✅既存データ可 | 低 |
| M2 | **Semantic Similarity Decay** | 元タスクからの意味的距離の増加 | cos_sim(emb(task_prompt), emb(step_k_output)) のk依存性 | 全文テキスト必要 | 中 |
| M3 | **Entity Preservation Rate** | 固有名詞の生存率 | NER(input) ∩ NER(output) / NER(input) | 全文テキスト必要 | 中 |
| M4 | **Numerical Fidelity** | 数値の正確な引き継ぎ | regex抽出した数値の入出力間一致率 | 全文テキスト必要 | 低 |
| M5 | **Information Density** | 単位トークンあたりの情報量 | unique n-grams / total tokens | 全文テキスト必要 | 低 |
| M6 | **Cross-Step MI Estimate** | ステップ間の相互情報量 | embeddingベースのMI推定（KSG estimator等） | 全文テキスト必要 | 高 |
| M7 | **Tracer Survival Rate** | 埋め込んだトレーサー情報の生存率 | 入力にinjectedした特定文字列の出力での検出率 | 特別な実験設計必要 | 中 |

### 2.2 実装計画

**新規モジュール**: `orgbench/src/orgbench/info_theory/`

```python
# metrics.py — 各指標の計算
class InfoTheoryMetrics:
    def compression_ratio(input_tokens: int, output_tokens: int) -> float
    def semantic_similarity(text_a: str, text_b: str, model: str = "text-embedding-3-small") -> float
    def entity_preservation_rate(input_text: str, output_text: str) -> float
    def numerical_fidelity(input_text: str, output_text: str) -> float
    def information_density(text: str, n: int = 3) -> float

# trace.py — トレーサー情報のinjectionと検出
class InfoTracer:
    def inject_tracers(task_prompt: str, n_tracers: int = 10) -> tuple[str, list[str]]
    def detect_tracers(output_text: str, tracers: list[str]) -> float

# analyzer.py — 275回分のバッチ分析
class InfoFlowAnalyzer:
    def analyze_run(run_dir: Path) -> RunInfoMetrics
    def analyze_all(results_dir: Path) -> pd.DataFrame
    def plot_distortion_curve(df: pd.DataFrame) -> Figure
    def plot_topology_comparison(df: pd.DataFrame) -> Figure
```

### 2.3 オーケストレータ修正

`orchestrator.py` に以下の変更を加える:

```python
# models.py に追加
@dataclass
class StepTrace:
    """1ステップの全入出力記録"""
    step_index: int
    agent: str
    input_text: str        # 全文（切り詰めなし）
    output_text: str       # 全文
    input_tokens: int
    output_tokens: int
    context_text: str      # ピア出力等の追加コンテキスト（全文）

# RunResult に追加
@dataclass
class RunResult:
    ...
    step_traces: list[StepTrace] = field(default_factory=list)  # 新規追加
```

`orchestrator.py` の `_execute_flow()` 内で、各ステップ実行後に `StepTrace` を記録。
保存先: `results/runs/{run_name}/step_traces.jsonl`

---

## 3. 実験計画

### 3.1 予備分析: 既存データでできること（Week 1-2）

既存275回のデータからすぐに計算可能な指標:

| 分析 | データ源 | 目的 |
|------|---------|------|
| **Compression Ratio by role** | llm_calls.jsonl の input/output tokens | 各役割のエージェントがどれだけ情報を圧縮/拡張するか |
| **Token flow graph** | llm_calls.jsonl のtokenカウント | 構成ごとの情報フロー量の可視化 |
| **Chain length vs quality** | run_meta.json + judge scores | 中継段数と品質の相関（構成間比較） |
| **Hub saturation** | llm_calls.jsonl のCEO入力トークン数 | CEOのinputトークン数と品質の関係 |

**コスト: $0**（既存データの再分析のみ）

### 3.2 追加実験A: 全文保存付き再実験（Week 3-4）

オーケストレータ修正後、以下の構成で再実験:

| 構成 | テーマ | 反復 | 計 | 目的 |
|------|--------|------|---|------|
| anchor (deep/hub) | 5テーマ | 3 | 15 | ベースライン（deep hierarchy） |
| flat_hub | 5テーマ | 3 | 15 | 階層深度の効果 |
| flat_mesh | 5テーマ | 3 | 15 | 通信トポロジーの効果 |
| deep_noreview | 5テーマ | 3 | 15 | レビューゲートの効果 |
| **合計** | | | **60** | |

**推定コスト**: 60回 × ~$0.04/回 = ~$2.4（LLM実行のみ）
**追加コスト**: embedding計算 ~$5-10

### 3.3 追加実験B: Chain長変化実験（Week 5-6）

情報歪みの階層依存性を直接測定するための特殊実験:

**設計**: 同一タスクを異なるchain長で実行

| 構成名 | フロー | chain長 |
|--------|--------|---------|
| chain_2 | CEO → Writer → output | 2 |
| chain_3 | CEO → TL → Writer → output | 3 |
| chain_4 | CEO → TL → Researcher → Writer → output | 4 |
| chain_5 | CEO → TL → Researcher → Writer → CFO review → output | 5 |
| chain_6 | CEO → TL → Researcher → Writer → CFO → CDO review → output | 6 |

| 構成 | テーマ | 反復 | 計 |
|------|--------|------|---|
| chain_2〜6 (5構成) | 5テーマ | 3 | 75 |

**推定コスト**: 75回 × ~$0.03/回 = ~$2.3

### 3.4 追加実験C: トレーサー情報注入実験（Week 5-6）

**設計**: タスクプロンプトに以下の種類のトレーサー情報を埋め込む

| トレーサー種別 | 例 | 測定対象 |
|---------------|---|---------|
| **架空固有名詞** | "競合企業XerionTech社の年間売上は240億円" | 固有名詞の生存率 |
| **架空数値** | "ターゲット市場のTAMは3,847億円" | 数値の正確な引き継ぎ |
| **架空事実** | "2025年の法改正により電子帳簿保存が全面義務化" | 事実情報の生存率 |
| **制約条件** | "初期投資額は5,000万円以内に抑えること" | 制約の遵守率 |

各テーマに10個のトレーサーを埋め込み、各ステップの出力で検出率を追跡。

| 構成 | テーマ | 反復 | 計 |
|------|--------|------|---|
| anchor, flat_hub, flat_mesh, chain_4 (4構成) | 3テーマ（トレーサー付き） | 3 | 36 |

**推定コスト**: 36回 × ~$0.04/回 = ~$1.4

### 3.5 実験コスト合計

| 実験 | 回数 | LLMコスト | Embeddingコスト | 計 |
|------|------|----------|----------------|---|
| 予備分析 | 0（既存データ） | $0 | $0 | $0 |
| 実験A: 全文保存再実験 | 60 | ~$2.4 | ~$5 | ~$7 |
| 実験B: Chain長変化 | 75 | ~$2.3 | ~$5 | ~$7 |
| 実験C: トレーサー注入 | 36 | ~$1.4 | ~$2 | ~$3 |
| Judge評価（追加実験分） | 171×2 | ~$5 | — | ~$5 |
| **合計** | **171** | **~$11** | **~$12** | **~$22** |

※ 当初見積もり$150より大幅に安い。Phase 0のパイロットで使ったモデル（Haiku/GPT-4o-mini/Gemini Flash）が安価なため。

---

## 4. 分析計画

### 4.1 分析A: Information Distortion Curve（理論予測P1の検証）

**仮説**: 情報保存指標はchain長dに対して単調減少する

**手法**:
1. 実験BのChain長2-6のデータから、各chain長でのM2-M7指標を算出
2. d vs 各指標のプロットを作成
3. 減衰モデルのフィッティング:
   - 線形: f(d) = a - b·d
   - 指数: f(d) = a·exp(-b·d)
   - 対数: f(d) = a - b·log(d)
4. AIC/BICで最適モデルを選択

**予想される結果**: 指数減衰が最もフィットする（各段で一定割合の情報が失われる）

### 4.2 分析B: トポロジー別情報保存効率（理論予測P2の検証）

**仮説**: mesh > star > chain の順に情報保存率が高い

**手法**:
1. 実験Aの構成別データから、M2-M7指標を算出
2. Kruskal-Wallis検定でトポロジー間の差異を検定
3. 事後検定で対比較

### 4.3 分析C: レビューゲートのフィードバック効果（理論予測P3の検証）

**仮説**: レビューゲートは情報保存率を改善する

**手法**:
1. anchor (レビューあり) vs deep_noreview (レビューなし) の比較
2. 特にレビュー差し戻しが発生したケースでの改善幅を計測
3. レビュー前後での指標変化量

### 4.4 分析D: トレーサー生存分析（理論予測P1の直接検証）

**仮説**: トレーサーの生存率はchain長と負の相関を示す

**手法**:
1. 実験Cのデータから、各ステップでのトレーサー検出率を算出
2. 構成別×トレーサー種別のヒートマップ作成
3. 生存曲線（Kaplan-Meierアナロジー）の作成

### 4.5 分析E: CEOボトルネック分析（理論予測P5の検証）

**仮説**: CEOの入力トークン数が多い（情報過多の）とき、最終品質が低下する

**手法**:
1. 既存275回のllm_calls.jsonlから、CEO最終統合ステップのinput_tokensを抽出
2. input_tokens vs overall_quality の散布図・相関分析
3. 閾値効果（input_tokensがある値を超えると品質が低下する）のbreakpoint分析

### 4.6 分析F: LLMのDPI違反分析（理論予測P4の検証）

**仮説**: Researcher（外部情報源アクセスあり）のステップでは、相互情報量が増加する

**手法**:
1. Researcher前後のsemantic similarityの変化を測定
2. Web検索ありのResearcherと、検索なしエージェントの比較
3. DPI違反の条件の同定

---

## 5. 論文構成

### 5.1 タイトル候補

1. "The Information-Theoretic Cost of Hierarchy: Modeling LLM Multi-Agent Organizations as Communication Networks"
2. "Information Flows Through Agent Hierarchies: A Channel-Theoretic Analysis of LLM Multi-Agent Systems"
3. "Does Depth Destroy Information? An Information-Theoretic Analysis of Hierarchical LLM Agent Organizations"

### 5.2 構成（8ページ + 参考文献）

| セクション | ページ | 内容 |
|-----------|--------|------|
| 1. Introduction | 1 | 「なぜ浅い階層が良いのか」の因果的説明の欠如。情報理論的アプローチの提案 |
| 2. Related Work | 0.75 | 情報理論×組織論（Galbraith）、DPI、LLMの情報処理特性 |
| 3. Theoretical Framework | 1.5 | 情報処理グラフモデル、Information Distortion定式化、トポロジー別予測 |
| 4. Information Metrics | 0.75 | M1-M7の定義と計算方法 |
| 5. Experimental Setup | 1 | 実験A/B/C/Dの設計、OrgBenchとの関係 |
| 6. Results | 1.5 | 分析A-Fの結果、理論予測 vs 実測 |
| 7. Discussion | 1 | LLMはDPIに従うか？設計指針。限界と将来展望 |
| 8. Conclusion | 0.5 | |

### 5.3 主要なFigure/Table（予定）

| # | 種類 | 内容 |
|---|------|------|
| Fig.1 | 概念図 | エージェント組織の情報処理グラフモデル。各ノード=チャネル、エッジ=情報フロー |
| Fig.2 | 折れ線グラフ | **Information Distortion Curve**: chain長 d vs 各情報指標（メインの結果） |
| Fig.3 | 棒グラフ | トポロジー別（chain/star/mesh）の情報保存率比較 |
| Fig.4 | ヒートマップ | トレーサー生存率: 構成×トレーサー種別 |
| Fig.5 | 散布図 | CEOの入力トークン数 vs 最終品質（ボトルネック効果） |
| Fig.6 | 折れ線グラフ | ステップごとのsemantic similarity decay（DPI検証） |
| Tab.1 | 表 | 理論予測 vs 実測の一致度まとめ |
| Tab.2 | 表 | 情報指標と品質スコアの相関行列 |

---

## 6. 週次スケジュール

### Week 1 (3/14-3/21): 予備分析 + 理論構築開始

- [ ] 既存275回データのCompression Ratio分析（M1）
- [ ] Token flow graphの可視化（構成別）
- [ ] CEO input tokens vs quality の散布図作成（分析E）
- [ ] 情報処理グラフモデルの数学的定式化ドラフト
- [ ] DPI, Rate-Distortion Theory の文献精読
  - Cover & Thomas "Elements of Information Theory" Ch.2 (Entropy), Ch.7 (Channel Capacity), Ch.10 (Rate-Distortion)
  - Shannon 1956 "The Zero Error Capacity of a Noisy Channel"

### Week 2 (3/22-3/28): 理論構築 + オーケストレータ修正

- [ ] Information Distortion の定式化完了
- [ ] トポロジー別最適性条件の導出
- [ ] `orchestrator.py` の修正（StepTrace全文保存）
- [ ] `info_theory/metrics.py` のM1, M4, M5実装
- [ ] ユニットテスト

### Week 3 (3/29-4/4): 実験A実行 + 指標実装

- [ ] 実験A（全文保存再実験60回）実行
- [ ] `info_theory/metrics.py` のM2, M3実装（embedding API使用）
- [ ] M6 (MI推定) の実装方針決定（KSG vs MINE vs embeddingベース簡易法）
- [ ] ユニットテスト

### Week 4 (4/5-4/11): 実験A分析 + 実験B/C準備

- [ ] 実験Aデータの情報指標計算
- [ ] 構成別の情報保存率比較（分析B, C）
- [ ] 実験B用のchain_2〜6テンプレートYAML作成
- [ ] 実験C用のトレーサー付きテーマYAML作成
- [ ] `info_theory/trace.py` 実装

### Week 5 (4/12-4/18): 実験B/C実行

- [ ] 実験B（Chain長変化75回）実行
- [ ] 実験C（トレーサー注入36回）実行
- [ ] Judge評価（実験A/B/C合計171回×2）
- [ ] Information Distortion Curve のプロット（分析A）

### Week 6 (4/19-4/25): 全分析完了

- [ ] 分析A-F の全結果をまとめる
- [ ] 理論予測 vs 実測の突き合わせ
- [ ] Figure/Tableの作成
- [ ] 減衰モデルフィッティング
- [ ] 統計検定の実施

### Week 7-8 (4/26-5/9): 論文執筆

- [ ] LaTeXドラフト執筆（Sec 1-7）
- [ ] Figure/Tableの仕上げ
- [ ] Related Workの精密化
- [ ] 内部レビュー（指導教員等）

### Week 9-10 (5/10-5/23): 修正 + 投稿準備

- [ ] レビューフィードバック反映
- [ ] 実験の追加（必要に応じて）
- [ ] 最終校正
- [ ] 投稿先の最終決定（AAMAS 2027 / NeurIPS 2027 / ICML 2027）

---

## 7. 文献リスト（Phase 1で精読すべきもの）

### 7.1 情報理論の基礎

| # | 文献 | 関連 |
|---|------|------|
| 1 | Cover & Thomas, "Elements of Information Theory" (2006) | DPI, Channel Capacity, Rate-Distortion |
| 2 | Shannon, "A Mathematical Theory of Communication" (1948) | チャネルモデルの基礎 |
| 3 | Shannon, "The Zero Error Capacity of a Noisy Channel" (1956) | フィードバック付きチャネル |

### 7.2 LLMの情報理論的分析

| # | 文献 | 関連 |
|---|------|------|
| 4 | Xu et al., "A Theory of LLM Compression" (2024, if exists) | LLMの情報圧縮特性 |
| 5 | Deletang et al., "Language Modeling Is Compression" (2024) | LLM=圧縮の観点 |
| 6 | Li et al., "The Entropy of Language Models" (2023-2025) | LLM出力のエントロピー特性 |

### 7.3 組織の情報理論

| # | 文献 | 関連 |
|---|------|------|
| 7 | Galbraith, "Designing Complex Organizations" (1973) | 情報処理理論の原典 |
| 8 | Daft & Lengel, "Organizational Information Requirements" (1986) | メディアリッチネス理論 |
| 9 | March & Simon, "Organizations" (1958) | 限定合理性と情報処理 |

### 7.4 マルチエージェントの情報フロー

| # | 文献 | 関連 |
|---|------|------|
| 10 | MacNet (ICLR 2025) — Qian et al. | DAGベースのトポロジー |
| 11 | G-Designer (ICML 2025) — Yao et al. | 適応的トポロジー生成 |
| 12 | Deletang et al., "Language Modeling Is Compression" (ICLR 2024) | 言語モデル＝圧縮 |

---

## 8. 成功基準

Phase 1は以下の条件を**少なくとも3つ**満たせば成功とする:

| # | 基準 | 検証方法 |
|---|------|---------|
| S1 | Information Distortion Curveがchain長に対して有意な減少傾向を示す | p < 0.05 for linear/exponential fit |
| S2 | トポロジー間で情報保存率に有意差がある | Kruskal-Wallis p < 0.05 |
| S3 | トレーサー生存率がchain長と有意な負の相関を示す | Spearman ρ < -0.3, p < 0.05 |
| S4 | 情報指標と品質スコアの間に有意な正の相関がある | Pearson r > 0.3, p < 0.05 |
| S5 | CEOの入力トークン数に閾値効果が観察される | breakpoint回帰で有意なbreakpoint |
| S6 | LLMのDPI違反条件（情報付加）が同定される | Researcher有無のablation |

### 失敗した場合のプランB

- S1-S3が全て棄却された場合 → 「LLMチャネルはDPIに従わない」という否定的結果自体を主貢献とする。LLMが情報を保存・付加する条件の分析に軸足を移す
- 効果量が小さすぎる場合 → chain長を極端に長くした実験（chain_8, chain_10）を追加
- 情報指標の妥当性が疑わしい場合 → 人間評価で情報保存率を直接評価するサブセット実験を追加

---

## 付録: 今すぐ始められること

### A. 既存データの予備分析スクリプト（10分で書ける）

```python
"""Phase 1 予備分析: 既存275回のCompression Ratioとtoken flow"""
import json
from pathlib import Path
from collections import defaultdict

results_dir = Path("orgbench/results/runs")
config_stats = defaultdict(lambda: defaultdict(list))

for run_dir in sorted(results_dir.iterdir()):
    if not run_dir.is_dir():
        continue
    config = run_dir.name.rsplit("_rep", 1)[0].rsplit("_t0", 1)[0]

    calls_path = run_dir / "llm_calls.jsonl"
    if not calls_path.exists():
        continue

    with open(calls_path) as f:
        for line in f:
            call = json.loads(line)
            agent = call["agent"]
            cr = call["output_tokens"] / call["input_tokens"] if call["input_tokens"] > 0 else 0
            config_stats[config][agent].append({
                "compression_ratio": cr,
                "input_tokens": call["input_tokens"],
                "output_tokens": call["output_tokens"],
            })

# 結果出力
for config, agents in sorted(config_stats.items()):
    print(f"\n=== {config} ===")
    for agent, stats in sorted(agents.items()):
        avg_cr = sum(s["compression_ratio"] for s in stats) / len(stats)
        avg_in = sum(s["input_tokens"] for s in stats) / len(stats)
        print(f"  {agent:12s}: CR={avg_cr:.2f}, avg_input={avg_in:.0f}")
```

このスクリプトを**今日中に実行して**、Compression Ratioの概要を把握することを推奨。理論構築の方向性を実データで裏付けられる。
