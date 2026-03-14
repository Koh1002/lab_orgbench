# 文献調査: LLMマルチエージェントシステムにおける組織トポロジーが集団意思決定品質に与える影響

**調査日**: 2026年3月9日
**対象期間**: 2023年〜2026年
**目的**: OrgBench研究提案のためのRelated Work基盤構築

---

## 目次
1. [Part 1: マルチエージェントLLMシステム (2023-2026)](#part-1)
2. [Part 2: エージェント間通信・協調プロトコル](#part-2)
3. [Part 3: マルチエージェントシステムのベンチマーク](#part-3)
4. [Part 4: 研究ギャップとOrgBenchの位置づけ](#part-4)

---

<a id="part-1"></a>
## Part 1: マルチエージェントLLMシステム (2023-2026)

### 1.1 基盤的フレームワーク (2023年)

#### AutoGen (Wu et al., 2023)
- **論文**: "AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation" [arXiv:2308.08155](https://arxiv.org/abs/2308.08155)
- **発表**: COLM 2024 (プレプリント 2023年8月)
- **開発元**: Microsoft Research
- **アーキテクチャ**: 会話駆動型マルチエージェントフレームワーク。`ConversableAgent`を基底クラスとし、`AssistantAgent`（LLM応答）、`UserProxyAgent`（ツール+人間）、`GroupChatManager`（グループチャット管理）の3種の組み込みエージェントを提供。
- **通信トポロジー**: **柔軟な会話パターン**。静的な事前定義フロー（二者間対話、グループチャット）と、動的な会話フロー（自然言語・コードによるプログラマブル遷移）の両方をサポート。GroupChatManagerによるスター型トポロジーがデフォルトだが、カスタム可能。
- **組織構造の変数化**: 明示的には行われていない。トポロジーはユーザーが手動で設計する。ただしv0.4以降は非同期イベント駆動アーキテクチャにより、より複雑な協調パターンを実現。
- **主要知見**: 数学、コーディング、質問応答、意思決定など広範なドメインで有効性を実証。被引用数851件以上（Semantic Scholar）と、マルチエージェントAI分野で最も影響力のあるフレームワークの一つ。
- **限界**: トポロジーの最適化は人手に依存。スケーラビリティ問題（v0.4で一部対応）。

#### MetaGPT (Hong et al., 2023)
- **論文**: "MetaGPT: Meta Programming for A Multi-Agent Collaborative Framework" [arXiv:2308.00352](https://arxiv.org/abs/2308.00352)
- **発表**: ICLR 2024
- **アーキテクチャ**: **組立ライン（Assembly Line）パラダイム**。ソフトウェア開発の人間ワークフロー（SOP: Standard Operating Procedures）をプロンプトシーケンスとしてエンコード。Product Manager → Architect → Engineer → QAのような役割分担。
- **通信トポロジー**: **階層的逐次型（パイプライン）**。各エージェントが前段の出力を受け取り、構造化された成果物を次段に渡す。SOPに基づく明確な指揮系統。
- **組織構造の変数化**: 行われていない。SOPは固定的に設計される。
- **主要知見**: 構造化されたSOPにより、ナイーブなLLMチェーニングで発生するカスケード幻覚（cascading hallucination）問題を軽減。ソフトウェア工学ベンチマークで既存のチャットベースシステムを上回る一貫性。
- **限界**: SOPの設計が人手に依存し、タスクドメインごとに再設計が必要。

#### ChatDev (Qian et al., 2023)
- **論文**: "ChatDev: Communicative Agents for Software Development" [arXiv:2307.07924](https://arxiv.org/abs/2307.07924)
- **発表**: ACL 2024 (Long Papers)
- **アーキテクチャ**: **チャットチェーン（Chat Chain）**方式。ソフトウェア開発を設計・コーディング・テストの各フェーズに分割し、各フェーズで専門エージェント間の対話を実行。
- **通信トポロジー**: **逐次フェーズ内ペアワイズ対話**。各フェーズ内ではCEO-CPO、CTO-Programmerなどの二者間対話を通じて意思決定。フェーズ間は逐次パイプライン。
- **組織構造の変数化**: 行われていない。会社組織（CEO, CTO, CPO, Programmer, Testerなど）は固定。
- **主要知見**: 「何を伝えるか」（チャットチェーン）と「どう伝えるか」（Communicative Dehallucination）の二軸で通信を制御することで幻覚を低減。自然言語はシステム設計に、プログラミング言語はデバッグに有利であることを示した。
- **限界**: 組織構造の比較分析は行われていない。

#### CAMEL (Li et al., 2023)
- **論文**: "CAMEL: Communicative Agents for 'Mind' Exploration of Large Language Model Society" [arXiv:2303.17760](https://arxiv.org/abs/2303.17760)
- **発表**: NeurIPS 2023
- **アーキテクチャ**: **ロールプレイングフレームワーク**。Inception Promptingを用いて、AIアシスタントとAIユーザーの二者がそれぞれ役割を演じながら協調的にタスクを解決。
- **通信トポロジー**: **ペアワイズ（二者間対話）**。指示者（AI User）と実行者（AI Assistant）の固定ペアによるマルチターン対話。
- **組織構造の変数化**: 行われていない。二者間のロールプレイに限定。
- **主要知見**: ロールプレイングが自律的マルチエージェント協調のスケーラブルな手法となり得ることを示した先駆的研究。LLMエージェント社会の「認知プロセス」を調査するためのデータ生成にも有用。
- **限界**: 二者間に限定され、3体以上の組織構造は未探索。

#### AgentVerse (Chen et al., 2023)
- **論文**: "AgentVerse: Facilitating Multi-Agent Collaboration and Exploring Emergent Behaviors" [arXiv:2308.10848](https://arxiv.org/abs/2308.10848)
- **発表**: ICLR 2024
- **アーキテクチャ**: **4段階動的フレームワーク**。①専門家募集（Expert Recruitment）→ ②協調的意思決定（Collaborative Decision-Making）→ ③行動実行（Action Execution）→ ④評価（Evaluation）。
- **通信トポロジー**: **動的スター型**。中央の調整者がエージェントグループを管理し、グループ討議を通じて意思決定。エージェント構成は動的に調整可能。
- **組織構造の変数化**: 部分的に実施。エージェントグループの構成を動的に変更する仕組みを持つが、トポロジー自体の体系的比較は行っていない。
- **主要知見**: テキスト理解、推論、コーディング、ツール利用、Embodied AIで有効性を確認。**協調行動の創発**（emergent collaborative behaviors）を観察し、集団効率向上に寄与することを示した。
- **限界**: スケーリング時のコンテキスト爆発問題。30体以上で性能低下（後続研究MacNetにより指摘）。暗黙的にスター型トポロジーに帰着する。

#### Generative Agents (Park et al., 2023)
- **論文**: "Generative Agents: Interactive Simulacra of Human Behavior" [arXiv:2304.03442](https://arxiv.org/abs/2304.03442)
- **発表**: UIST 2023 (ACM Symposium on User Interface Software and Technology)
- **開発元**: Stanford University
- **アーキテクチャ**: **メモリ中心型シミュレーション**。経験の記録（Memory Stream）→ 高次反省（Reflection）→ 動的検索（Retrieval）→ 行動計画（Planning）の認知アーキテクチャ。The Sims風のサンドボックス環境で25体のエージェントが生活。
- **通信トポロジー**: **非構造的・空間ベース**。エージェントは環境内で物理的に近接した他エージェントと自発的に会話を開始。明示的な組織構造は存在しない。
- **組織構造の変数化**: 行われていない。社会的相互作用は創発的。
- **主要知見**: LLMエージェントが信憑性のある人間的行動をシミュレートできることを実証。情報拡散、関係構築、協調行動の創発を観察。Science, Natureなど主要メディアでも報道された影響力の大きい研究。
- **限界**: タスク指向ではなくシミュレーション指向。組織構造の効果は未分析。

### 1.2 産業フレームワーク (2024-2026年)

#### CrewAI
- **公式サイト**: [crewai.com](https://crewai.com/)、[GitHub](https://github.com/crewAIInc/crewAI)
- **関連論文**: "Exploration of LLM Multi-Agent Application Implementation Based on LangGraph+CrewAI" [arXiv:2411.18241](https://arxiv.org/abs/2411.18241) (2024年11月)
- **アーキテクチャ**: **Crews and Flows**。Agent（役割・目標・ツールを持つ自律エージェント）、Task（具体的タスク）、Tool、Crewの4つのビルディングブロック。
- **通信トポロジー**: **階層型またはフラット型を選択可能**。階層モードではManagerエージェントがタスクを委任。フラット（分散）モードではエージェント間の直接協調。
- **組織構造の変数化**: 設定レベルでの選択（hierarchical / sequential / consensual）は可能だが、体系的な比較研究は行われていない。
- **主要知見**: ロールベースのエージェント設計、共有メモリ（短期・長期・エンティティ・文脈メモリ）、Agentic RAGの統合を実現。産業応用に最も広く採用されたフレームワークの一つ。

#### LangGraph / LangChain Agents
- **公式サイト**: [langchain.com/langgraph](https://www.langchain.com/langgraph)
- **アーキテクチャ**: **DAGベース（有向非巡回グラフ）オーケストレーション**。ノード＝エージェント/関数/判断点、エッジ＝データフロー。ステートマシンと有向グラフによるマルチエージェント制御。
- **通信トポロジー**: **明示的グラフ定義**。開発者がエージェント間の遷移確率・条件を明示的にグラフとして定義。AutoGenの「会話」フレーミングに対し、LangGraphは「グラフ」フレーミングを採用。
- **組織構造の変数化**: フレームワークレベルではグラフ構造を自由に定義可能だが、異なるトポロジーの体系的比較は提供されていない。
- **主要知見**: 共有永続状態（persistent state）によるワークフロー横断のコンテキスト維持。実行時条件に基づく動的調整。GitHub星120k超。

#### OpenAI Swarm → Agents SDK (2024-2025)
- **Swarm**: [GitHub](https://github.com/openai/swarm) (2024年、教育用実験フレームワーク)
- **Agents SDK**: [公式ドキュメント](https://openai.github.io/openai-agents-python/) (2025年3月リリース、本番運用向け)
- **アーキテクチャ**: **ステートレス・ハンドオフベース**。Chat Completions APIを基盤とし、エージェント間の制御移譲（handoff）を明示的な関数で実現。常に1体のエージェントのみが制御を保持。
- **通信トポロジー**: **チェーン型（逐次ハンドオフ）**。明示的なハンドオフ関数による制御移譲。各ハンドオフ時に必要なコンテキストを明示的に渡す。
- **組織構造の変数化**: 行われていない。ハンドオフパターンは開発者が設計。
- **主要知見**: Guardrails（入力/出力/ツール検証）のパラレル実行、ブロッキングモードによるコスト最適化。軽量・透明性・可観測性を重視した設計哲学。

#### Google Agent2Agent (A2A) Protocol (2025)
- **公式サイト**: [a2a-protocol.org](https://a2a-protocol.org/latest/)
- **発表**: 2025年4月、Linux Foundationに寄贈
- **アーキテクチャ**: **オープン通信プロトコル**。異なるフレームワーク（ADK, LangGraph, CrewAIなど）・ベンダー間のエージェント相互運用性を実現する標準規格。エージェント発見、協調、タスク委任のための共通言語。
- **通信トポロジー**: プロトコルレベルではトポロジー非依存。任意の構造を上位レイヤーで実装可能。
- **主要知見**: 150以上の組織が参加するエコシステム。v0.3でgRPCサポート追加。MCP（Model Context Protocol）と補完的に動作。

#### Anthropic MCP (Model Context Protocol) (2024-2025)
- **概要**: AIエージェントと外部システム（ツール・データ）を接続するためのオープン標準。2024年11月発表以降、数千のMCPサーバーが構築され、事実上のツール接続標準に。
- **マルチエージェントとの関連**: A2AプロトコルとMCPの組み合わせにより、ツール統合・コンテキスト共有・タスク委任を含むマルチエージェントシステムの構築を支援。Agent Skills（SKILL.mdによる再利用可能ワークフロー定義）も導入。

### 1.3 先端研究 (2024-2025年)

#### MacNet: Scaling Large Language Model-Based Multi-Agent Collaboration (Qian et al., 2024)
- **論文**: "Scaling Large Language Model-Based Multi-Agent Collaboration" [arXiv:2406.07155](https://arxiv.org/abs/2406.07155)
- **発表**: ICLR 2025
- **アーキテクチャ**: **有向非巡回グラフ（DAG）ベースのマルチエージェント協調ネットワーク**。各エッジに監督的批評者（Critic）、各ノードに従順な実行者（Actor）を配置し、役割の機能的二分割を実現。
- **通信トポロジー**: **DAGベース階層型**。情報の逆流を構造的に防止。不規則トポロジーが規則的トポロジーを上回ることを実証。
- **組織構造の変数化**: **本研究の核心**。1000体以上のエージェントスケーリングを実現し、トポロジーとスケールの関係を体系的に分析。
- **主要知見**:
  - 全体性能はエージェント数に対してロジスティック成長パターンに従う
  - 協調的創発（collaborative emergence）はニューラル創発より早期に発現
  - AgentVerseは暗黙的にスター型に帰着し、30体超でコンテキスト爆発
  - 多数決投票はCoT/Auto-GPT増強でも0.9%向上に留まり、8体で飽和

#### DyLAN: Dynamic LLM-Powered Agent Network (Liu et al., 2023/2024)
- **論文**: "A Dynamic LLM-Powered Agent Network for Task-Oriented Agent Collaboration" [arXiv:2310.02170](https://arxiv.org/abs/2310.02170)
- **アーキテクチャ**: **時間的フィードフォワードネットワーク（T-FFN）**。ノード＝エージェント、エッジ＝通信チャネル。2段階パラダイム：①チーム最適化（Agent Importance Scoreによる教師なし選定）、②タスク解決（動的協調）。
- **通信トポロジー**: **動的・タスク適応型**。エージェントの重要度に基づいてチーム構成を最適化。
- **組織構造の変数化**: 暗黙的に実施。エージェント選定により実効的なトポロジーが変化。
- **主要知見**: 最適化された3体チームが、7体の同一アーキテクチャや4体のLLM Debateを上回り、効率を52.9%〜67.8%改善。

#### G-Designer (Yao et al., 2024)
- **論文**: "G-Designer: Architecting Multi-agent Communication Topologies via Graph Neural Networks" [arXiv:2410.11782](https://arxiv.org/abs/2410.11782)
- **発表**: ICML 2025 Poster
- **アーキテクチャ**: **変分グラフオートエンコーダ（VAE）ベースのトポロジー設計**。エージェントノードとタスク固有仮想ノードをエンコードし、タスク適応的な通信トポロジーをデコード。
- **通信トポロジー**: **学習可能・タスク適応型**。GNNにより動的に最適トポロジーを生成。
- **組織構造の変数化**: **本研究の核心**。トポロジーを明示的に学習対象とする。
- **主要知見**: MMLU 84.50%、HumanEval pass@1 89.90%。トークン消費を最大95.33%削減。敵対攻撃に対してわずか0.3%の精度低下で耐性。

#### "Topological Structure Learning Should Be A Research Priority for LLM-Based MAS" (2025)
- **論文**: [arXiv:2505.22467](https://arxiv.org/abs/2505.22467)
- **概要**: LLMベースMASのトポロジー（エージェント構成、接続、協調方法）が未踏領域であると主張するポジションペーパー。トポロジー認識型MASへのパラダイムシフトを提唱。
- **提案フレームワーク**: ①エージェント選定、②構造プロファイリング、③トポロジー合成の3段階アプローチ。適応性・効率性・頑健性・公平性の4軸で評価。

#### "Understanding the Information Propagation Effects of Communication Topologies" (2025)
- **論文**: [arXiv:2505.23352](https://arxiv.org/html/2505.23352v1)
- **概要**: チェーン、スター、完全結合グラフなどの固定トポロジーにおける情報伝播効果を分析。学習可能な通信グラフの最新動向を整理。

#### Guided Topology Diffusion (GTD) (2025)
- **論文**: [arXiv:2510.07799](https://arxiv.org/html/2510.07799)
- **概要**: 条件付き離散グラフ拡散モデルによる通信ネットワークの動的生成。タスク適応的、スパース、効率的なトポロジーを反復構築。

---

<a id="part-2"></a>
## Part 2: エージェント間通信・協調プロトコル

### 2.1 討論・議論プロトコル

#### Multiagent Debate (Du et al., 2023)
- **論文**: "Improving Factuality and Reasoning in Language Models through Multiagent Debate" [arXiv:2305.14325](https://arxiv.org/abs/2305.14325)
- **発表**: ICML 2024
- **手法**: 複数のLLMインスタンスが各自の回答と推論過程を提案し、複数ラウンドにわたって討論し、共通の最終回答に到達。
- **主要知見**: 数学的・戦略的推論を大幅に向上。事実性を改善し、幻覚を低減。既存のブラックボックスモデルに直接適用可能。すべてのタスクで同一のプロンプトと手順を使用。
- **限界**: 計算コストが高い。後続研究により、予算制約下ではCoT+Self-Consistencyの方が効率的であることが判明。

#### "Rethinking the Bounds of LLM Reasoning: Are Multi-Agent Discussions the Key?" (Wang et al., 2024)
- **論文**: [arXiv:2402.18272](https://arxiv.org/abs/2402.18272)
- **発表**: ACL 2024
- **主要知見（重要）**: **強力なプロンプトを用いた単一エージェントLLMが、最良の既存討論アプローチとほぼ同等の性能を達成可能**。マルチエージェント討論が単一エージェントを上回るのは、プロンプトにデモンストレーションがない場合に限定される。
- **意義**: マルチエージェント討論の有効性に対する重要な反証。組織構造の効果を分離して評価する必要性を示唆。

#### "Can LLM Agents Really Debate?" (2025)
- **論文**: [arXiv:2511.07784](https://arxiv.org/pdf/2511.07784)
- **概要**: マルチエージェント討論の制御実験。討論メカニズムの実効性を厳密に検証。

### 2.2 投票・合意形成メカニズム

#### "Voting or Consensus? Decision-Making in Multi-Agent Debate" (Kaesberg et al., 2025)
- **論文**: [arXiv:2502.19130](https://arxiv.org/html/2502.19130v4)
- **発表**: ACL 2025 Findings
- **概要**: Exchange-of-Thoughtなどの合意ベースアプローチと投票ベースアプローチの体系的比較。先行研究は単一クラスの意思決定プロトコルに焦点を当てており、パラメータ変動による体系的比較が不足していると指摘。

#### "Debate or Vote: Which Yields Better Decisions?" (2025)
- **論文**: [arXiv:2508.17536](https://arxiv.org/pdf/2508.17536)
- **主要知見**: マルチエージェント討論が協調的議論により性能を向上させる有望なメカニズムとされてきたが、**単純多数決投票が観測される改善の大部分を説明する**という実証的証拠を提示。

#### "FREE-MAD: Consensus-Free Multi-Agent Debate" (2025)
- **論文**: [arXiv:2509.11035](https://arxiv.org/pdf/2509.11035)
- **概要**: 合意形成は理論的に保証されず、実用上も一般に達成困難であるとし、合意不要のマルチエージェント討論を提案。

#### Budget-Aware Evaluation of LLM Reasoning Strategies (2024)
- **発表**: EMNLP 2024
- **主要知見**: 予算認識型の評価において、**CoT+Self-Consistencyがマルチエージェント討論に対して極めて競争力が高い**。Self-ConsistencyがCoTにより、はるかに少ない予算で他の推論戦略を一貫して上回る。

### 2.3 ロールプレイングとペルソナ割当の効果

#### "Two Tales of Persona in LLMs: A Survey of Role-Playing and Personalization" (2024)
- **発表**: EMNLP 2024 Findings ([aclanthology.org](https://aclanthology.org/2024.findings-emnlp.969/))
- **概要**: ペルソナの統一的視点からロールプレイングとパーソナライゼーションを初めて包括的にサーベイ。

#### "From Biased Chatbots to Biased Agents: Examining Role Assignment Effects" (2025)
- **論文**: [arXiv:2602.12285](https://arxiv.org/html/2602.12285)
- **主要知見**: 人口統計学的ペルソナ割当がLLMエージェントの頑健性を意図せず低下させうることを示し、タスク無関連のペルソナ手がかりが暗黙的バイアスを誘発。

#### PersonaGym (2024)
- **論文**: [arXiv:2407.18416](https://arxiv.org/html/2407.18416v2)
- **概要**: ペルソナエージェントとLLMを評価するためのベンチマーク。

#### "From Single to Societal: Analyzing Persona-Induced Bias in Multi-Agent Interactions" (2025)
- **論文**: [arXiv:2511.11789](https://arxiv.org/html/2511.11789v1)
- **概要**: 異なるペルソナ割当が個々のLLMの問題解決性能に顕著に影響を与えることを実証。マルチエージェント環境における影響を拡張分析。

### 2.4 Chain-of-Thought vs. マルチエージェント推論

上述の通り、2024年以降の研究は以下の重要な知見を蓄積している：

1. **マルチエージェント討論の有効性は限定的**: 強力なプロンプトによる単一エージェントとほぼ同等（Wang et al., ACL 2024）
2. **予算制約下ではCoT+Self-Consistencyが優位**: はるかに少ないトークンで同等以上の性能（EMNLP 2024）
3. **単純多数決投票が討論の改善の大部分を説明**: 討論プロセス自体の付加価値は限定的（2025年の複数研究）
4. **既存のMAD設計は追加推論時計算を十分活用できていない**: エージェント構成や討論ラウンドの分析から示唆

→ **これらは「組織構造自体の効果」を分離して評価する必要性を強く示唆しており、OrgBenchの動機付けとなる。**

### 2.5 社会心理学的視点からの協調メカニズム

#### "Exploring Collaboration Mechanisms for LLM Agents: A Social Psychology View" (Zhang et al., 2024)
- **論文**: [arXiv:2310.02124](https://arxiv.org/abs/2310.02124)
- **発表**: ACL 2024
- **手法**: 4つの「社会」を構築。各エージェントは特性（easy-going / overconfident）を持ち、協調パターン（debate / reflection）で活動。
- **主要知見**:
  - 特定の協調戦略が既存トップ手法を上回りつつ効率を最適化
  - LLMエージェントが**人間的な社会行動（同調、合意形成）**を示す
  - 社会心理学の基礎理論（同調行動理論など）を反映
- **意義**: 組織構造（社会的特性＋協調パターンの組み合わせ）が性能に影響することを社会心理学の観点から実証。OrgBenchの理論的基盤として重要。

---

<a id="part-3"></a>
## Part 3: マルチエージェントシステムのベンチマーク

### 3.1 既存ベンチマーク

#### AgentBench (Liu et al., 2023)
- **論文**: "AgentBench: Evaluating LLMs as Agents" [arXiv:2308.03688](https://arxiv.org/abs/2308.03688)
- **発表**: ICLR 2024
- **概要**: 8つの環境でLLM-as-Agentの推論・意思決定能力を評価する最初のベンチマーク。29以上のAPI/OSSモデルをテスト。
- **評価対象**: 単一エージェントの能力。マルチエージェント間の協調・組織構造は評価対象外。
- **主要知見**: 商用LLMとOSSモデルの間に大きな性能格差。長期推論・意思決定・指示追従が主要課題。

#### ChatArena (Farama Foundation)
- **GitHub**: [Farama-Foundation/chatarena](https://github.com/Farama-Foundation/chatarena)
- **概要**: マルチエージェント言語ゲーム環境。LLMの通信・協調・競争能力のベンチマーキングおよび訓練を支援。
- **限界**: 環境は提供されるが、組織トポロジーを変数とした体系的評価は行われていない。

#### MultiAgentBench (MARBLE) (2025)
- **論文**: "MultiAgentBench: Evaluating the Collaboration and Competition of LLM agents" [arXiv:2503.01935](https://arxiv.org/abs/2503.01935)
- **発表**: ACL 2025 Main Conference
- **概要**: タスク達成だけでなく、協調・競争の品質をマイルストーンベースKPIで評価。**スター、チェーン、ツリー、グラフの各通信トポロジー**とグループ討議・認知的計画戦略を評価。
- **組織構造の変数化**: **部分的に実施**。協調プロトコル（通信トポロジー）を変数として比較。
- **主要知見**:
  - gpt-4o-miniが平均最高タスクスコアを達成
  - **グラフ構造が協調プロトコルの中で最良**の性能を示す（研究シナリオ）
  - 認知的計画がマイルストーン達成率を3%向上
- **OrgBenchとの関係**: MultiAgentBenchは通信トポロジーを変数として含むが、「組織構造」（階層・フラット・マトリクスなど）の体系的比較は行っていない。また、意思決定品質への影響を独立して評価する仕組みは限定的。

### 3.2 マルチエージェント出力の評価方法

既存研究における評価アプローチは以下に大別される：

| 評価手法 | 使用例 | 限界 |
|---------|--------|------|
| タスク正解率 | AgentBench, MultiAgentBench | 協調プロセスを評価しない |
| pass@k (コード生成) | MetaGPT, HumanEval | ソフトウェア開発に限定 |
| マイルストーンKPI | MultiAgentBench | タスク固有の設計が必要 |
| 人間評価 | Generative Agents | スケーラビリティに欠ける |
| LLM-as-Judge | 多数の研究 | 評価者バイアスの問題 |
| トークン消費量 | G-Designer, DyLAN | 品質との兼ね合いが不明確 |

### 3.3 組織構造を変数とするベンチマーク

**現時点で、組織トポロジー（階層型、フラット型、マトリクス型など）を独立変数として体系的に比較するベンチマークは存在しない。** 最も近い研究は以下の通り：

| 研究 | 変数化の範囲 | 限界 |
|------|-------------|------|
| MacNet (ICLR 2025) | DAGトポロジーのスケーリング | 組織構造の「型」ではなくグラフ構造 |
| MultiAgentBench (ACL 2025) | スター/チェーン/ツリー/グラフ | 通信プロトコルレベル。組織論的構造の比較ではない |
| G-Designer (ICML 2025) | 学習可能トポロジー | 特定タスクへの最適化。人間の組織形態との対応なし |
| Zhang et al. (ACL 2024) | 特性×協調パターン | 2×2の限定的組み合わせ |

---

<a id="part-4"></a>
## Part 4: 研究ギャップとOrgBenchの位置づけ

### 4.1 特定された研究ギャップ

以上の文献調査から、以下の明確な研究ギャップが特定される：

#### ギャップ1: 組織構造の体系的比較の不在
既存のフレームワーク（AutoGen, MetaGPT, ChatDev, CrewAIなど）はそれぞれ固有の組織構造を採用しているが、**同一タスク・同一LLMで異なる組織構造を制御実験的に比較した研究は存在しない**。MacNetやG-Designerはグラフトポロジーを変数化しているが、人間の組織論で定義される階層型・フラット型・マトリクス型・ホラクラシー型などの構造との対応付けは行われていない。

#### ギャップ2: 意思決定品質の独立評価指標の欠如
既存ベンチマークはタスク達成率を主要指標としているが、**集団意思決定の品質**（合意形成の速度、情報統合の完全性、少数意見の反映度、意思決定の頑健性など）を独立して評価する指標とベンチマークが存在しない。

#### ギャップ3: 通信トポロジーと組織構造の混同
MultiAgentBenchは通信トポロジー（スター、チェーン等）を変数化しているが、**通信トポロジー（物理的接続）と組織構造（権限・責任・意思決定権限の配分）は異なる概念**であり、両者を分離して評価する研究は存在しない。例えば、スター型通信でも民主的意思決定を行う場合と、スター型通信で中央集権的意思決定を行う場合では結果が異なるはずだが、この区別は未探索。

#### ギャップ4: スケーリング法則の組織構造依存性
MacNet (ICLR 2025) はエージェント数に対するロジスティック成長パターンを発見したが、この法則が**組織構造の型によってどう変化するか**は未解明。階層型ではより多くのエージェントに有利か、フラット型では少数精鋭が最適か、といった問いは未回答。

#### ギャップ5: ロールプレイとトポロジーの交互作用
ペルソナ割当の効果（EMNLP 2024, ACL 2024）と通信トポロジーの効果は個別に研究されているが、**特定のロール配置が特定のトポロジーでのみ有効になる交互作用効果**は未調査。

#### ギャップ6: 動的組織変化（Adaptive Organization）の欠如
現実の組織は状況に応じて構造を変化させる（危機時の集権化、創造的タスクでのフラット化など）が、**タスクの性質や進行状況に応じて組織構造を動的に変化させるメカニズム**の研究は限定的（G-Designerは静的なタスク適応のみ）。

### 4.2 OrgBenchが埋めるギャップ

提案するOrgBenchは以下の点でこれらのギャップを包括的に埋めることを目指す：

1. **組織論に基づく構造定義**: 経営学・組織論で定義される組織形態（階層型、フラット型、マトリクス型、ネットワーク型、ホラクラシー型等）をLLMマルチエージェントシステムに形式的にマッピング
2. **制御実験フレームワーク**: 同一タスク・同一LLM・同一エージェント数で組織構造のみを変数とする実験設計
3. **集団意思決定品質指標**: タスク達成率に加え、合意形成過程・情報統合度・意思決定頑健性などの多面的評価指標
4. **通信トポロジーと権限構造の分離**: 物理的通信構造と論理的権限構造を独立変数として設計
5. **スケーリング実験**: 組織構造×エージェント数のスケーリング法則の解明
6. **タスクタイプ×組織構造の適合性マッピング**: どのタスクにどの組織構造が最適かの実証的知見

---

## 参考文献一覧

### マルチエージェントフレームワーク
- Wu, Q., et al. (2023). "AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation." COLM 2024. [arXiv:2308.08155](https://arxiv.org/abs/2308.08155)
- Hong, S., et al. (2023). "MetaGPT: Meta Programming for A Multi-Agent Collaborative Framework." ICLR 2024. [arXiv:2308.00352](https://arxiv.org/abs/2308.00352)
- Qian, C., et al. (2023). "ChatDev: Communicative Agents for Software Development." ACL 2024. [arXiv:2307.07924](https://arxiv.org/abs/2307.07924)
- Li, G., et al. (2023). "CAMEL: Communicative Agents for 'Mind' Exploration of Large Language Model Society." NeurIPS 2023. [arXiv:2303.17760](https://arxiv.org/abs/2303.17760)
- Chen, W., et al. (2023). "AgentVerse: Facilitating Multi-Agent Collaboration and Exploring Emergent Behaviors." ICLR 2024. [arXiv:2308.10848](https://arxiv.org/abs/2308.10848)
- Park, J.S., et al. (2023). "Generative Agents: Interactive Simulacra of Human Behavior." UIST 2023. [arXiv:2304.03442](https://arxiv.org/abs/2304.03442)

### スケーリング・トポロジー研究
- Qian, C., et al. (2024). "Scaling Large Language Model-Based Multi-Agent Collaboration." ICLR 2025. [arXiv:2406.07155](https://arxiv.org/abs/2406.07155)
- Liu, Z., et al. (2023). "DyLAN: A Dynamic LLM-Powered Agent Network for Task-Oriented Agent Collaboration." [arXiv:2310.02170](https://arxiv.org/abs/2310.02170)
- Yao, Y., et al. (2024). "G-Designer: Architecting Multi-agent Communication Topologies via Graph Neural Networks." ICML 2025. [arXiv:2410.11782](https://arxiv.org/abs/2410.11782)
- (2025). "Topological Structure Learning Should Be A Research Priority for LLM-Based MAS." [arXiv:2505.22467](https://arxiv.org/abs/2505.22467)
- (2025). "Understanding the Information Propagation Effects of Communication Topologies in LLM-based MAS." [arXiv:2505.23352](https://arxiv.org/html/2505.23352v1)
- (2025). "Dynamic Generation of Multi LLM Agents Communication Topologies with Graph Diffusion Models." [arXiv:2510.07799](https://arxiv.org/html/2510.07799)

### 通信・協調プロトコル
- Du, Y., et al. (2023). "Improving Factuality and Reasoning in Language Models through Multiagent Debate." ICML 2024. [arXiv:2305.14325](https://arxiv.org/abs/2305.14325)
- Wang, Q., et al. (2024). "Rethinking the Bounds of LLM Reasoning: Are Multi-Agent Discussions the Key?" ACL 2024. [arXiv:2402.18272](https://arxiv.org/abs/2402.18272)
- Kaesberg, J., et al. (2025). "Voting or Consensus? Decision-Making in Multi-Agent Debate." ACL 2025 Findings. [arXiv:2502.19130](https://arxiv.org/html/2502.19130v4)
- Zhang, J., et al. (2024). "Exploring Collaboration Mechanisms for LLM Agents: A Social Psychology View." ACL 2024. [arXiv:2310.02124](https://arxiv.org/abs/2310.02124)

### ベンチマーク
- Liu, X., et al. (2023). "AgentBench: Evaluating LLMs as Agents." ICLR 2024. [arXiv:2308.03688](https://arxiv.org/abs/2308.03688)
- (2025). "MultiAgentBench: Evaluating the Collaboration and Competition of LLM agents." ACL 2025. [arXiv:2503.01935](https://arxiv.org/abs/2503.01935)

### ペルソナ・ロールプレイ
- (2024). "Two Tales of Persona in LLMs: A Survey of Role-Playing and Personalization." EMNLP 2024 Findings. [ACL Anthology](https://aclanthology.org/2024.findings-emnlp.969/)
- (2025). "From Biased Chatbots to Biased Agents: Examining Role Assignment Effects on LLM Agent Robustness." [arXiv:2602.12285](https://arxiv.org/html/2602.12285)

### 産業フレームワーク・プロトコル
- CrewAI. [crewai.com](https://crewai.com/) / [GitHub](https://github.com/crewAIInc/crewAI)
- LangGraph. [langchain.com/langgraph](https://www.langchain.com/langgraph)
- OpenAI Swarm. [GitHub](https://github.com/openai/swarm)
- OpenAI Agents SDK. [公式ドキュメント](https://openai.github.io/openai-agents-python/)
- Google Agent2Agent Protocol. [a2a-protocol.org](https://a2a-protocol.org/latest/)
- Anthropic Model Context Protocol (MCP). [anthropic.com](https://www.anthropic.com/engineering/advanced-tool-use)

### サーベイ論文
- (2024). "Multi-Agent Collaboration Mechanisms: A Survey of LLMs." [arXiv:2501.06322](https://arxiv.org/html/2501.06322v1)
- (2024). "LLM-based Multi-Agent Systems: Techniques and Business Perspectives." [arXiv:2411.14033](https://arxiv.org/html/2411.14033v2)
- (2025). "A Taxonomy of Hierarchical Multi-Agent Systems." [arXiv:2508.12683](https://arxiv.org/pdf/2508.12683)
