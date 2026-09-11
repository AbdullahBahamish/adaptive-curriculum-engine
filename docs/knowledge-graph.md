# Prerequisite Knowledge Graph & Centrality Formulation

The foundation of ACE is a formal directed prerequisite knowledge graph satisfying strict mathematical invariants.

---

## 1. Graph Definitions and Mathematical Invariants

Let $G = (V, E)$ be a directed graph where:
- $V$ is the set of all canonical skills.
- $E \subseteq V \times V$ is the set of directed prerequisite edges.
- An edge $(u, v) \in E$ indicates that skill $u$ is a prerequisite for skill $v$ (i.e. $u$ must be learned before $v$).

### Strict Acyclicity Invariant
$$\forall v \in V, \quad v \notin \text{Ancestors}(v)$$
ACE enforces that $G$ is strictly a Directed Acyclic Graph (DAG). Cycle detection runs prior to sequence generation (`validate_graph(G)`), guaranteeing zero cyclic dependency lockups.

---

## 2. Graph Metrics & Centrality

ACE implements memoized structural measurements in `src/ace/graph/graph_metrics.py`:

### Prerequisite Depth
The longest dependency chain required to master skill $v$:
$$\text{depth}(v) = \begin{cases} 0 & \text{if } \text{InDegree}(v) = 0 \\ 1 + \max_{(u, v) \in E} \text{depth}(u) & \text{otherwise} \end{cases}$$

### Downstream Unblocking Impact (Centrality)
Quantifies the cognitive leverage of a skill across the curriculum:
$$\text{impact}(v) = 1.0 + \ln(1 + |\text{Descendants}(v)|)$$
Skills with high descendant counts (e.g. `prog_logic`, `data_structures`) receive high centrality impact multipliers ($> 2.5$), prioritizing them early in gap resolution.
