"""Prerequisite graph metrics — depth, centrality, closures, and unblocking power.

Provides memoized and vectorized graph measurements over NetworkX prerequisite DAGs.
All calculations satisfy strict DAG invariants.
"""
import math

import networkx as nx


class PrerequisiteGraphMetrics:
    """Precomputes and caches structural metrics for a prerequisite DAG."""

    def __init__(self, graph: nx.DiGraph) -> None:
        self.graph = graph
        self._ancestors_cache: dict[str, set[str]] = {}
        self._descendants_cache: dict[str, set[str]] = {}
        self._depth_cache: dict[str, int] = {}
        self._impact_cache: dict[str, float] = {}
        self._precompute()

    def _precompute(self) -> None:
        """Precompute closures, depth, and impact for all nodes in topological order."""
        if not nx.is_directed_acyclic_graph(self.graph):
            return

        # Memoize ancestors and descendants
        for node in self.graph.nodes:
            self._ancestors_cache[node] = nx.ancestors(self.graph, node)
            self._descendants_cache[node] = nx.descendants(self.graph, node)

        # Depth in topological order: depth(v) = 0 if no predecessors else 1 + max(depth(u))
        for node in nx.topological_sort(self.graph):
            preds = list(self.graph.predecessors(node))
            if not preds:
                self._depth_cache[node] = 0
            else:
                self._depth_cache[node] = 1 + max(self._depth_cache.get(p, 0) for p in preds)

        # Prerequisite impact: 1.0 + ln(1 + |Descendants(node)|)
        for node in self.graph.nodes:
            desc_count = len(self._descendants_cache[node])
            self._impact_cache[node] = round(1.0 + math.log(1.0 + desc_count), 4)

    def get_ancestors(self, node: str) -> set[str]:
        """Return transitive ancestors (prerequisites) of node."""
        if node in self._ancestors_cache:
            return self._ancestors_cache[node]
        if node in self.graph:
            res = nx.ancestors(self.graph, node)
            self._ancestors_cache[node] = res
            return res
        return set()

    def get_descendants(self, node: str) -> set[str]:
        """Return transitive descendants (dependents) of node."""
        if node in self._descendants_cache:
            return self._descendants_cache[node]
        if node in self.graph:
            res = nx.descendants(self.graph, node)
            self._descendants_cache[node] = res
            return res
        return set()

    def get_depth(self, node: str) -> int:
        """Return prerequisite depth (longest prerequisite chain)."""
        return self._depth_cache.get(node, 0)

    def get_impact(self, node: str) -> float:
        """Return prerequisite centrality / impact score: 1 + ln(1 + |Descendants|)."""
        return self._impact_cache.get(node, 1.0)

    def get_unblocks_count(self, node: str, target_subgraph: set[str] | None = None) -> int:
        """Return number of downstream skills unblocked (optionally filtered by a target set)."""
        desc = self.get_descendants(node)
        if target_subgraph is not None:
            return len(desc & target_subgraph)
        return len(desc)


_METRICS_CACHE: dict[int, PrerequisiteGraphMetrics] = {}


def get_graph_metrics(graph: nx.DiGraph) -> PrerequisiteGraphMetrics:
    """Retrieve or compute PrerequisiteGraphMetrics for a graph."""
    key = id(graph)
    if key not in _METRICS_CACHE:
        _METRICS_CACHE[key] = PrerequisiteGraphMetrics(graph)
    return _METRICS_CACHE[key]
