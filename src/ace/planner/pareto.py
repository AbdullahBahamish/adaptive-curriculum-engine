"""Pareto Frontier Optimizer and Trade-off Analysis.

Identifies non-dominated candidate pathways and synthesizes human-interpretable
trade-off explanations across conflicting pedagogical objectives.
"""
from dataclasses import dataclass
from typing import Any

from ace.planner.scorer import PathwayObjectiveScores


@dataclass
class ParetoCandidate:
    """A scored candidate pathway evaluated for Pareto dominance."""
    strategy: str
    skill_ids: list[str]
    scores: PathwayObjectiveScores


@dataclass
class ParetoTradeoff:
    """Human-readable trade-off explanation for an alternative pathway."""
    strategy: str
    is_recommended: bool
    composite_score: float
    key_strengths: list[str]
    tradeoffs_vs_primary: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "strategy": self.strategy,
            "is_recommended": self.is_recommended,
            "composite_score": self.composite_score,
            "key_strengths": self.key_strengths,
            "tradeoffs_vs_primary": self.tradeoffs_vs_primary,
        }


class ParetoOptimizer:
    """Calculates non-dominated Pareto frontier and summarizes multi-objective trade-offs."""

    @staticmethod
    def dominates(a: PathwayObjectiveScores, b: PathwayObjectiveScores) -> bool:
        """Return True if score vector `a` strictly dominates `b`."""
        vec_a = [
            a.goal_alignment,
            a.gap_reduction,
            a.difficulty_smoothness,
            a.time_budget_fit,
            a.category_continuity,
        ]
        vec_b = [
            b.goal_alignment,
            b.gap_reduction,
            b.difficulty_smoothness,
            b.time_budget_fit,
            b.category_continuity,
        ]

        all_ge = all(x >= y for x, y in zip(vec_a, vec_b))
        any_gt = any(x > y for x, y in zip(vec_a, vec_b))
        return all_ge and any_gt

    def extract_frontier(self, candidates: list[ParetoCandidate]) -> list[ParetoCandidate]:
        """Return subset of candidates that are not dominated by any other candidate."""
        frontier: list[ParetoCandidate] = []
        for i, cand in enumerate(candidates):
            dominated = False
            for j, other in enumerate(candidates):
                if i != j and self.dominates(other.scores, cand.scores):
                    dominated = True
                    break
            if not dominated:
                frontier.append(cand)
        return frontier

    def explain_tradeoffs(
        self,
        recommended: ParetoCandidate,
        alternatives: list[ParetoCandidate],
    ) -> list[ParetoTradeoff]:
        """Generate human-interpretable trade-off summaries comparing alternatives to recommended."""
        results: list[ParetoTradeoff] = []

        # Tradeoff for primary path
        primary_strengths = self._identify_strengths(recommended.scores)
        results.append(
            ParetoTradeoff(
                strategy=recommended.strategy,
                is_recommended=True,
                composite_score=recommended.scores.composite_score,
                key_strengths=primary_strengths,
                tradeoffs_vs_primary=["Primary path selected as the optimal multi-objective balance."],
            )
        )

        # Tradeoffs for alternatives
        for alt in alternatives:
            if alt.strategy == recommended.strategy:
                continue

            alt_strengths = self._identify_strengths(alt.scores)
            tradeoffs: list[str] = []

            # Compare individual objectives
            if alt.scores.goal_alignment > recommended.scores.goal_alignment + 0.05:
                diff = int(round((alt.scores.goal_alignment - recommended.scores.goal_alignment) * 100))
                tradeoffs.append(f"+{diff}% higher early career goal alignment")
            elif alt.scores.goal_alignment < recommended.scores.goal_alignment - 0.05:
                diff = int(round((recommended.scores.goal_alignment - alt.scores.goal_alignment) * 100))
                tradeoffs.append(f"-{diff}% lower early career goal alignment")

            if alt.scores.difficulty_smoothness > recommended.scores.difficulty_smoothness + 0.05:
                diff = int(round((alt.scores.difficulty_smoothness - recommended.scores.difficulty_smoothness) * 100))
                tradeoffs.append(f"+{diff}% smoother cognitive difficulty gradient")
            elif alt.scores.difficulty_smoothness < recommended.scores.difficulty_smoothness - 0.05:
                diff = int(round((recommended.scores.difficulty_smoothness - alt.scores.difficulty_smoothness) * 100))
                tradeoffs.append(f"-{diff}% steeper difficulty gradient (more challenging early steps)")

            if alt.scores.category_continuity > recommended.scores.category_continuity + 0.10:
                diff = int(round((alt.scores.category_continuity - recommended.scores.category_continuity) * 100))
                tradeoffs.append(f"+{diff}% higher domain clustering (reduced context switching)")

            if alt.scores.time_budget_fit > recommended.scores.time_budget_fit + 0.05:
                tradeoffs.append("Better alignment with short-term time budget constraints")

            if not tradeoffs:
                tradeoffs.append("Comparable multi-objective profile with alternative step sequencing.")

            results.append(
                ParetoTradeoff(
                    strategy=alt.strategy,
                    is_recommended=False,
                    composite_score=alt.scores.composite_score,
                    key_strengths=alt_strengths,
                    tradeoffs_vs_primary=tradeoffs,
                )
            )

        return results

    def _identify_strengths(self, scores: PathwayObjectiveScores) -> list[str]:
        strengths: list[str] = []
        if scores.goal_alignment >= 0.8:
            strengths.append("High early career goal alignment")
        if scores.difficulty_smoothness >= 0.8:
            strengths.append("Smooth cognitive progression")
        if scores.gap_reduction >= 0.8:
            strengths.append("Rapid critical gap elimination")
        if scores.category_continuity >= 0.7:
            strengths.append("High category continuity")
        if scores.time_budget_fit >= 0.9:
            strengths.append("Optimal time budget fit")
        if not strengths:
            strengths.append("Balanced multi-factor sequencing")
        return strengths
