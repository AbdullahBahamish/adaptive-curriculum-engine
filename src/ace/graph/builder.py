"""Graph builder — constructs a NetworkX DAG from skills and prerequisites.

The prerequisite graph is a Directed Acyclic Graph (DAG) where:
  - Each node is a Skill (identified by skill_id)
  - Each directed edge (A -> B) means: "A must be learned before B"
"""
import networkx as nx

from ace.domain.prerequisite import Prerequisite
from ace.domain.skill import Skill


def build_prerequisite_graph(
    skills: list[Skill],
    prerequisites: list[Prerequisite],
) -> nx.DiGraph:
    """Build and return the prerequisite DAG.

    Args:
        skills: All skills to include as nodes.
        prerequisites: All prerequisite edges.

    Returns:
        A directed graph where an edge (A -> B) means A must come before B.
    """
    graph = nx.DiGraph()

    # Add all skill nodes with metadata
    for skill in skills:
        graph.add_node(
            skill.id,
            name=skill.name,
            category=skill.category,
            difficulty=skill.difficulty,
            estimated_hours=skill.estimated_hours,
        )

    # Add directed edges: requires_skill_id -> skill_id
    # (prereq must come BEFORE the skill)
    for prereq in prerequisites:
        if prereq.skill_id in graph and prereq.requires_skill_id in graph:
            graph.add_edge(prereq.requires_skill_id, prereq.skill_id)

    return graph