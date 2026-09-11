# Architecture & Intelligence Layers

The **Adaptive Curriculum Engine (ACE)** is a production-grade, resource-efficient intelligent learning-path engine operating under strict local CPU and RAM constraints.

---

## 1. High-Level Architecture Diagram

```
                                  [ Client Request ]
                                          │
                                          ▼
                      ┌─────────────────────────────────────────┐
                      │          ACE API Layer (FastAPI)        │
                      │   /gap-analysis  •  /learning-path      │
                      │   /mastery/update • /semantic/match     │
                      └───────────────────┬─────────────────────┘
                                          │
                  ┌───────────────────────┴───────────────────────┐
                  ▼                                               ▼
     ┌────────────────────────┐                     ┌───────────────────────────┐
     │  Layer B: Learner Model│                     │ Layer D: Semantic Matcher │
     │  • SkillMasteryState   │                     │ • EmbeddingProvider       │
     │  • LearningPreferences │                     │ • Persistent Vector Cache │
     │  • BKT Probabilistic   │                     │ • Precomputed 112 Skills  │
     │    Mastery Estimation  │                     │ • Cosine Vector Index     │
     └────────────┬───────────┘                     └─────────────┬─────────────┘
                  │                                               │
                  └───────────────────────┬───────────────────────┘
                                          ▼
                      ┌─────────────────────────────────────────┐
                      │    Layer E: Knowledge-Gap Analysis      │
                      │    Weighted Gap: Importance × Relevance │
                      │    × (1 - Mastery) × PrerequisiteImpact │
                      │    Categorization & Reason Codes        │
                      └───────────────────┬─────────────────────┘
                                          │
                                          ▼
                      ┌─────────────────────────────────────────┐
                      │  Layer A: Prerequisite Knowledge Graph  │
                      │  • Strict DAG Invariants (0 Cycles)     │
                      │  • Ancestor Closure Memoization         │
                      │  • Centrality & Depth Metrics           │
                      └───────────────────┬─────────────────────┘
                                          │
                                          ▼
                      ┌─────────────────────────────────────────┐
                      │ Layer F: Candidate Pathway Generator    │
                      │ Bounded Search (Foundational, Goal-First│
                      │ Quick-Wins, Clustered, Beam Search)     │
                      │ 100% Valid Topological Sequences        │
                      └───────────────────┬─────────────────────┘
                                          │
                                          ▼
                      ┌─────────────────────────────────────────┐
                      │ Layer G & H: Multi-Objective Ranking    │
                      │ • Scoring: Alignment, Smoothness, Time  │
                      │ • Pareto Frontier (Trade-off Analysis)  │
                      │ • PathRanker (Rule-Based, Linear, Hybrid│
                      └───────────────────┬─────────────────────┘
                                          │
                                          ▼
                      ┌─────────────────────────────────────────┐
                      │   Layer I: Structured Explainability    │
                      │   • Machine-Readable Reason Codes       │
                      │   • Grounded LLM / Deterministic Rationale
                      └─────────────────────────────────────────┘
```

---

## 2. Layer Specifications

### Layer A — Prerequisite Knowledge Graph & Invariants
- **Graph Representation**: Directed Acyclic Graph (DAG) $G = (V, E)$ where nodes $v \in V$ represent skills, and directed edges $(u, v) \in E$ assert that $u$ must be learned before $v$.
- **Hard Invariant**: $\forall v \in V, v \notin \text{Ancestors}(v)$ (zero cycles permitted). Every generated curriculum path satisfies $\forall (u, v) \in E, \text{index}(u) < \text{index}(v)$.
- **Memoized Closures**: Transitive closures $\text{Ancestors}(v)$ and $\text{Descendants}(v)$ are precomputed in topological order.
- **Structural Centrality**:
  $$\text{depth}(v) = 0 \text{ if } \text{InDegree}(v)=0 \text{ else } 1 + \max_{(u, v) \in E} \text{depth}(u)$$
  $$\text{impact}(v) = 1.0 + \ln(1 + |\text{Descendants}(v)|)$$

### Layer B & C — Learner Model & Bayesian Knowledge Tracing (BKT)
- Learner state is represented continuously through `SkillMasteryState`:
  - $P(L_t) \in [0.0, 1.0]$: Probability of latent skill mastery.
  - $\text{confidence} \in [0.0, 1.0]$: Monotonically increasing confidence function based on evidence count $N$ ($1 - e^{-0.35 N}$) and variance.
- BKT Bayesian inference:
  $$P(L_t \mid obs=1) = \frac{P(L_{t-1})(1 - P(S))}{P(L_{t-1})(1 - P(S)) + (1 - P(L_{t-1}))P(G)}$$
  $$P(L_t \mid obs=0) = \frac{P(L_{t-1})P(S)}{P(L_{t-1})P(S) + (1 - P(L_{t-1}))(1 - P(G))}$$
  $$P(L_{t+1}) = P(L_t \mid obs) + (1 - P(L_t \mid obs)) \cdot P(T)$$

### Layer D — Semantic Matching & Vector Indexing
- **Vector Space**: 384-dimensional dense semantic embeddings (`all-MiniLM-L6-v2`).
- **Disk Cache**: Precomputed 112 canonical skill embeddings saved to `data/processed/canonical_skill_embeddings.json`.
- **Runtime Vector Index**: In-memory unit-normalized matrix with NumPy dot-product cosine similarity ($< 0.5\text{ms}$ retrieval on CPU).

### Layer E — Weighted Knowledge-Gap Analysis
- Computes multi-factor priority scores:
  $$\text{gap}(s) = \text{importance}(s) \times \text{target\_relevance}(s) \times (1 - \text{mastery}(s)) \times \text{prerequisite\_impact}(s)$$
- Categorizes skills into 6 distinct tiers: `MISSING`, `WEAKLY_MASTERED`, `ADEQUATELY_MASTERED`, `STRONGLY_MASTERED`, `BLOCKED_BY_PREREQUISITE`, `READY_TO_LEARN`.

### Layer F — Candidate Pathway Generation
- Generates 5 diverse topological candidates:
  1. **Foundational-First**: Prioritizes lowest depth and lowest cognitive difficulty.
  2. **Career-Goal-First**: Schedules high-importance career skills immediately upon prerequisite clearance.
  3. **Quick-Wins**: Prioritizes lowest estimated acquisition hours.
  4. **Domain-Clustered**: Groups related domain categories to minimize context-switching.
  5. **Bounded Beam Search**: Topologically explores candidate sequences with bounded priority queue.

### Layer G & H — Multi-Objective Scoring & Pareto Optimization
- Normalized objective functions:
  - $f_{\text{goal}}(p)$: Discounted cumulative career importance at early steps.
  - $f_{\text{gap}}(p)$: Discounted mastery gap reduction.
  - $f_{\text{smooth}}(p)$: Cognitive difficulty transition smoothness ($1 - \frac{\text{mean}(|\Delta \text{diff}|)}{4}$).
  - $f_{\text{time}}(p)$: Time budget compliance.
  - $f_{\text{cluster}}(p)$: Adjacent domain continuity.
- Non-dominated Pareto frontier extraction: identifies Pareto-optimal pathways and synthesizes structured trade-offs.

### Layer I — Structured Explainability
- Produces machine-readable reason codes (`CAREER_MANDATORY`, `PREREQUISITE_CLEARED`, `CRITICAL_UNBLOCKER`, `SMOOTH_STEP`, `QUICK_WIN`).
- Powers both deterministic structured markdown walk-throughs and grounded LLM mentors.
