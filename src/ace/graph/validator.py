"""Graph validator — detects cycles and structural problems in the prerequisite graph.

A valid prerequisite graph must be a DAG (no cycles). A cycle such as
A requires B and B requires A makes it impossible to generate a learning order.
"""
import networkx as nx

from ace.core.exceptions import CycleDetectedError, DisconnectedGraphError


def validate_graph(graph: nx.DiGraph) -> None:
    """Validate that the graph is a valid DAG.

    Raises:
        CycleDetectedError: If one or more cycles are detected.
        DisconnectedGraphError: If the graph has structural issues.
    """
    if not nx.is_directed_acyclic_graph(graph):
        # Find and report all cycles for debugging
        cycles = list(nx.simple_cycles(graph))
        if cycles:
            # Report the first cycle found
            raise CycleDetectedError(cycle=cycles[0])
        raise DisconnectedGraphError("Graph is not a DAG but no simple cycles found.")


def find_all_cycles(graph: nx.DiGraph) -> list[list[str]]:
    """Return all cycles in the graph (for admin debugging/reporting)."""
    return list(nx.simple_cycles(graph))
