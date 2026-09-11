# Curriculum Planner, Candidate Generation & Multi-Objective Ranking

The Curriculum Planner translates diagnosed skill gaps into a personalized, pedagogically coherent, and topologically valid curriculum path.

---

## 1. Candidate Pathway Generation Archetypes

ACE implements 5 distinct candidate generators in `src/ace/planner/candidate_generator.py`:

| Strategy | Sorting Invariant / Priority Key | Pedagogical Goal |
| :--- | :--- | :--- |
| **Foundational-First** (`foundational_first`) | `(depth, difficulty, -unblocks, skill_id)` | Builds rock-solid conceptual grounding before exposing the student to complex applied topics. |
| **Career-Goal-First** (`career_goal_first`) | `(-importance, -target_relevance, depth, skill_id)` | Schedules target career competencies as early as theoretically possible to maximize immediate career utility. |
| **Quick-Wins** (`quick_wins`) | `(estimated_hours, difficulty, -importance, skill_id)` | Starts with short, highly accessible skills to build momentum and early learner self-efficacy. |
| **Domain-Clustered** (`domain_clustered`) | `(category_switch, depth, difficulty, skill_id)` | Minimizes domain context switching by completing skills within the same career category before jumping across disciplines. |
| **Bounded Beam Search** (`bounded_beam_search`) | Combinatorial priority queue (width $B=5$, budget 20ms) | Explores topological space with step rewards balancing career importance and difficulty jumps. |

### Hard Topological Invariant Guarantee
Every generator guarantees that:
$$\forall (u, v) \in E \text{ present in path}, \quad \text{index}(u) < \text{index}(v)$$
Prerequisite violation rate across all generated paths is strictly **0.00%**.

---

## 2. Multi-Objective Scoring

Pathways are scored across 5 normalized pedagogical objectives $f_k(p) \in [0.0, 1.0]$:

### 1. Goal Alignment ($f_{\text{goal}}$)
$$\sum_{i=1}^M \gamma^{i-1} \cdot \frac{\text{importance}(s_i)}{5.0} \Bigg/ \sum_{i=1}^M \gamma^{i-1}$$
where $\gamma = 0.95$ discounts skills appearing later in the curriculum.

### 2. Gap Reduction Efficiency ($f_{\text{gap}}$)
$$\sum_{i=1}^M \gamma^{i-1} \cdot \frac{\text{gap\_score}(s_i)}{\max(\text{gap\_scores})} \Bigg/ \sum_{i=1}^M \gamma^{i-1}$$

### 3. Cognitive Smoothness ($f_{\text{smooth}}$)
$$1.0 - \frac{1}{4(M-1)} \sum_{i=1}^{M-1} |\text{difficulty}(s_{i+1}) - \text{difficulty}(s_i)|$$
Penalizes steep difficulty jumps between adjacent steps.

### 4. Time Budget Fit ($f_{\text{time}}$)
Evaluates compliance against learner's weekly hour budget and semester caps.

### 5. Domain Continuity ($f_{\text{cluster}}$)
$$\frac{1}{M-1} \sum_{i=1}^{M-1} \mathbb{I}(\text{category}(s_{i+1}) == \text{category}(s_i))$$

---

## 3. Pareto Frontier Optimization

A pathway $A$ dominates pathway $B$ ($A \succ B$) if:
$$\forall k, f_k(A) \ge f_k(B) \quad \text{and} \quad \exists k, f_k(A) > f_k(B)$$

The `ParetoOptimizer` extracts non-dominated candidate pathways and synthesizes human-readable trade-off explanations, empowering learners and mentors to make informed curriculum decisions.
