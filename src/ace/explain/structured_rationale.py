from __future__ import annotations

from typing import TYPE_CHECKING

import networkx as nx

from ace.domain.career import Career
from ace.domain.learning_path import LearningPath, LearningStep
from ace.domain.skill import SkillGap

if TYPE_CHECKING:
    from ace.graph.graph_metrics import PrerequisiteGraphMetrics



def populate_step_rationales(
    path_skill_ids: list[str],
    graph: nx.DiGraph,
    career: Career,
    gaps: list[SkillGap] | None = None,
    metrics: PrerequisiteGraphMetrics | None = None,
) -> list[LearningStep]:
    """Build enriched LearningStep objects with structured reason codes and metrics."""
    gap_map: dict[str, SkillGap] = {g.skill.id: g for g in (gaps or [])}
    req_map = {r.skill_id: r for r in career.required_skills}
    path_set = set(path_skill_ids)

    steps: list[LearningStep] = []
    prev_difficulty = 1
    prev_category: str | None = None

    for order, skill_id in enumerate(path_skill_ids, start=1):
        node_data = graph.nodes.get(skill_id, {})
        name = node_data.get("name", skill_id)
        cat = node_data.get("category", "General")
        hours = int(node_data.get("estimated_hours", 0))
        diff = int(node_data.get("difficulty", 1))

        # Prerequisites satisfied in this path
        prereqs = [p for p in graph.predecessors(skill_id) if p in path_set]
        unblocks = metrics.get_unblocks_count(skill_id, path_set) if metrics else len(set(graph.successors(skill_id)) & path_set)

        gap = gap_map.get(skill_id)
        gap_score = gap.gap_score if gap else (req_map[skill_id].importance * 1.0 if skill_id in req_map else 1.0)
        diff_step = diff - prev_difficulty

        reason_codes: list[str] = []

        # 1. Dependency codes
        if not prereqs:
            reason_codes.append("NO_PREREQUISITES")
            if order == 1:
                reason_codes.append("FOUNDATION_START")
        else:
            reason_codes.append("PREREQUISITE_CLEARED")

        # 2. Unblocker codes
        if unblocks >= 3:
            reason_codes.append("CRITICAL_UNBLOCKER")
        elif unblocks >= 1:
            reason_codes.append("UNBLOCKS_DOWNSTREAM")

        # 3. Career importance codes
        req = req_map.get(skill_id)
        if req:
            if req.is_mandatory:
                reason_codes.append("CAREER_MANDATORY")
            else:
                reason_codes.append("CAREER_RECOMMENDED")
            if req.importance >= 4:
                reason_codes.append("HIGH_PRIORITY_GOAL")

        # 4. Cognitive load / smoothness
        if abs(diff_step) <= 1:
            reason_codes.append("SMOOTH_STEP")

        # 5. Quick win
        if hours <= 15 and diff <= 2:
            reason_codes.append("QUICK_WIN")

        # 6. Domain continuity
        if prev_category and cat == prev_category:
            reason_codes.append("CATEGORY_CONTINUITY")

        # Deterministic rationale text
        rationale = _build_deterministic_step_rationale(name, prereqs, unblocks, reason_codes)

        steps.append(
            LearningStep(
                order=order,
                skill_id=skill_id,
                skill_name=name,
                category=cat,
                estimated_hours=hours,
                rationale=rationale,
                prerequisites_satisfied=prereqs,
                reason_codes=reason_codes,
                unblocks_count=unblocks,
                gap_score=round(gap_score, 3),
                difficulty_step=diff_step,
            )
        )

        prev_difficulty = diff
        prev_category = cat

    return steps


def _build_deterministic_step_rationale(
    name: str,
    prereqs: list[str],
    unblocks: int,
    reason_codes: list[str],
) -> str:
    parts = []
    if "FOUNDATION_START" in reason_codes:
        parts.append(f"Essential foundation for {name}.")
    elif prereqs:
        prereq_str = ", ".join(f"'{p}'" for p in prereqs[:2])
        parts.append(f"Requires {prereq_str} cleared.")
    else:
        parts.append("Zero remaining prerequisites.")

    if "CRITICAL_UNBLOCKER" in reason_codes:
        parts.append(f"Unblocks {unblocks} downstream skills.")

    if "QUICK_WIN" in reason_codes:
        parts.append("Quick-win building initial momentum.")

    if "CAREER_MANDATORY" in reason_codes:
        parts.append("Mandatory core competency.")

    return " ".join(parts)


def generate_deterministic_explanation(path: LearningPath) -> str:
    """Generate a rich, grounded markdown walkthrough without LLM dependencies."""
    if not path.steps:
        return f"### Curriculum Overview: {path.career_name}\n\nAll prerequisite skills already mastered!"

    total_hours = path.total_estimated_hours
    total_skills = path.total_skills

    lines = [
        f"## Personalized Curriculum Roadmap: {path.career_name}",
        f"**Strategy**: `{path.strategy}` | **Skills**: {total_skills} | **Total Effort**: ~{total_hours} hours",
        "",
    ]

    if path.objective_scores:
        lines.extend([
            "### Pedagogical Quality Profile",
            f"- **Career Goal Alignment**: {path.objective_scores.get('goal_alignment', 0.0) * 100:.1f}%",
            f"- **Difficulty Progression Smoothness**: {path.objective_scores.get('difficulty_smoothness', 0.0) * 100:.1f}%",
            f"- **Category Continuity**: {path.objective_scores.get('category_continuity', 0.0) * 100:.1f}%",
            "",
        ])

    lines.append("### Recommended Learning Sequence")
    for step in path.steps:
        badges = " ".join(f"`[{code}]`" for code in step.reason_codes[:3])
        lines.append(
            f"{step.order}. **{step.skill_name}** ({step.category}, ~{step.estimated_hours}h) {badges}\n"
            f"   - *Rationale*: {step.rationale}"
        )

    if path.pareto_tradeoffs:
        lines.extend(["", "### Alternative Pathways Considered"])
        for alt in path.pareto_tradeoffs:
            if not alt.get("is_recommended", False):
                strat = alt.get("strategy", "Alternative")
                tradeoffs = "; ".join(alt.get("tradeoffs_vs_primary", []))
                lines.append(f"- **{strat}**: {tradeoffs}")

    return "\n".join(lines)
