# Does Information Flow Design Matter? Isolating the Effect of Communication and Authority Patterns on Multi-Agent Collective Decision Quality

**Draft v0.1 — Sections 1–4 (Introduction through Methodology)**
**Target:** AAMAS 2027 / IEEE ICA 2027
**Format:** IEEE double-column, 8 pages + references

---

## 1. Introduction

### 1.1 The Unasked Question

Large language model (LLM) based multi-agent systems have proliferated rapidly since 2023. Frameworks such as AutoGen [1], MetaGPT [2], ChatDev [3], and CrewAI adopt organizational metaphors—assigning agents roles like "CEO," "Engineer," or "Reviewer"—and connecting them through communication channels with implicit authority relationships. Yet a fundamental question remains unaddressed: **does the design of information flow among agents—who sends messages to whom, who holds decision authority, who reviews whose output—actually affect the quality of the collective output?**

This question has a long history in human organizational theory. Galbraith's information processing theory [4] posits that organizational effectiveness depends on the fit between information processing requirements (determined by task uncertainty) and information processing capacity (determined by organizational design). Mintzberg [5] classified organizations into five structural configurations, each suited to different environmental conditions. Lawrence and Lorsch [6] demonstrated that high-performing organizations match their internal differentiation and integration mechanisms to environmental uncertainty. Burns and Stalker [7] distinguished mechanistic from organic organizational forms, arguing that the latter outperform under conditions of rapid change.

Despite decades of research, these theories have never been tested under controlled experimental conditions. Human organizations are confounded by culture, motivation, trust, political behavior, tacit knowledge, and learning curves—factors that are inextricable from organizational structure in practice. Randomized controlled experiments on organizational design are ethically and practically infeasible with human participants.

LLM-powered multi-agent systems present a novel opportunity. They lack the confounding factors inherent to human organizations: LLM agents have no intrinsic motivation, no political interests, no cultural biases beyond those embedded in training data, and no tacit knowledge that resists formalization. What remains when these confounds are removed is the **pure effect of information flow design**—message routing patterns, authority allocation, and review protocols. LLM agents thus constitute a **controlled experimental system for isolating the information-flow component of organizational structure**, a component that organizational theory has theorized about but never measured in isolation.

### 1.2 The Single-Agent Challenge

Before investigating how different multi-agent designs compare, we must confront a more basic question: **does multi-agent structure itself add value over a well-prompted single agent?**

Recent evidence suggests this is far from obvious. Wang et al. [8] demonstrated that a single LLM with a carefully crafted prompt achieves performance comparable to the best multi-agent debate configurations. Budget-aware evaluations at EMNLP 2024 [9] showed that Chain-of-Thought with self-consistency is more cost-effective than multi-agent debate under fixed token budgets. Multiple 2025 studies [10, 11] found that simple majority voting explains most of the performance gains attributed to multi-agent discussion processes.

These findings raise a critical concern: if the organizational structure—the information flow design—of a multi-agent system does not measurably improve output quality beyond what a single agent achieves, then the substantial engineering effort devoted to multi-agent frameworks (and the research effort devoted to optimizing them) may be misallocated. Our study directly addresses this concern by including a strong single-agent baseline and treating the question of multi-agent added value as the zeroth research question (RQ0).

### 1.3 Present Work

We present **OrgBench**, a benchmark framework for systematically comparing information flow design patterns in LLM multi-agent systems. OrgBench operationalizes the three layers of information flow design—communication topology, authority structure, and review protocol—as independent variables, and evaluates their effects on collective decision quality through a controlled experiment.

Our experimental design comprises 55 configurations (54 multi-agent configurations spanning four design dimensions, plus one optimized single-agent baseline) evaluated across 20 standardized business proposal tasks with 5 replications per condition, yielding 5,500 experimental runs. Task uncertainty is operationalized through both objective indicators (web search hit counts, academic publication counts, and market maturity metrics) and subjective expert ratings, enabling a test of the contingency hypothesis—that optimal information flow design depends on task characteristics.

We assess output quality primarily through LLM-as-Judge evaluation (with bias mitigation through evaluator-generator separation, multi-evaluator consensus, and blinding), validated against human assessment on a representative subset. Our analysis plan accommodates four possible outcome scenarios, ensuring that the study produces actionable knowledge regardless of whether multi-agent designs prove superior, inferior, or equivalent to single-agent approaches.

### 1.4 Contributions

Our contributions are as follows:

1. **A new perspective on LLM agents as experimental systems.** We frame LLM multi-agent systems not as imitations of human organizations, but as controlled experimental systems that isolate the information-flow component of organizational structure—a component that has been theorized about for six decades but never measured in isolation due to confounding factors in human organizations.

2. **OrgBench: a benchmark for information flow design.** We introduce the first benchmark that treats information flow design patterns (communication topology × authority structure × review protocol) as independent variables, including a strong single-agent baseline for calibrating the added value of multi-agent structure itself.

3. **A systematic empirical comparison.** We report results from 55 configurations × 20 tasks × 5 replications = 5,500 runs, with LLM-as-Judge evaluation validated by human assessment—the largest controlled comparison of multi-agent information flow designs to date.

4. **Practical design guidelines.** We provide an evidence-based mapping from task uncertainty levels to recommended information flow designs, grounded in objective uncertainty metrics.

### 1.5 Scope and Limitations

We are explicit about what this study is and is not. We study **information flow design patterns**—the routing of messages, the allocation of decision authority, and the configuration of review processes among LLM agents. We do not claim to study "organizational structure" in the full sense that organizational theorists use the term, which encompasses culture, trust, motivation, political behavior, tacit knowledge, and other factors absent from LLM agent systems.

This limitation is simultaneously our methodological advantage. Because LLM agents lack these confounds, they allow us to measure the pure effect of information flow design for the first time. Our findings apply directly to the design of LLM multi-agent systems. Their applicability to human organizations is limited to the information-flow component and should not be generalized beyond that scope.

---

## 2. Related Work

### 2.1 Multi-Agent LLM Frameworks

The first generation of LLM multi-agent frameworks (2023) introduced organizational metaphors to multi-agent design but treated organizational structure as a fixed architectural choice rather than a variable to be optimized. AutoGen [1] provides flexible conversation patterns but does not systematically compare topologies. MetaGPT [2] implements a sequential pipeline inspired by software development Standard Operating Procedures, with roles such as Product Manager, Architect, and Engineer arranged in a fixed hierarchy. ChatDev [3] adopts a similar approach with a waterfall-style "chat chain" where pairs of agents (e.g., CEO–CTO, CTO–Programmer) engage in sequential dialogue. CAMEL [12] explores two-agent role-playing, and AgentVerse [13] facilitates group discussion among dynamically recruited expert agents, but both operate under flat, non-hierarchical structures. Generative Agents [14] simulate believable human behavior in a sandbox environment but do not address task-oriented organizational design.

A second generation of research (2024–2025) began to examine communication topology as a variable. MacNet [15] (ICLR 2025) introduced DAG-based multi-agent collaboration networks, demonstrating that irregular topologies outperform regular ones and that collective performance follows a logistic growth pattern with respect to agent count. Critically, MacNet showed that AgentVerse implicitly reduces to a star topology and saturates at approximately 30 agents due to context explosion. G-Designer [16] (ICML 2025) uses a variational graph autoencoder to generate task-adaptive communication topologies, achieving up to 95% reduction in token consumption. A 2025 position paper [17] argued that topological structure learning should be a research priority for LLM-based multi-agent systems.

However, all of these studies treat "topology" as synonymous with "communication graph"—who can send messages to whom. They do not distinguish communication topology from authority structure (who holds decision-making power) or review protocol (who evaluates whose output). As we argue in Section 2.4, these are distinct design dimensions that can be independently varied and whose effects may differ.

Industrial frameworks reflect a similar gap. CrewAI offers hierarchical and sequential modes but provides no systematic comparison. LangGraph enables arbitrary graph definitions but leaves topology selection to the developer. OpenAI's Agents SDK implements a stateless handoff pattern without optimizing the handoff structure.

### 2.2 The Single-Agent Counterargument

A line of research challenges the fundamental premise that multi-agent systems outperform single agents. Wang et al. [8] (ACL 2024) provided the most direct challenge, demonstrating that a single LLM with strong prompting (including demonstrations) achieves performance comparable to the best multi-agent debate configurations. Their finding implies that the apparent benefits of multi-agent discussion may be attributable to the prompt engineering embedded in the agent roles rather than to the inter-agent interaction itself.

Supporting evidence comes from multiple directions. Budget-aware evaluation at EMNLP 2024 [9] showed that CoT + self-consistency consistently outperforms multi-agent debate under equivalent token budgets. Kaesberg et al. [10] (ACL 2025 Findings) found that systematic comparison of debate and voting protocols reveals limited added value from the debate process. A 2025 study [11] provided empirical evidence that simple majority voting explains the bulk of improvements attributed to multi-agent discussion.

These findings do not invalidate multi-agent systems—they may apply primarily to reasoning tasks (math, logic) rather than to open-ended creative tasks like business proposal generation. However, they mandate that any serious study of multi-agent information flow design must include a strong single-agent baseline. Our study addresses this directly through RQ0 and the Single-Agent-Strong configuration.

### 2.3 Organizational Information Processing Theory

Our theoretical framework draws primarily on Galbraith's information processing theory [4], which provides the most natural bridge between organizational theory and LLM multi-agent design. Galbraith's central proposition—that organizational effectiveness depends on the fit between information processing requirements and capacity—translates directly to the multi-agent setting, where "information processing" is literally what agents do, measurable in tokens and API calls.

Galbraith identified four strategies for managing the information processing gap: creating slack resources, creating self-contained task units, investing in vertical information systems, and creating lateral relations. In the LLM agent context, these correspond to: allowing generous context windows and retry budgets (slack); expanding each agent's autonomous scope (self-contained units); implementing shared memory or structured message passing (vertical information systems); and enabling direct peer-to-peer communication channels (lateral relations).

Burns and Stalker's [7] distinction between mechanistic and organic organizations provides our design taxonomy. Mechanistic organizations (fixed pipelines, strict hierarchy, vertical communication) correspond to deep hierarchy configurations with hub-and-spoke communication. Organic organizations (flexible roles, lateral communication, distributed authority) correspond to flat or matrix configurations with mesh communication.

Lawrence and Lorsch's [6] contingency theory motivates our central hypothesis (H5): that the optimal information flow design depends on task uncertainty. Their empirical finding—that high-performing organizations in uncertain environments exhibit greater differentiation and more sophisticated integration mechanisms—suggests that complex, mesh-like communication patterns should outperform simple pipelines for high-uncertainty tasks, while the reverse should hold for low-uncertainty tasks.

Steiner's [18] process loss framework provides our analytical lens for understanding when multi-agent designs underperform. Actual productivity equals potential productivity minus process loss. In LLM multi-agent systems, motivation loss (a major factor in human groups) is absent, leaving only coordination loss—information distortion across message chains, redundant processing, and synchronization overhead. Our Communication Efficiency metric directly quantifies this coordination loss.

Woolley et al.'s [19] collective intelligence research suggests that group performance depends more on the quality of interaction than on individual member ability—a hypothesis we test by comparing configurations where the strongest model is concentrated at the top (CEO) versus distributed across all agents.

We emphasize that we use these theories as **sources of testable hypotheses about information flow design**, not as theories to be validated in their full scope. LLM agents lack the human factors (culture, motivation, politics) that are central to these theories' explanatory power in human organizations. Our study tests only the information-flow predictions that these theories generate.

### 2.4 Distinguishing Three Layers of Information Flow Design

Existing literature conflates what we argue are three distinct design dimensions:

**Communication topology** defines which agents can exchange messages. This is the layer that MacNet [15], G-Designer [16], and MultiAgentBench [20] vary. It is well-modeled as a directed graph where nodes are agents and edges are communication channels.

**Authority structure** defines who holds decision-making power—who can approve, reject, or modify the outputs of other agents. Two systems with identical star-topology communication (all messages routed through a central node) can differ dramatically if one implements democratic voting among all agents while the other grants the central node unilateral decision authority.

**Review protocol** defines the quality control pipeline—how many review stages exist, which expertise each reviewer brings, and whether review is sequential or parallel. This layer is distinct from both communication (a reviewer may have communication access to all agents but only review authority over specific ones) and authority (a reviewer may flag issues without having the authority to override decisions).

Our experimental design varies these three layers independently. While we acknowledge that in practice these layers interact (and our analysis examines these interactions), their conceptual separation enables us to attribute observed effects to specific design choices rather than to undifferentiated "structure."

### 2.5 Multi-Agent Benchmarks

Existing benchmarks for multi-agent systems evaluate capabilities orthogonal to our focus. AgentBench [21] evaluates single-agent reasoning across 8 environments. MultiAgentBench [20] (ACL 2025) compares communication protocols (star, chain, tree, graph) but operates at the communication topology layer only, without varying authority structure or review protocol, and evaluates through task success rate rather than multi-dimensional quality assessment. Neither includes single-agent baselines calibrated to match the total compute budget of multi-agent runs.

OrgBench fills this gap by: (1) varying all three layers of information flow design as independent variables; (2) including a strong single-agent baseline; (3) using open-ended business proposal tasks where quality is multi-dimensional rather than binary; (4) operationalizing task uncertainty through objective indicators; and (5) requiring replicated runs to ensure statistical reliability.

---

## 3. OrgBench Framework

### 3.1 System Architecture

OrgBench is built on the PJ_Anima agent-core, a multi-agent orchestration system that has been validated through end-to-end LLM execution with 6 agents, 18 LLM calls per run, at approximately $0.07 per run. The system supports heterogeneous model assignment (different LLM providers per agent), configurable communication topologies, role-based system prompts, and structured message passing with review gates.

The key architectural feature enabling OrgBench is the **externalization of information flow design into declarative YAML templates**. Each template specifies: (1) agent definitions (role, model, system prompt); (2) communication topology (which agents can send messages to which); (3) authority relations (who reviews whose output, who holds approval authority); and (4) review protocol (number of review stages, review criteria, escalation rules). The orchestration engine reads a template and instantiates the corresponding multi-agent system without code changes, ensuring that observed differences in output quality are attributable to the information flow design alone.

All configurations share the same underlying execution engine, tool access (Tavily web search API with cached results for reproducibility), and output format specification. Variation occurs exclusively at the information flow design layer.

### 3.2 Information Flow Design Templates

#### 3.2.1 Design Space

Our design space spans four independent dimensions:

**Dimension 1: Communication Topology (2 levels)**

| Level | Description | Graph Property |
|-------|-------------|----------------|
| Hub-and-spoke | All messages route through a central node (CEO). Peripheral agents cannot communicate directly. | Star graph, diameter 2 |
| Mesh | All agents can communicate with all others. Messages may be sent directly between any pair. | Complete graph, diameter 1 |

**Dimension 2: Authority Structure (3 levels)**

| Level | Description | Decision Pattern |
|-------|-------------|-----------------|
| Deep Hierarchy | CEO delegates to middle managers (TL, CFO, CDO), who in turn direct workers (Researcher, Writer). Decisions escalate upward through the chain. | Strictly vertical |
| Flat | CEO directly oversees all 5 other agents. No middle management layer. All agents report directly to CEO. | Single-level |
| Matrix | Agents report to multiple superiors along functional and project axes. Researcher reports to both TL (project) and CDO (function); Writer reports to both TL and CFO. | Dual reporting |

**Dimension 3: Review Protocol (3 levels)**

| Level | Description | Review Composition |
|-------|-------------|-------------------|
| Finance-heavy | Two-stage financial review (CFO + dedicated financial analyst role) with single-stage technical review. | 2 finance gates, 1 tech gate |
| Tech-heavy | Two-stage technical review (CDO + dedicated technical analyst role) with single-stage financial review. | 1 finance gate, 2 tech gates |
| Balanced | Parallel single-stage review by both CFO and CDO with equal weight. | 1 finance gate, 1 tech gate |

**Dimension 4: Model Heterogeneity (3 levels)**

| Level | Models Used | Rationale |
|-------|-------------|-----------|
| Homogeneous-A | All agents use Claude Sonnet | Control for model-specific biases |
| Homogeneous-B | All agents use GPT-4o-mini | Cross-model replication |
| Heterogeneous | CEO: Claude Sonnet; TL/CFO/CDO: GPT-4o-mini; Researcher: Gemini Flash; Writer: GPT-4o-mini | Cognitive diversity hypothesis |

The full factorial combination yields 2 × 3 × 3 × 3 = **54 multi-agent configurations**. All configurations use exactly 6 agents.

#### 3.2.2 Single-Agent Baseline

In addition to the 54 multi-agent configurations, we include one optimized single-agent baseline:

**Single-Agent-Strong.** A single instance of the highest-capability model (Claude Sonnet) receives a carefully engineered prompt that integrates the perspectives of all six roles. The prompt instructs the agent to: (1) conduct market research as a Researcher would; (2) analyze financial viability as a CFO would; (3) evaluate technical feasibility as a CDO would; (4) synthesize findings into a coherent proposal as a Writer would; (5) perform a self-review against financial and technical criteria; and (6) produce the final deliverable.

This baseline is deliberately designed to be as strong as possible—it uses the best available model, the most comprehensive prompt, and is unconstrained by the communication overhead and potential information loss of multi-agent interaction. If multi-agent configurations cannot outperform this baseline, the implication is clear: for the task class under study, information flow design does not add value beyond what prompt engineering alone can achieve. This would itself be a significant empirical contribution.

The total compute budget (in tokens) for the single-agent baseline is set to match the median compute budget of the 54 multi-agent configurations, ensuring a fair comparison.

#### 3.2.3 No-Review Control

Among the 54 multi-agent configurations, the Review Protocol dimension does not include a "no review" level in the full factorial design (as this would conflate review absence with the other dimensions). Instead, we include a **dedicated No-Review control configuration**: Deep Hierarchy topology with hub-and-spoke communication, Heterogeneous models, and no CFO/CDO review gates. The CEO directly integrates Researcher and Writer outputs without specialist review. This control allows us to quantify the marginal value of review processes independent of other design choices.

### 3.3 Task Design

#### 3.3.1 Task Structure

Each task presents a business domain and requires the multi-agent system (or single agent) to produce a structured business proposal containing:

1. **Executive Summary** (problem statement and proposed solution)
2. **Market Analysis** (target market size, competitive landscape, customer segments)
3. **Technical Approach** (core technology, development roadmap, technical risks)
4. **Financial Projections** (revenue model, cost structure, break-even analysis, 3-year projections)
5. **Risk Assessment** (market, technical, financial, and regulatory risks with mitigation strategies)
6. **Implementation Plan** (milestones, resource requirements, timeline)

All configurations receive identical task prompts specifying these requirements. The structured output format enables automated completeness scoring and facilitates consistent evaluation across configurations.

#### 3.3.2 Theme Set

We select 20 business themes spanning 5 domains (Healthcare, FinTech, AgriTech/CleanTech, Consumer Tech, DeepTech/GovTech), with 4 themes per domain. Themes are selected to span a range of uncertainty levels, from well-established markets with abundant information (e.g., "AI-powered accounting automation for SMEs") to frontier domains with sparse information (e.g., "Space debris removal as a service").

| # | Theme | Domain | Subjective Difficulty |
|---|-------|--------|----------------------|
| 1 | AI fitness app for elderly | Healthcare | Medium |
| 2 | AI accounting automation for SMEs | FinTech | Low |
| 3 | Agricultural IoT data platform | AgriTech | High |
| 4 | Gen-Z mental health social network | HealthTech | Medium |
| 5 | DX support SaaS for local shopping districts | RetailTech | Low |
| 6 | Space debris removal service | DeepTech | Very High |
| 7 | Pet wearable health device | IoT | Medium |
| 8 | AI tutor subscription service | EdTech | Low |
| 9 | Carbon credit exchange platform | CleanTech | High |
| 10 | Municipal disaster prevention AI | GovTech | High |
| 11 | Personalized nutrition AI from gut microbiome | HealthTech | High |
| 12 | Cross-border remittance for migrant workers | FinTech | Medium |
| 13 | Precision fermentation food platform | AgriTech | Very High |
| 14 | AI-driven insurance underwriting | FinTech | Medium |
| 15 | Autonomous last-mile delivery robots | Consumer Tech | High |
| 16 | Digital twin for building energy optimization | CleanTech | High |
| 17 | Sleep quality improvement wearable | Consumer Tech | Medium |
| 18 | AI legal contract review SaaS | LegalTech | Medium |
| 19 | Quantum computing cloud access for SMEs | DeepTech | Very High |
| 20 | AI-powered local government citizen service chatbot | GovTech | Low |

#### 3.3.3 Task Uncertainty Operationalization

A central contribution of this study is the operationalization of task uncertainty through objective indicators, enabling a rigorous test of the contingency hypothesis (RQ4). We measure uncertainty along three objective dimensions and one subjective dimension:

**Objective Indicator 1: Information Availability.**
For each theme, we issue 5 standardized search queries (theme name + "market size," "business model," "technology stack," "competitors," "regulation") via the Tavily API and record the total number of high-relevance results. Themes with fewer results have lower information availability, corresponding to higher Galbraithian uncertainty (more information must be generated during the task rather than retrieved).

**Objective Indicator 2: Knowledge Accumulation.**
We query the Semantic Scholar API for the number of academic publications matching each theme's keywords (published 2020–2026). Domains with sparse academic coverage represent higher uncertainty.

**Objective Indicator 3: Market Maturity.**
We manually survey the number of existing companies, startups, and products in each theme's domain using Crunchbase and public databases. Crowded markets indicate lower uncertainty; greenfield markets indicate higher uncertainty.

**Subjective Indicator: Expert-Rated Difficulty.**
Five human raters (with business and technology backgrounds) independently rate each theme on a 5-point scale for "How difficult would it be to write a high-quality business proposal for this theme?" We report inter-rater reliability (Fleiss' κ).

**Integration.** The three objective indicators are z-score normalized and averaged to produce an **Objective Uncertainty Score (OUS)** for each theme. We report the Spearman correlation between OUS and the subjective difficulty rating to assess construct validity. For the RQ4 analysis, we classify themes into three uncertainty groups (Low / Medium / High) based on OUS tertiles. We repeat the analysis using subjective ratings as a robustness check.

### 3.4 Web Search Caching for Reproducibility

Because web search results vary over time, we implement a caching layer that records all Tavily API responses during the first run of each theme and replays identical results for all subsequent runs (across all configurations and replications). This ensures that variation in output quality is attributable to information flow design rather than to differences in retrieved information.

---

## 4. Evaluation Methodology

### 4.1 Overview

Our evaluation pipeline consists of three layers, each serving a distinct purpose:

| Layer | Scope | Purpose |
|-------|-------|---------|
| LLM-as-Judge | All 5,500 outputs | Scalable primary evaluation across 6 quality dimensions |
| Automated Metrics | All 5,500 outputs | Objective structural and efficiency measures |
| Human Validation | 55-output subset | Validation of LLM-as-Judge reliability; not a primary evaluation |

### 4.2 LLM-as-Judge Evaluation (Primary)

Each of the 5,500 outputs is evaluated by two LLM judges on six quality dimensions using a standardized rubric.

#### 4.2.1 Quality Dimensions

| Dimension | Definition | Scale |
|-----------|------------|-------|
| **Feasibility** | How realistic and implementable is the proposed business? Considers market demand evidence, resource requirements, and regulatory constraints. | 1–5 |
| **Novelty** | How original is the proposal? Considers differentiation from existing solutions and creative approaches. | 1–5 |
| **Market Insight** | How well does the proposal demonstrate understanding of the target market, customer needs, and competitive landscape? | 1–5 |
| **Financial Rigor** | How sound are the financial projections? Considers revenue model clarity, cost structure completeness, and assumption reasonableness. | 1–5 |
| **Technical Depth** | How thorough is the technical analysis? Considers technology choice justification, development roadmap realism, and technical risk identification. | 1–5 |
| **Overall Quality** | Holistic assessment of the proposal as a document that could inform a real investment or go/no-go decision. | 1–5 |

Each dimension is accompanied by a detailed rubric with anchor descriptions for scores 1, 3, and 5 (provided in Appendix A of the final paper).

#### 4.2.2 Bias Mitigation

LLM-as-Judge evaluation is subject to known biases, including self-preference bias (an LLM rating its own outputs higher) and position bias. We mitigate these through four design choices:

1. **Evaluator–generator separation.** We use an LLM not used in any generation configuration as the primary evaluator. If generation uses Claude Sonnet, GPT-4o-mini, and Gemini Flash, we use GPT-4.1 as the primary evaluator and a second independent model as the secondary evaluator.

2. **Multi-evaluator consensus.** Each output is evaluated by two independent LLM judges. We report inter-judge agreement (Cohen's κ) and use the average score for analysis. Outputs with large disagreements (|score difference| ≥ 2) are flagged for human adjudication.

3. **Blinding.** All configuration identifiers, model names, and agent role labels are stripped from outputs before evaluation. The judge sees only the structured business proposal text.

4. **Randomized presentation order.** Outputs are presented to judges in randomized order to prevent position-based rating drift.

### 4.3 Automated Metrics

| Metric | Computation | Measures |
|--------|-------------|----------|
| **Completeness Score** | Proportion of required sections (§3.3.1) present and non-trivially filled (>50 words) | Structural coverage |
| **Specificity Score** | Density of named entities, numerical values, and concrete examples per 1,000 words | Concreteness vs. vagueness |
| **Inter-Configuration Diversity** | Mean pairwise cosine distance of output embeddings (text-embedding-3-large) across configurations for the same theme | Whether different designs produce meaningfully different outputs |
| **Communication Efficiency** | Total message count and total LLM API calls to completion | Coordination overhead |
| **Cost Efficiency** | Overall Quality score / total API cost in USD | Quality per dollar |

### 4.4 Human Validation

The purpose of human evaluation in our design is **not** to serve as a primary quality measure (which would be infeasible at 5,500 outputs) but to **validate that LLM-as-Judge scores are meaningful proxies for human quality judgments**.

#### 4.4.1 Subset Selection

We select a representative subset of 55 outputs for human evaluation:
- 9 multi-agent configurations (one per combination of the 3 Topology levels × 3 Review Protocol levels, holding Communication = Hub-and-spoke and Model = Heterogeneous)
- 1 No-Review control
- 1 Single-Agent-Strong baseline
- Each evaluated on the same 5 themes (selected to span the uncertainty range)
- 1 replication per condition (randomly selected from the 5 available)

#### 4.4.2 Protocol

Three human evaluators with mixed business and technology backgrounds independently rate each of the 55 outputs on the same 6-dimension rubric used by the LLM judges. Evaluators receive a 30-minute training session with 3 calibration examples (not from the main experiment).

We report:
- **Fleiss' κ** for inter-rater reliability on each dimension.
- **Spearman rank correlation** between mean human scores and mean LLM-as-Judge scores, per dimension.
- A correlation of ρ ≥ 0.7 on Overall Quality is our pre-registered threshold for considering LLM-as-Judge evaluation sufficiently valid.

**Contingency plan.** If Fleiss' κ < 0.4 on a dimension, we consider that dimension unreliable for human evaluation and either: (a) merge it with a related dimension (e.g., Market Insight + Feasibility), (b) increase rater training and re-evaluate, or (c) report results on that dimension as exploratory only.

If LLM–human correlation falls below ρ = 0.5 on any dimension, we investigate the source of disagreement and report that dimension's LLM-as-Judge results with appropriate caveats.

---

## 5. Experimental Design

### 5.1 Configurations Summary

| Category | Count | Description |
|----------|-------|-------------|
| Multi-agent (full factorial) | 54 | 2 Communication × 3 Authority × 3 Review × 3 Model |
| No-Review control | 1 | Deep Hierarchy, Hub-and-spoke, Heterogeneous, no review gates |
| Single-Agent-Strong | 1 | Claude Sonnet with integrated multi-role prompt |
| **Total** | **55** (with 1 overlap: No-Review is part of a planned comparison, not a 55th factorial cell) |

Note: The No-Review control shares its Communication × Authority × Model settings with one of the 54 factorial configurations but differs in review protocol (none vs. balanced/finance/tech). It is analyzed as a separate contrast rather than as a factorial level.

### 5.2 Replication

Each of the 55 configurations is run on each of the 20 themes **5 times**, yielding **5,500 total runs**. The replication count is determined by:

1. **Statistical necessity.** At temperature = 0.7, LLM output variance is substantial. Without replication, observed quality differences between configurations could reflect stochastic fluctuation rather than design effects. With 5 replications per cell, we obtain 100 observations per configuration (5 × 20 themes) and 25 observations per cell in the Topology × Uncertainty interaction analysis (5 reps × ~7 themes per uncertainty level), sufficient to detect medium effect sizes (η² ≈ .06) at α = .05 with power ≈ .80.

2. **Budget constraint.** At $0.07 per run, 5,500 runs cost approximately $385. Adding LLM-as-Judge evaluation (~$40) and uncertainty indicator API calls (~$10) brings the total API cost to approximately $435, within our budget ceiling of $500.

### 5.3 Controlled Variables

| Variable | Control Method |
|----------|---------------|
| Agent count | Fixed at 6 for all multi-agent configurations |
| Temperature | Fixed at 0.7 for all LLM calls (generation and review) |
| Max tokens | Fixed at 2,048 per agent per call |
| Execution timeout | Fixed at 10 minutes per run |
| Web search | Tavily API with cached results (§3.4); identical search results across all configurations and replications for a given theme |
| Output format | Identical 6-section structure specification in all task prompts |
| Single-agent compute budget | Set to match median multi-agent total token consumption |

### 5.4 Analysis Plan

#### 5.4.1 RQ0: Does Multi-Agent Structure Add Value?

- **Test:** Welch's t-test comparing Single-Agent-Strong mean Overall Quality (across 20 themes × 5 reps = 100 observations) against the best-performing multi-agent configuration's mean Overall Quality.
- **Effect size:** Cohen's d.
- **Interpretation:**
  - If Single-Agent-Strong ≈ Best-Multi (d < 0.2): Information flow design does not add value beyond prompt engineering for this task class. Report as a significant negative finding.
  - If Best-Multi > Single-Agent-Strong (d ≥ 0.2): Multi-agent structure adds measurable value. Proceed to analyze which design dimensions drive the advantage.
  - If Single-Agent-Strong > all Multi (d ≥ 0.2): Multi-agent coordination loss exceeds information processing gains. Quantify the loss using Steiner's framework.

#### 5.4.2 RQ1: Topology Effects

- **Test:** One-way ANOVA with Topology (3 levels) as the factor, applied to each quality dimension. Post-hoc pairwise comparisons via Tukey's HSD.
- **Effect size:** η² (partial eta-squared).
- **Aggregation:** Scores are averaged across Review Protocol, Model Heterogeneity, and Communication levels within each Topology level (i.e., marginal means).

#### 5.4.3 RQ2: Review Gate Effects

- **Test 1:** One-way ANOVA with Review Protocol (3 levels) as the factor.
- **Test 2:** Contrast of No-Review control vs. mean of all reviewed configurations (Dunnett's test).
- **Test 3:** Two-way ANOVA (Review Protocol × Quality Dimension) to test whether the review effect is dimension-specific (e.g., Finance-heavy review improves Financial Rigor but not Novelty).

#### 5.4.4 RQ3: Model Heterogeneity Effects

- **Test:** Kruskal-Wallis test across 3 Model Heterogeneity levels (non-parametric, as model effects may violate normality assumptions). Post-hoc Mann-Whitney U for pairwise comparisons.
- **Supplementary:** Compare Homogeneous-A vs. Homogeneous-B to isolate absolute model capability differences from heterogeneity effects.

#### 5.4.5 RQ4: Contingency Hypothesis

- **Test:** Two-way ANOVA with Topology (3 levels) × Uncertainty (3 levels, based on OUS tertiles) on Overall Quality. A significant interaction term supports the contingency hypothesis.
- **Robustness:** Repeat with subjective difficulty as the uncertainty measure.
- **Visualization:** Interaction plot (Topology × Uncertainty) for each quality dimension.
- **Effect size:** η² for the interaction term.

#### 5.4.6 Exploratory Analyses

- Communication pattern analysis: graph-level metrics (degree distribution, average path length, clustering coefficient) of actual message flow vs. designed topology.
- Cost–quality Pareto frontier: which configurations achieve the best quality at each cost level?
- Within-configuration variance: do some designs produce more consistent outputs than others? (Levene's test for equality of variances across configurations.)

### 5.5 Pre-Registered Outcome Scenarios

We commit to the following interpretive framework before data collection:

| Scenario | Condition | Interpretation | Paper Narrative |
|----------|-----------|----------------|-----------------|
| **A** | Single-Agent-Strong ≈ Best-Multi (d < 0.2) AND no significant Topology effects | Information flow design is irrelevant for this task class | "Prompt engineering, not organizational design, drives quality. Multi-agent structure adds coordination cost without commensurate benefit." |
| **B** | Best-Multi > Single-Agent-Strong (d ≥ 0.2) AND significant Topology effects | Information flow design is a genuine quality lever | "OrgBench demonstrates that information flow design is an independent quality determinant. [Specific design] achieves [X]% improvement over single-agent." |
| **C** | Best-Multi > Single-Agent-Strong BUT no significant differences among multi-agent configs | Multi-agent helps, but which topology doesn't matter | "The benefit of multi-agent collaboration is real but structure-agnostic—any reasonable multi-agent design outperforms single-agent." |
| **D** | Significant Topology × Uncertainty interaction | Contingency theory confirmed in LLM agents | "Optimal information flow design is task-dependent. For low-uncertainty tasks, [X] is recommended; for high-uncertainty tasks, [Y]." |

---

## References

[1] Q. Wu et al., "AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation," COLM 2024, arXiv:2308.08155.

[2] S. Hong et al., "MetaGPT: Meta Programming for A Multi-Agent Collaborative Framework," ICLR 2024, arXiv:2308.00352.

[3] C. Qian et al., "ChatDev: Communicative Agents for Software Development," ACL 2024, arXiv:2307.07924.

[4] J. R. Galbraith, *Designing Complex Organizations*, Addison-Wesley, 1973.

[5] H. Mintzberg, *The Structuring of Organizations*, Prentice-Hall, 1979.

[6] P. R. Lawrence and J. W. Lorsch, *Organization and Environment*, Harvard Business School Press, 1967.

[7] T. Burns and G. M. Stalker, *The Management of Innovation*, Tavistock, 1961.

[8] Q. Wang et al., "Rethinking the Bounds of LLM Reasoning: Are Multi-Agent Discussions the Key?" ACL 2024, arXiv:2402.18272.

[9] "Budget-Aware Evaluation of LLM Reasoning Strategies," EMNLP 2024.

[10] J. Kaesberg et al., "Voting or Consensus? Decision-Making in Multi-Agent Debate," ACL 2025 Findings, arXiv:2502.19130.

[11] "Debate or Vote: Which Yields Better Decisions?" arXiv:2508.17536, 2025.

[12] G. Li et al., "CAMEL: Communicative Agents for 'Mind' Exploration of Large Language Model Society," NeurIPS 2023, arXiv:2303.17760.

[13] W. Chen et al., "AgentVerse: Facilitating Multi-Agent Collaboration and Exploring Emergent Behaviors," ICLR 2024, arXiv:2308.10848.

[14] J. S. Park et al., "Generative Agents: Interactive Simulacra of Human Behavior," UIST 2023, arXiv:2304.03442.

[15] C. Qian et al., "Scaling Large Language Model-Based Multi-Agent Collaboration," ICLR 2025, arXiv:2406.07155.

[16] Y. Yao et al., "G-Designer: Architecting Multi-agent Communication Topologies via Graph Neural Networks," ICML 2025, arXiv:2410.11782.

[17] "Topological Structure Learning Should Be A Research Priority for LLM-Based MAS," arXiv:2505.22467, 2025.

[18] I. D. Steiner, *Group Process and Productivity*, Academic Press, 1972.

[19] A. W. Woolley et al., "Evidence for a Collective Intelligence Factor in the Performance of Human Groups," *Science*, vol. 330, no. 6004, pp. 686–688, 2010.

[20] "MultiAgentBench: Evaluating the Collaboration and Competition of LLM agents," ACL 2025, arXiv:2503.01935.

[21] X. Liu et al., "AgentBench: Evaluating LLMs as Agents," ICLR 2024, arXiv:2308.03688.

---

*End of Draft v0.1 — Sections 1–5 (Introduction through Experimental Design)*
