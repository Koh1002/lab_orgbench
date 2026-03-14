# Research Plan: Information Flow Design Patterns in LLM Multi-Agent Systems and Their Impact on Collective Decision Quality

**Target Venue:** IEEE International Conference on Agents (ICA) / AAAI / AAMAS
**Document Type:** Research Plan (pre-submission draft outline)
**Version:** v0.2
**Date:** 2026-03-11

---

## 1. Paper Structure (IEEE Conference Format)

### Title (Working)

**"Does Information Flow Design Matter? Isolating the Effect of Communication and Authority Patterns on Multi-Agent Collective Decision Quality"**

Alternative titles:
- "Information Flow as a Hyperparameter: How Message Routing and Authority Patterns Shape LLM Agent Collectives"
- "OrgBench: A Controlled Testbed for Information Flow Design in Multi-Agent Systems"

---

## 2. Abstract (Draft, ~150 words)

Multi-agent LLM systems increasingly adopt organizational metaphors—hierarchies, roles, review gates—yet the isolated effect of information flow design (message routing and authority patterns) on output quality remains unquantified. Human organizational theory has studied these patterns for decades, but confounding factors (culture, motivation, politics) have prevented controlled experiments. LLM agents, lacking these confounds, offer a **pure experimental system** for isolating information flow effects. We present **OrgBench**, a framework for systematically comparing information flow configurations by running identical business analysis tasks across varied designs. Using a configurable multi-agent system where 6 LLM-powered agents operate under defined communication topologies, authority structures, and review protocols, we evaluate **55 configurations** (including a single-agent baseline) on **20 standardized business themes** with **5 replications** per condition. We assess output quality through LLM-as-Judge evaluation validated by human assessment. Our results reveal that [TBD: key findings]. We release OrgBench as an open benchmark.

---

## 3. Introduction

### 3.1 Research Motivation

既存のマルチエージェント研究の多くは、以下に集中している:
- エージェント間の協調プロトコル（議論、投票、合意形成）
- 単一タスクの分割と並列処理
- ベンチマーク（コーディング、数学、推論）

**見落とされている問い:**
> 同じエージェント群でも、**情報フロー設計（メッセージの経路・権限の配分・レビューの構成）** を変えると、出力の質はどう変わるのか？

これは人間の組織論（Mintzberg, 1979; Galbraith, 1973）では数十年研究されてきたが、人間組織には文化・動機・政治・暗黙知などの交絡因子が不可分に組み込まれており、**情報フロー設計の純粋な効果を分離する制御実験は不可能だった**。

LLMエージェントはこれらの交絡因子を構造的に排除した**純粋な情報フロー実験系**を提供する。本研究は、人間組織における「組織構造」の効果のうち、**情報フロー設計に帰着する成分を初めて分離・定量化する**。

### 3.2 Why This Matters Now

- 2025-2026年、企業のAIエージェント導入が急速に進行中（OpenAI Agents SDK、Google A2A、Anthropic MCP等のインフラ整備）
- CrewAI (25k+ Stars)、LangGraph (120k+ Stars) の利用者の大半が「最適な構造がわからない」状態で設計している
- Wang et al. (ACL 2024) は「強力なプロンプトの単一エージェントがマルチエージェント討論に匹敵する」ことを示しており、**マルチエージェント構造自体の付加価値を定量的に問い直す必要がある**

### 3.3 Research Questions

| # | Research Question |
|---|-------------------|
| **RQ0** | マルチエージェント情報フロー設計は、最適化された単一エージェントに対して付加価値を持つか？ |
| **RQ1** | 情報フロー・トポロジー（階層型/フラット型/マトリクス型）は、ビジネス提案の品質にどの程度影響するか？ |
| **RQ2** | レビューゲートの構成（財務重視/技術重視/バランス型/なし）は、提案の実現可能性・新規性にどう作用するか？ |
| **RQ3** | エージェント間のモデル異質性（同一モデル vs 混合モデル）は、提案の多様性・内部一貫性にどう影響するか？ |
| **RQ4** | 最適な情報フロー設計はタスクの不確実性水準に依存するか？（不確実性×構造の交互作用 — コンティンジェンシー理論の検証） |

### 3.4 Contributions

1. **理論的貢献**: LLMエージェントを人間組織の交絡因子を排除した「純粋な情報フロー実験系」として位置づける視座の確立。組織構造の効果のうち、情報フロー設計に帰着する成分を分離。
2. **OrgBench**: 情報フロー設計パターンを独立変数として制御可能な、初のマルチエージェントベンチマーク（単一エージェントベースライン含む）
3. **実験結果**: 55構成×20テーマ×5反復の体系的比較（LLM-as-Judge＋人間バリデーション）
4. **設計指針**: 「このタスク不確実性水準にはこの情報フロー設計が適する」という実践的ガイドライン
5. **再現パッケージ**: 全コード・設定・評価データを公開

### 3.5 Scope and Honest Framing

本研究が扱うのは「情報フロー設計パターンの効果」であり、人間の「組織構造」の全体ではない。人間組織の組織構造には、文化・信頼・動機づけ・政治的行動・暗黙知の共有など、LLMエージェントには存在しない要素が不可分に組み込まれている。本研究の知見を人間組織に直接一般化することはできない。

ただし逆に言えば、人間組織では不可能だった「情報フロー設計の純粋効果の測定」を、LLMエージェントが初めて可能にしたという点に本研究の方法論的価値がある。

---

## 4. Related Work

### 4.1 Multi-Agent LLM Systems

| 研究 | 構造 | 本研究との差異 |
|------|------|--------------|
| AutoGen (Wu et al., 2023) | 対話ベース、フラット | 情報フロー設計の比較なし |
| MetaGPT (Hong et al., 2023) | ソフトウェア開発ロール固定 | 構造が1つ固定、比較不可 |
| ChatDev (Qian et al., 2023) | ウォーターフォール型固定 | 開発特化、構造の変数化なし |
| CAMEL (Li et al., 2023) | 2エージェント対話 | 組織を形成していない |
| AgentVerse (Chen et al., 2023) | グループ討論 | フラット構造のみ |
| MacNet (Qian et al., 2024) | DAGトポロジー | 通信トポロジーのみ。権限・レビュー構造なし |
| G-Designer (Yao et al., 2024) | GNN自動設計 | タスク特化最適化。情報フロー設計の比較ではない |
| MultiAgentBench (ACL 2025) | 協調・競合ベンチマーク | 通信プロトコルレベル。権限構造は変数に含まれない |

**Gap:** 情報フロー設計パターン（通信トポロジー＋権限構造＋レビュー構成）を独立変数として体系的に比較した研究は存在しない。

### 4.2 Single-Agent Baselines: The Critical Counterargument

本研究の前提（マルチエージェント構造が品質に影響する）に対する最も強い反論：

- **Wang et al. (ACL 2024)**: 強力なプロンプトの単一エージェントがマルチエージェント討論とほぼ同等
- **EMNLP 2024**: 予算制約下ではCoT+Self-Consistencyがマルチエージェント討論より効率的
- **2025年複数研究**: 単純多数決投票が討論プロセスの改善の大部分を説明

→ これらの知見を踏まえ、**単一エージェントベースラインを実験に含めることが不可欠**。マルチエージェントの付加価値が検出されない場合も、それ自体が重要な実証的知見となる。

### 4.3 Organizational Theory (Human)

本研究は以下の理論を「LLMエージェントでの検証対象」ではなく、**「情報フロー設計パターンの分類と仮説生成の源泉」**として活用する：

| 理論 | 本研究での活用 |
|------|-------------|
| Galbraith情報処理理論 (1973) | **中心理論**。情報処理要求と処理能力のフィットという枠組みを直接適用 |
| Burns & Stalker (1961) | 機械的（固定パイプライン）vs 有機的（動的メッシュ）の設計パターン分類 |
| Lawrence & Lorsch (1967) | タスク不確実性×構造の交互作用仮説（RQ4）の理論的根拠 |
| Steiner (1972) | プロセスロス概念 — 調整コストの定量化フレーム |
| Woolley et al. (2010) | 集合知因子"c" — 相互作用の質がメンバー能力の総和より重要という仮説 |
| Leavitt (1951) | 通信ネットワーク構造と問題解決の古典的実験 — 本研究の直接的先行 |

**重要な区別**: 本研究はこれらの理論を「LLMエージェントでも成り立つか検証する」のではなく、「情報フロー設計という部分問題に対して、これらの理論が示唆する仮説を実験的に検証する」。人間組織の交絡因子（文化・動機・政治）が除去された状態での検証であり、結果が人間組織に直接一般化されるものではない。

### 4.4 通信トポロジー ≠ 情報フロー設計（概念の整理）

既存研究（MacNet, G-Designer, MultiAgentBench）は「通信トポロジー」（誰が誰にメッセージを送れるか）を変数化しているが、「情報フロー設計」はそれより広い概念であり、以下の3層を含む：

| 層 | 内容 | 例 |
|---|------|---|
| **通信トポロジー** | 物理的な通信可能性 | Hub-and-spoke / Mesh |
| **権限構造** | 誰が決定権を持ち、誰がレビューするか | 階層型 / フラット型 / マトリクス型 |
| **レビュープロトコル** | 品質管理の構成と段数 | 財務重視 / 技術重視 / バランス / なし |

本研究はこれら3層を独立変数として直交的に操作する。

---

## 5. Methodology

### 5.1 System: OrgBench Framework

PJ_Anima の agent-core をベースに、以下を実現する:

```
OrgBench
├── 情報フロー設計テンプレート（Independent Variable）
│   ├── hierarchy_deep.yaml      — 深い階層（CEO→VP→Manager→Worker）
│   ├── hierarchy_flat.yaml      — フラット（CEO→全Worker直轄）
│   ├── matrix.yaml              — マトリクス（機能×プロジェクト）
│   ├── review_finance.yaml      — CFO重視（財務ゲート2段）
│   ├── review_tech.yaml         — CDO重視（技術ゲート2段）
│   ├── review_balanced.yaml     — バランス型（CFO+CDO並列）
│   ├── review_none.yaml         — レビューなし（コントロール群）
│   ├── homogeneous_claude.yaml  — 全員Claude
│   ├── homogeneous_gpt.yaml     — 全員GPT
│   ├── heterogeneous_mix.yaml   — 混合モデル
│   ├── single_agent_strong.yaml — 単一エージェントベースライン
│   └── ...
│
├── テーマセット（Controlled Input）
│   ├── healthcare_ai.md
│   ├── fintech_senior.md
│   ├── edtech_emerging.md
│   ├── sustainability_tech.md
│   └── ... (20テーマ、不確実性水準の客観指標付き)
│
├── 評価基準（Dependent Variable）
│   ├── llm_judge.py             — LLM-as-Judge（メイン評価）
│   ├── automated_metrics.py     — 自動メトリクス
│   └── human_eval_rubric.md     — 人間バリデーション用ルーブリック
│
└── 実行エンジン
    └── competition_runner.py     — N構成×Mテーマ×K反復を並列実行
```

### 5.2 Independent Variables（操作変数）

| 変数 | 水準 | 説明 |
|------|------|------|
| **Topology** | 3水準 | Deep Hierarchy / Flat / Matrix |
| **Review Gate** | 3水準 | Finance-heavy / Tech-heavy / Balanced |
| **Model Heterogeneity** | 3水準 | Homogeneous-A / Homogeneous-B / Heterogeneous |
| **Communication** | 2水準 | Hub-and-spoke / Mesh (peers可) |

→ 完全組み合わせ: 3×3×3×2 = **54構成（マルチエージェント）**

**＋ 単一エージェントベースライン（1構成）:**

| ベースライン | 説明 |
|-------------|------|
| **Single-Agent-Strong** | 最高性能モデル（Claude Sonnet）に、6体分の全役割の知見を統合した最適化プロンプトを付与。同一テーマを単体で処理。 |

→ **合計: 55構成**

**反復回数:**
- 各条件 **5回反復**（LLM出力の確率的揺らぎの統制）
- 実験規模: 55構成 × 20テーマ × 5反復 = **5,500回実行**
- コスト概算: 5,500 × $0.07 = **$385**（約¥58,000）

**反復回数の根拠:**
- temperature=0.7でのLLM出力のばらつきを考慮し、観察された差が構造の効果か確率的揺らぎかを統計的に区別するために必要
- 中程度の効果量（η²=.06）を検出するための検定力分析に基づき、各セルに最低5観測値を確保
- 予算上限$500以内に収まる最大反復数

### 5.3 Controlled Variables（統制変数）

| 変数 | 統制方法 |
|------|---------|
| テーマの不確実性 | 客観指標3種 + 人間5名の主観評価で多面的に測定（§5.6参照） |
| エージェント数 | 全マルチエージェント構成で6体に固定 |
| LLM温度パラメータ | 全実行で temperature=0.7 に固定 |
| トークン上限 | 各エージェント max_tokens=2048 に固定 |
| 実行時間上限 | 10分/フローに固定 |
| Web検索 | 全構成で同一 Tavily API（**検索結果のキャッシュによる完全統制**） |

### 5.4 Dependent Variables（評価指標）

#### 5.4.1 LLM-as-Judge（メイン評価）

全5,500出力に対してスケーラブルに適用。バイアス対策として以下の設計を採用：

| 設計要素 | 対策 |
|---------|------|
| 評価LLMと生成LLMの分離 | 生成に使用していないLLM（例: GPT-4.1）を評価者に使用 |
| 複数評価LLMの合議 | 2種のLLMで独立評価し、一致度を報告 |
| 匿名化 | 評価時に構成名・モデル名を除去（ブラインド評価） |
| ルーブリック標準化 | 6軸の評価基準を詳細なルーブリックで定義 |

| 評価軸 | 1-5スケール | 説明 |
|--------|-----------|------|
| **Feasibility** | 1-5 | 実現可能性 |
| **Novelty** | 1-5 | 新規性・独自性 |
| **Market Insight** | 1-5 | 市場理解の深さ |
| **Financial Rigor** | 1-5 | 財務分析の妥当性 |
| **Technical Depth** | 1-5 | 技術的な深さ・正確さ |
| **Overall Quality** | 1-5 | 総合評価 |

#### 5.4.2 自動メトリクス

| メトリクス | 測定方法 | 何を測るか |
|-----------|---------|-----------|
| **Completeness Score** | 提案資料の必須セクション充足率（チェックリスト照合） | 網羅性 |
| **Specificity Score** | 固有名詞・数値・具体例の密度 | 具体性 |
| **Diversity (across orgs)** | 同一テーマでの構成間の提案類似度（embedding cosine） | 構造が異なる出力を生むか |
| **Communication Efficiency** | 完走までの総メッセージ数・LLM呼び出し回数 | 情報フロー設計の効率性 |
| **Cost Efficiency** | 品質スコア / 総コスト | コスパ |

#### 5.4.3 人間バリデーション（LLM-as-Judgeの妥当性検証）

LLM-as-Judge評価の妥当性を検証するためのサブセット人間評価：

- 対象: 代表的な11構成（54構成の各変数の代表水準9 + 単一エージェント + No-Review）× 5テーマ × 1反復分 = **55提案**
- 評価者: 3名以上（ビジネス/技術バックグラウンド混合）
- 同一ルーブリック（6軸）で評価
- 報告指標:
  - LLM-as-Judge評価と人間評価のSpearman相関（各軸）
  - Fleiss' κ（人間評価者間信頼性）
  - κ < 0.4の場合の対処: 評価軸の統合・再定義、評価者トレーニングの追加、またはその軸の報告を探索的に降格

### 5.5 Analysis Plan

| 分析 | 手法 | 対応するRQ |
|------|------|-----------|
| **単一 vs マルチの比較** | Welch's t-test（Single-Agent-Strong vs 各マルチ構成） | **RQ0** |
| 構造間の品質差 | One-way ANOVA + Tukey HSD | RQ1 |
| レビューゲートの効果 | Two-way ANOVA (Gate × Quality dimension) | RQ2 |
| レビューの付加価値 | No-Review条件（コントロール群）との対比較 | RQ2 |
| モデル異質性の効果 | Kruskal-Wallis + Mann-Whitney U | RQ3 |
| 不確実性×構造の交互作用 | Two-way ANOVA + 交互作用プロット | RQ4 |
| 効果量 | Cohen's d / η² | 全RQ |
| 通信パターン分析 | グラフ分析（次数分布、パス長） | 探索的 |

**結果シナリオの事前準備:**

| シナリオ | 解釈 | 論文ストーリー |
|---------|------|-------------|
| **A: 単一エージェント ≈ 最良マルチ構成** | 情報フロー設計の効果はプロンプト設計で代替可能 | 「構造よりプロンプトが重要」という実践的知見。否定的結果だが設計者にとって有用 |
| **B: マルチ構成間に有意差あり、単一を上回る** | 情報フロー設計は独立した品質決定因子 | メインストーリー。設計指針を提供 |
| **C: マルチ構成間に有意差あるが、単一に劣る** | マルチエージェントの調整ロスが利益を上回る | Steiner的プロセスロスの定量化として報告 |
| **D: 交互作用あり（不確実性依存）** | コンティンジェンシー理論のLLM版が成立 | 最も豊かな結果。タスク特性→推奨設計の対応表を提供 |

### 5.6 タスク不確実性の操作化（RQ4対応）

RQ4（コンティンジェンシー理論の検証）の鍵となる「タスクの不確実性」を、**主観評価だけでなく客観指標で多面的に測定**する：

#### 客観指標（3種）

| 指標 | 測定方法 | 理論的根拠 |
|------|---------|-----------|
| **情報入手可能性** | Tavily API検索ヒット数（テーマ名 + 関連キーワード5つの平均） | Galbraith: 不確実性 = 事前に入手できない情報の量 |
| **知識蓄積度** | Semantic Scholar API での関連学術論文数 | 学術知識の蓄積が少ないドメインほど不確実性が高い |
| **市場成熟度** | Crunchbase等での関連スタートアップ・企業数（手動調査） | Lawrence & Lorsch: 市場の安定性 |

#### 主観指標（1種）

| 指標 | 測定方法 |
|------|---------|
| **人間評定難易度** | 評価者5名による5段階評価（「このテーマでビジネス提案を書く難しさ」） |

#### 統合方法

- 客観指標3種を標準化（z-score）後に平均し、「客観的不確実性スコア」を算出
- 主観指標との相関を報告し、構成概念妥当性を検証
- RQ4の分析では客観スコアでテーマを3群（Low / Medium / High不確実性）に分類
- 主観スコアでの分類でも同様の分析を行い、結果のロバスト性を確認

---

## 6. Expected Results & Hypotheses

| 仮説 | 根拠 | 検証方法 |
|------|------|---------|
| **H0**: 単一エージェントベースラインは最良のマルチ構成と品質差なし | Wang et al. (ACL 2024) | Single vs Best-Multi の Welch's t-test |
| **H1**: 深い階層はCompleteness↑だがNovelty↓ | Leavitt (1951) の車輪型実験、レビュー層増加→保守化の知見 | Topology × {Completeness, Novelty} |
| **H2**: フラット構成はCommunication Efficiency↑ | 中間ノード不在→メッセージ数削減 | Topology × Message Count |
| **H3**: 財務重視ゲートはFeasibility↑、技術重視はTechnical Depth↑ | 専門フィルターの選択的効果 | Gate × {Feasibility, Technical Depth} |
| **H4**: モデル異質性はDiversity↑、Internal Consistency↓ | 異なるLLMの「思考の癖」が多様性を生む一方、矛盾も増える | Heterogeneity × {Diversity, Consistency} |
| **H5**: 最適設計は不確実性水準に依存する | Lawrence & Lorsch (1967), Burns & Stalker (1961) | Uncertainty Level × Topology 交互作用 |

---

## 7. Implementation Plan

### 7.1 OrgBench 開発（2週間）

| # | タスク | 工数 | 成果物 |
|---|--------|------|--------|
| 1 | 情報フロー設計テンプレートYAML 55種の定義（含: 単一エージェント） | 2日 | `orgbench/templates/*.yaml` |
| 2 | テーマセット20種の作成＋不確実性の客観指標測定 | 2日 | `orgbench/themes/*.md`, `orgbench/themes/uncertainty_scores.csv` |
| 3 | CompetitionRunner実装（並列Orchestrator拡張、反復制御） | 3日 | `orgbench/runner.py` |
| 4 | LLM-as-Judge評価パイプライン実装 | 2日 | `orgbench/judge/` |
| 5 | 自動評価メトリクス実装 | 1日 | `orgbench/metrics/` |
| 6 | 人間バリデーション用ルーブリック＋UIフォーム | 1日 | `orgbench/eval/` |
| 7 | 結果集約＋統計分析パイプライン | 2日 | `orgbench/analysis/` |
| 8 | 検索結果キャッシュ（統制用） | 1日 | `orgbench/cache/` |

### 7.2 実験実行（2週間）

| # | タスク | 工数 | コスト | 目的 |
|---|--------|------|--------|------|
| 1 | **パイロット実行**（11構成×5テーマ×5反復 = 275回） | 2日 | ~$19 | 効果量の事前推定、実験系の検証 |
| 2 | パイロット結果分析 → 本実験のGo/No-Go判断 | 1日 | — | 効果量が極小の場合、反復数増加 or 研究の方向転換を判断 |
| 3 | **本実行**（55構成×20テーマ×5反復 = 5,500回） | 3日 | ~$385 | — |
| 4 | LLM-as-Judge評価（5,500提案×2評価LLM） | 1日 | ~$40 | — |
| 5 | 人間バリデーション評価（55提案×3名） | 3日 | 評価者依頼 | — |
| 6 | 統計分析＋可視化 | 3日 | — | — |

### 7.3 論文執筆（2週間）

| # | セクション | 工数 |
|---|-----------|------|
| 1 | Introduction + Related Work | 3日 |
| 2 | Methodology（OrgBench Framework） | 2日 |
| 3 | Results + Discussion | 4日 |
| 4 | Figures + Tables | 2日 |
| 5 | Abstract + Conclusion + 校正 | 3日 |

### 7.4 Target Venues & Deadlines

| Venue | 種別 | 想定締切 | 採択率 | 適合度 |
|-------|------|---------|--------|--------|
| **AAMAS 2027** | Top conference (Multi-Agent) | 2026年10月頃 | ~25% | ★★★★★ |
| **AAAI 2027** | Top conference (AI general) | 2026年8月頃 | ~20% | ★★★★☆ |
| **IEEE ICA 2027** | IEEE conference (Agents) | TBD | ~30% | ★★★★★ |
| **NeurIPS 2026 Workshop** | Workshop (lower bar) | 2026年9月頃 | ~40% | ★★★★☆ |
| **arXiv preprint** | Preprint | いつでも | — | ★★★★★ |

**推奨戦略:**
1. まず arXiv にプレプリント投稿（先行性確保）
2. AAMAS 2027 をメインターゲット
3. 不採択の場合 IEEE ICA にリサブミット

---

## 8. Novelty Statement

本研究の新規性は以下の4点:

1. **視座の新しさ**: LLMエージェントを「組織の模倣物」としてではなく、**人間組織の交絡因子を排除した「純粋な情報フロー実験系」**として位置づける。これにより、組織論が60年間分離できなかった「情報フロー設計の純粋効果」の測定を初めて可能にする。

2. **方法論の新しさ**: 情報フロー設計パターンを**独立変数として厳密に制御**し、同一タスクセット上で多水準比較を行うフレームワーク（OrgBench）は初。単一エージェントベースラインを含むことで、マルチエージェント構造自体の付加価値を問い直す。5反復による統計的再現性も確保。

3. **2段構えの知見**: 情報フロー設計がMASの出力に影響するか？という一次的問いへの実証的回答を提供。結果がyes/noいずれでも設計者にとって有用な知見となる。

4. **実践的示唆**: 「このタスク不確実性水準にはこの情報フロー設計が適する」という対応表を、客観的不確実性指標に基づいて提供。

---

## 9. Ethical Considerations

- LLM出力にバイアス（文化的、ジェンダー等）が含まれる可能性 → 評価軸に「バイアス検出」を追加検討
- 人間評価者への適切な報酬・同意取得
- 生成されたビジネス提案は研究目的であり、実際の投資判断に用いないことを明記
- LLM APIの利用規約への準拠
- 本研究の知見を人間組織に直接一般化するリスクを論文中で明示

---

## 10. Budget Summary

| 項目 | 金額 |
|------|------|
| LLM API（パイロット: 275回） | ~$19（¥2,900） |
| LLM API（本実行: 5,500回） | ~$385（¥58,000） |
| LLM-as-Judge評価（5,500×2） | ~$40（¥6,000） |
| 不確実性客観指標の取得（API等） | ~$10（¥1,500） |
| 人間バリデーション評価者（3名×$50相当） | ~$150（¥22,500） |
| arXiv投稿 | 無料 |
| 学会参加費（採択時） | ~$500-800 |
| **合計（投稿まで）** | **~¥91,000** |

---

## Appendix A: 情報フロー設計テンプレート一覧（抜粋）

### A.0 Single-Agent-Strong (Baseline)
```
Human → Single-Agent（最高性能モデル、全役割統合プロンプト）
（マルチエージェントの付加価値を問うためのベースライン）
```

### A.1 Deep Hierarchy (baseline = PJ_Anima Phase 1)
```
Shareholder → CEO → {CFO, CDO, TL} → {Researcher, Writer}
```

### A.2 Flat Organization
```
Shareholder → CEO → {CFO, CDO, Researcher, Writer, Analyst}
                     (全員がCEO直轄、中間管理なし)
```

### A.3 Matrix Organization
```
Shareholder → CEO
                ├── Function Heads: {CFO, CDO}
                └── Project Lead: TL
                    ├── Researcher (reports to both TL and CDO)
                    └── Writer (reports to both TL and CFO)
```

### A.4 Dual Review (Finance-Heavy)
```
Shareholder → CEO → TL → {Researcher, Writer}
                     ↑
              CFO → Accountant (2段財務レビュー)
              CDO (1段技術レビュー)
```

### A.5 Consensus Model
```
Shareholder → Board{CEO, CFO, CDO} (多数決) → TL → {Researcher, Writer}
```

### A.6 No-Review (Control)
```
Shareholder → CEO → TL → {Researcher, Writer}
              (CFO/CDOなし、レビューゲートなし)
```

---

## Appendix B: テーマセット（案）

| # | テーマ | ドメイン | 主観難易度 | 不確実性の客観指標（事前測定） |
|---|--------|---------|-----------|---------------------------|
| 1 | 高齢者向けAIフィットネスアプリ | Healthcare | Medium | Web検索ヒット数 / 論文数 / 企業数 |
| 2 | 中小企業向けAI経理自動化 | FinTech | Medium | 〃 |
| 3 | 農業IoTデータプラットフォーム | AgriTech | High | 〃 |
| 4 | Z世代向けメンタルヘルスSNS | HealthTech | Medium | 〃 |
| 5 | ローカル商店街のDX支援SaaS | RetailTech | Low | 〃 |
| 6 | 宇宙デブリ除去ビジネス | DeepTech | Very High | 〃 |
| 7 | ペット向けウェアラブルデバイス | IoT | Medium | 〃 |
| 8 | AI家庭教師サブスクリプション | EdTech | Low | 〃 |
| 9 | カーボンクレジット取引所 | CleanTech | High | 〃 |
| 10 | 地方自治体向け防災AI | GovTech | High | 〃 |
| 11-20 | (追加予定) | Mixed | Mixed | 〃 |

---

## Appendix C: IEEE Conference Paper Template Structure

```
1. Introduction (1.5 pages)
   1.1 LLM Agents as a Pure Experimental System for Information Flow
   1.2 Research Questions
2. Related Work (1 page)
   2.1 Multi-Agent LLM Systems
   2.2 Single-Agent Baselines
   2.3 Organizational Information Processing Theory
3. OrgBench Framework (2 pages)
   3.1 System Architecture
   3.2 Information Flow Design Templates
   3.3 Task Design and Uncertainty Operationalization
4. Experimental Setup (1 page)
   4.1 Independent Variables (55 configurations incl. single-agent)
   4.2 Evaluation: LLM-as-Judge + Human Validation
   4.3 Analysis Plan and Result Scenarios
5. Results (2 pages)
   5.1 RQ0: Single-Agent vs Multi-Agent
   5.2 RQ1: Topology Effects
   5.3 RQ2: Review Gate Effects
   5.4 RQ3: Model Heterogeneity
   5.5 RQ4: Uncertainty × Design Interaction
6. Discussion (1 page)
   6.1 Implications for MAS Design
   6.2 Information Flow as the Isolable Component of Organizational Structure
   6.3 Limitations and Scope
7. Conclusion (0.5 page)
References
```

**Page limit:** 8 pages (IEEE double-column) + references

---

*End of Research Plan v0.2*
