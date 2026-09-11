"""Graph Solver — generates topologically sorted and multi-objective ranked learning paths.

Coordinates:
  1. Transitive ancestor expansion for missing prerequisite skills.
  2. Bounded candidate pathway generation (Foundational, Goal-First, Quick-Wins, Clustered, Beam).
  3. Normalized multi-objective scoring (Goal alignment, smoothness, gap reduction, time budget).
  4. Pareto frontier analysis and trade-off summarization.
  5. Machine-readable step reason codes and unblock metrics.
"""
import networkx as nx

from ace.domain.career import Career, CareerSkillRequirement
from ace.domain.learner import ConfirmedSkill, LearnerProfile
from ace.domain.learning_path import LearningPath
from ace.domain.skill import Skill, SkillGap
from ace.explain.structured_rationale import populate_step_rationales
from ace.graph.graph_metrics import get_graph_metrics
from ace.graph.validator import validate_graph
from ace.planner.candidate_generator import CandidatePathwayGenerator
from ace.planner.pareto import ParetoCandidate, ParetoOptimizer
from ace.planner.scorer import MultiObjectivePathScorer
from ace.ranking.ranker import PathRanker, RuleBasedRanker


def generate_learning_path(
    gaps: list[SkillGap],
    graph: nx.DiGraph,
    learner_id: str,
    career_id: str,
    career_name: str,
    confirmed_skill_ids: set[str],
    career: Career | None = None,
    learner: LearnerProfile | None = None,
    all_skills: dict[str, Skill] | None = None,
    ranker: PathRanker | None = None,
    strategy: str | None = None,
    return_alternatives: bool = False,
) -> LearningPath:
    """Generate an optimal, prerequisite-safe, multi-objective learning path.

    Backward compatible with the v0.1 signature while executing the full
    candidate generation, Pareto optimization, and ranking pipeline.
    """
    validate_graph(graph)
    metrics = get_graph_metrics(graph)

    gap_ids = {g.skill.id for g in gaps}

    # Transitive expansion of missing prerequisite ancestors
    expanded_ids: set[str] = set()
    for gap_id in gap_ids:
        if gap_id in graph:
            ancestors = metrics.get_ancestors(gap_id)
            missing_ancestors = ancestors - confirmed_skill_ids
            expanded_ids.update(missing_ancestors)
    expanded_ids.update(gap_ids)

    if not expanded_ids:
        return LearningPath(
            learner_id=learner_id,
            career_id=career_id,
            career_name=career_name,
            total_skills=0,
            total_estimated_hours=0,
            steps=[],
        )

    subgraph = graph.subgraph(expanded_ids)

    # Reconstruct or adapt career & learner if legacy callers didn't pass full models
    if career is None:
        career = Career(
            id=career_id,
            name=career_name,
            required_skills=[
                CareerSkillRequirement(
                    skill_id=g.skill.id,
                    is_mandatory=g.is_mandatory,
                    importance=3,
                )
                for g in gaps
            ],
        )

    if learner is None:
        learner = LearnerProfile(
            id=learner_id,
            confirmed_skills=[ConfirmedSkill(skill_id=sid) for sid in confirmed_skill_ids],
        )

    # 1. Candidate Pathway Generation
    generator = CandidatePathwayGenerator(
        subgraph=subgraph,
        career=career,
        learner=learner,
        all_skills=all_skills,
        metrics=metrics,
    )

    if strategy == "foundational_first":
        candidates = [generator.generate_foundational_first()]
    elif strategy == "career_goal_first":
        candidates = [generator.generate_goal_first()]
    elif strategy == "quick_wins":
        candidates = [generator.generate_quick_wins()]
    elif strategy == "domain_clustered":
        candidates = [generator.generate_domain_clustered()]
    elif strategy == "bounded_beam_search":
        candidates = [generator.generate_beam_search()]
    else:
        candidates = generator.generate_all(beam_width=5, time_budget_ms=20.0)

    # 2. Multi-Objective Scoring
    scorer = MultiObjectivePathScorer(
        career=career,
        learner=learner,
        subgraph=subgraph,
        gaps=gaps,
    )

    scored_candidates: list[ParetoCandidate] = []
    for cand in candidates:
        scores = scorer.score_path(cand.skill_ids)
        scored_candidates.append(
            ParetoCandidate(
                strategy=cand.strategy,
                skill_ids=cand.skill_ids,
                scores=scores,
            )
        )

    # 3. Pareto Frontier Analysis
    pareto_optimizer = ParetoOptimizer()
    frontier = pareto_optimizer.extract_frontier(scored_candidates)

    # 4. Build Enriched Candidate Paths
    built_paths: list[LearningPath] = []
    for cand in scored_candidates:
        steps = populate_step_rationales(
            path_skill_ids=cand.skill_ids,
            graph=graph,
            career=career,
            gaps=gaps,
            metrics=metrics,
        )
        total_hours = sum(s.estimated_hours for s in steps)
        built_paths.append(
            LearningPath(
                learner_id=learner_id,
                career_id=career_id,
                career_name=career_name,
                total_skills=len(steps),
                total_estimated_hours=total_hours,
                steps=steps,
                strategy=cand.strategy,
                objective_scores=cand.scores.to_dict(),
                composite_score=cand.scores.composite_score,
            )
        )

    # 5. Ranking
    active_ranker = ranker or RuleBasedRanker()
    ranked_paths = active_ranker.rank_paths(built_paths, learner)
    recommended = ranked_paths[0]

    # 6. Synthesize Pareto Trade-off Explanations
    rec_pareto = next(
        (c for c in scored_candidates if c.strategy == recommended.strategy),
        scored_candidates[0],
    )
    alt_paretos = [c for c in scored_candidates if c.strategy != recommended.strategy]
    tradeoffs = pareto_optimizer.explain_tradeoffs(rec_pareto, alt_paretos)

    recommended.pareto_tradeoffs = [t.to_dict() for t in tradeoffs]
    if return_alternatives:
        recommended.alternative_paths = [p for p in ranked_paths if p.strategy != recommended.strategy]

    return recommended
