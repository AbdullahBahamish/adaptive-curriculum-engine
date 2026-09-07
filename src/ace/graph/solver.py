"""Graph Solver — generates an ordered learning path from skill gaps.

Uses topological sorting on the prerequisite DAG to produce a valid
learning sequence: skills with no prerequisites come first, and each
skill only appears after all its prerequisites have been satisfied.

This is the core AI-enhanced decision making:
  1. Start from the learner's gap skills.
  2. Expand each gap to include any prerequisite skills the learner
     is also missing (transitive prerequisites).
  3. Run topological sort on the subgraph of gap skills only.
  4. Return an ordered list of LearningStep objects.
"""
import networkx as nx

from ace.domain.learning_path import LearningPath, LearningStep
from ace.domain.skill import Skill, SkillGap
from ace.graph.validator import validate_graph


def generate_learning_path(
    gaps: list[SkillGap],
    graph: nx.DiGraph,
    learner_id: str,
    career_id: str,
    career_name: str,
    confirmed_skill_ids: set[str],
) -> LearningPath:
    """Generate a topologically sorted learning path from skill gaps.

    Args:
        gaps: Skills the learner is missing.
        graph: The full prerequisite DAG (all skills).
        learner_id: Identifier of the learner.
        career_id: Identifier of the target career.
        career_name: Display name of the target career.
        confirmed_skill_ids: Skills the learner already has (excluded from path).

    Returns:
        A LearningPath with ordered LearningStep entries.
    """
    # Validate the graph is a DAG before proceeding
    validate_graph(graph)

    gap_ids = {g.skill.id for g in gaps}

    # Expand gaps to include transitive prerequisites the learner is also missing
    expanded_ids: set[str] = set()
    for gap_id in gap_ids:
        if gap_id in graph:
            ancestors = nx.ancestors(graph, gap_id)
            missing_ancestors = ancestors - confirmed_skill_ids
            expanded_ids.update(missing_ancestors)
    expanded_ids.update(gap_ids)

    # Build a subgraph containing only the skills we need to learn
    subgraph = graph.subgraph(expanded_ids)

    # Topological sort gives us a valid learning order
    ordered_skill_ids = list(nx.topological_sort(subgraph))

    # Build the step-by-step learning path
    gap_skill_map: dict[str, Skill] = {g.skill.id: g.skill for g in gaps}
    steps: list[LearningStep] = []

    for order, skill_id in enumerate(ordered_skill_ids, start=1):
        node_data = graph.nodes.get(skill_id, {})
        prereq_ids = list(graph.predecessors(skill_id))
        # Only list prerequisites that are within the learning path itself
        path_prereqs = [p for p in prereq_ids if p in expanded_ids]

        skill = gap_skill_map.get(skill_id)
        steps.append(
            LearningStep(
                order=order,
                skill_id=skill_id,
                skill_name=node_data.get("name", skill_id),
                category=node_data.get("category", "General"),
                estimated_hours=node_data.get("estimated_hours", 0),
                rationale=_build_rationale(skill_id, path_prereqs, node_data),
                prerequisites_satisfied=path_prereqs,
            )
        )

    total_hours = sum(s.estimated_hours for s in steps)

    return LearningPath(
        learner_id=learner_id,
        career_id=career_id,
        career_name=career_name,
        total_skills=len(steps),
        total_estimated_hours=total_hours,
        steps=steps,
    )


def _build_rationale(skill_id: str, prereqs: list[str], node_data: dict) -> str:
    """Generate a deterministic textual rationale for a learning step."""
    if not prereqs:
        return f"'{node_data.get('name', skill_id)}' has no prerequisites — start here."
    prereq_names = ", ".join(f"'{p}'" for p in prereqs[:3])
    return f"Requires {prereq_names} to be completed first."