"""Gap Analyzer — computes the skill gap between a learner and a career.

Gap analysis logic (binary model):
  - A skill is a GAP if:
      (a) it is required by the career, AND
      (b) the learner has NOT confirmed they have it.
  - Skills the learner already has are excluded from the learning path.
"""
import networkx as nx

from ace.domain.career import Career
from ace.domain.learner import LearnerProfile
from ace.domain.skill import GapStatus, Skill, SkillGap
from ace.graph.graph_metrics import get_graph_metrics


def compute_skill_gaps(
    career: Career,
    learner: LearnerProfile,
    all_skills: dict[str, Skill],
    graph: nx.DiGraph | None = None,
) -> list[SkillGap]:
    """Return the ordered list of skills the learner still needs with multi-factor gap scores.

    Formula:
        gap(s) = importance(s) * target_relevance(s) * (1 - mastery(s)) * prerequisite_impact(s)

    Args:
        career: The selected target career with required skills.
        learner: The learner profile with confirmed skills and mastery states.
        all_skills: Mapping of skill_id -> Skill for lookup.
        graph: Optional prerequisite DAG for structural impact and blocking analysis.

    Returns:
        List of SkillGap objects sorted by gap priority score descending.
    """
    confirmed_ids = learner.confirmed_skill_ids
    metrics = get_graph_metrics(graph) if graph is not None else None
    gaps: list[SkillGap] = []

    for req in career.required_skills:
        mastery = learner.get_mastery(req.skill_id)

        # Exclude skills already confirmed or strongly mastered (>= 0.8)
        if req.skill_id in confirmed_ids or mastery >= 0.8:
            continue

        skill = all_skills.get(req.skill_id)
        if skill is None:
            continue  # Unknown skill — skip gracefully

        importance = float(req.importance)
        target_relevance = 1.0 if req.is_mandatory else 0.8
        prereq_impact = metrics.get_impact(req.skill_id) if metrics is not None else 1.0

        gap_score = round(importance * target_relevance * (1.0 - mastery) * prereq_impact, 3)

        # Determine blocking and reason codes
        reason_codes: list[str] = []
        if req.is_mandatory:
            reason_codes.append("CAREER_MANDATORY")
        else:
            reason_codes.append("CAREER_RECOMMENDED")

        unfulfilled_prereqs: set[str] = set()
        if graph is not None and req.skill_id in graph:
            preds = set(graph.predecessors(req.skill_id))
            unfulfilled_prereqs = preds - confirmed_ids
            if not preds:
                reason_codes.append("NO_PREREQUISITES")
            elif not unfulfilled_prereqs:
                reason_codes.append("PREREQUISITE_CLEARED")
            else:
                reason_codes.append("BLOCKED_BY_PREREQUISITE")
            if prereq_impact > 1.8:
                reason_codes.append("CRITICAL_UNBLOCKER")
        else:
            reason_codes.append("READY_TO_LEARN")

        if mastery >= 0.5:
            reason_codes.append("HIGH_STARTING_MASTERY")
        elif mastery > 0.0:
            reason_codes.append("PARTIAL_MASTERY")

        # 6-tier status classification
        if unfulfilled_prereqs:
            status = GapStatus.BLOCKED_BY_PREREQUISITE
        elif mastery >= 0.5:
            status = GapStatus.ADEQUATELY_MASTERED
        elif mastery >= 0.2:
            status = GapStatus.WEAKLY_MASTERED
        elif unfulfilled_prereqs:
            status = GapStatus.MISSING
        else:
            status = GapStatus.READY_TO_LEARN

        gaps.append(
            SkillGap(
                skill=skill,
                is_missing=True,
                mastery=mastery,
                status=status,
                gap_score=gap_score,
                reason_codes=reason_codes,
                prerequisite_impact=prereq_impact,
                target_relevance=target_relevance,
                is_mandatory=req.is_mandatory,
            )
        )

    # Sort: mandatory first, then by gap_score descending, then alphabetically for stability
    def sort_key(gap: SkillGap) -> tuple[int, float, str]:
        return (0 if gap.is_mandatory else 1, -gap.gap_score, gap.skill.id)

    gaps.sort(key=sort_key)
    return gaps