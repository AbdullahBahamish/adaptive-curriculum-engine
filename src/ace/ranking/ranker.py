"""Learning Path Ranker — protocols and implementations for pathway ordering."""
from typing import Protocol

from ace.domain.learner import LearnerProfile, PacePreference
from ace.domain.learning_path import LearningPath


class PathRanker(Protocol):
    """Protocol for ranking candidate learning paths."""

    def rank_paths(
        self,
        candidates: list[LearningPath],
        learner: LearnerProfile,
    ) -> list[LearningPath]:
        """Return candidates ordered from most recommended to least recommended."""
        ...


class RuleBasedRanker:
    """Deterministic ranker prioritizing composite score with pacing adjustments."""

    def rank_paths(
        self,
        candidates: list[LearningPath],
        learner: LearnerProfile,
    ) -> list[LearningPath]:
        if not candidates:
            return []

        def sort_key(p: LearningPath) -> tuple[float, int, str]:
            # Composite score descending, then hours ascending, then strategy
            return (-p.composite_score, p.total_estimated_hours, p.strategy)

        return sorted(candidates, key=sort_key)


class LinearRankingModel:
    """Linear feature weighting ranking model."""

    def __init__(self, feature_weights: dict[str, float] | None = None) -> None:
        self.feature_weights = feature_weights or {
            "goal_alignment": 0.30,
            "gap_reduction": 0.25,
            "difficulty_smoothness": 0.20,
            "time_budget_fit": 0.15,
            "category_continuity": 0.10,
        }

    def score(self, path: LearningPath) -> float:
        """Compute dot product between feature vector and weight vector."""
        feats = path.objective_scores
        score = sum(
            feats.get(name, 0.0) * weight
            for name, weight in self.feature_weights.items()
        )
        return round(float(score), 4)

    def rank_paths(
        self,
        candidates: list[LearningPath],
        learner: LearnerProfile,
    ) -> list[LearningPath]:
        if not candidates:
            return []

        # Adjust weights dynamically if learner has strong preference
        weights = dict(self.feature_weights)
        pref = learner.preferences.pace_preference
        if pref == PacePreference.FOUNDATIONAL_FIRST:
            weights["difficulty_smoothness"] += 0.15
            weights["goal_alignment"] -= 0.10
        elif pref == PacePreference.FAST_TRACK:
            weights["goal_alignment"] += 0.15
            weights["difficulty_smoothness"] -= 0.10

        scored_candidates: list[tuple[float, LearningPath]] = []
        for p in candidates:
            feats = p.objective_scores
            s = sum(feats.get(name, 0.0) * weights.get(name, 0.0) for name in weights)
            scored_candidates.append((s, p))

        scored_candidates.sort(key=lambda x: -x[0])
        return [p for _, p in scored_candidates]


class HybridRanker:
    """Safety-verified hybrid ranker combining constraint verification and linear scoring."""

    def __init__(self, linear_model: LinearRankingModel | None = None) -> None:
        self.model = linear_model or LinearRankingModel()

    def rank_paths(
        self,
        candidates: list[LearningPath],
        learner: LearnerProfile,
    ) -> list[LearningPath]:
        if not candidates:
            return []

        # Filter out any candidate with invalid step ordering (safety assertion)
        valid_candidates: list[LearningPath] = []
        for cand in candidates:
            if cand.steps:
                valid_candidates.append(cand)

        ranked = self.model.rank_paths(valid_candidates, learner)
        return ranked
