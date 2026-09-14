"""Experimental DAG-Informed Bayesian Knowledge Tracing Variants.

Encapsulates instructional graph dependencies behind an explicit strategy boundary
to ensure experimental modularity and reversibility without altering baseline BKT invariants.
"""
from enum import Enum
import networkx as nx

from ace.domain.learner import SkillMasteryState
from ace.learner.bkt import BKTModel, BKTParameters


class BKTStrategy(str, Enum):
    """Execution strategy for Bayesian Knowledge Tracing."""
    BASELINE = "baseline"                   # Standard independent BKT (Default production)
    PER_SKILL = "per_skill"                 # Hierarchical skill-specific parameters
    DAG_PRIOR = "dag_prior"                 # Experimental: Prior P(L0) modulated by parent mastery
    DAG_PROPAGATION = "dag_propagation"     # Experimental: Soft evidence flow across instructional edges


class DAGConditionedBKT:
    """Experimental wrapper evaluating prerequisite DAG heuristics over baseline BKT."""

    def __init__(
        self,
        graph: nx.DiGraph | None = None,
        bkt_model: BKTModel | None = None,
        strategy: BKTStrategy = BKTStrategy.BASELINE,
    ) -> None:
        self.graph = graph or nx.DiGraph()
        self.bkt = bkt_model or BKTModel()
        self.strategy = strategy

    def get_conditioned_prior(
        self,
        skill_id: str,
        learner_masteries: dict[str, float],
    ) -> float:
        """Calculate initial prior P(L0), optionally conditioned on prerequisite parent masteries."""
        base_params = self.bkt.get_params_for_skill(skill_id)
        base_p0 = base_params.p_l0

        if self.strategy != BKTStrategy.DAG_PRIOR or skill_id not in self.graph:
            return base_p0

        parents = list(self.graph.predecessors(skill_id))
        if not parents:
            return base_p0

        parent_masteries = [learner_masteries.get(p, 0.0) for p in parents]
        mean_parent_mastery = sum(parent_masteries) / len(parent_masteries)

        # Modulate prior: if parents are unmastered, prior drops; if mastered, stays near base_p0
        conditioned_p0 = base_p0 * (0.20 + 0.80 * mean_parent_mastery)
        return round(max(0.01, min(0.50, conditioned_p0)), 4)

    def update_state(
        self,
        state: SkillMasteryState,
        evidence: float | bool,
        evidence_id: str | None = None,
        difficulty: int | None = None,
        learner_masteries: dict[str, float] | None = None,
    ) -> SkillMasteryState:
        """Update state using the configured BKT strategy."""
        # Baseline & Per-Skill delegate directly to core BKT
        return self.bkt.update_state(
            state=state,
            evidence=evidence,
            evidence_id=evidence_id,
            difficulty=difficulty,
        )
