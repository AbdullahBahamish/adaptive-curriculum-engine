"""Graph engine package.

Exposes:
  - build_prerequisite_graph: builds the NetworkX DAG
  - validate_graph: checks for cycles
  - compute_skill_gaps: binary gap analysis
  - generate_learning_path: topologically sorted path generation
"""
from ace.graph.builder import build_prerequisite_graph
from ace.graph.gap_analyzer import compute_skill_gaps
from ace.graph.solver import generate_learning_path
from ace.graph.validator import validate_graph

__all__ = [
    "build_prerequisite_graph",
    "validate_graph",
    "compute_skill_gaps",
    "generate_learning_path",
]