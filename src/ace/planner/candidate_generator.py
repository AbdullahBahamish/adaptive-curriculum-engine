"""Candidate Pathway Generator.

Generates diverse, pedagogical, 100% valid topological learning paths:
1. Foundational-First: Prioritizes prerequisite depth and solid conceptual fundamentals
2. Career-Goal-First: Prioritizes immediate scheduling of high-importance career skills
3. Quick-Wins: Prioritizes low estimated hours and beginner difficulty for early momentum
4. Domain-Clustered: Minimizes cognitive context-switching across different domains
5. Bounded Beam Search: Priority-guided combinatorial exploration of topological sequence space

Every generated path satisfies the strict DAG invariant:
    forall (u, v) in E, index(u) < index(v)
Prerequisite violation rate is strictly 0.00%.
"""
import time
from dataclasses import dataclass
from typing import Any

import networkx as nx

from ace.domain.career import Career
from ace.domain.learner import LearnerProfile
from ace.domain.skill import Skill
from ace.graph.graph_metrics import PrerequisiteGraphMetrics, get_graph_metrics


@dataclass
class CandidatePath:
    """A generated candidate sequence of skill IDs with generator metadata."""
    strategy: str
    skill_ids: list[str]
    generation_time_ms: float


class CandidatePathwayGenerator:
    """Generates multiple diverse topological candidate sequences for an induced skill subgraph."""

    def __init__(
        self,
        subgraph: nx.DiGraph,
        career: Career,
        learner: LearnerProfile,
        all_skills: dict[str, Skill] | None = None,
        metrics: PrerequisiteGraphMetrics | None = None,
    ) -> None:
        self.subgraph = subgraph
        self.career = career
        self.learner = learner
        self.all_skills = all_skills or {}
        self.metrics = metrics or get_graph_metrics(subgraph)

        # Precompute lookups for fast priority sorting
        self._importance_map = {
            r.skill_id: r.importance for r in career.required_skills
        }
        self._mandatory_map = {
            r.skill_id: (1.0 if r.is_mandatory else 0.8) for r in career.required_skills
        }

    def _verify_topological_invariant(self, path: list[str]) -> bool:
        """Assert that every edge (u -> v) in subgraph satisfies index(u) < index(v)."""
        pos = {sid: idx for idx, sid in enumerate(path)}
        for u, v in self.subgraph.edges:
            if u in pos and v in pos:
                if pos[u] >= pos[v]:
                    return False
        return True

    def generate_all(self, beam_width: int = 5, time_budget_ms: float = 20.0) -> list[CandidatePath]:
        """Generate all distinct candidate pathways."""
        candidates: list[CandidatePath] = []
        strategies = [
            self.generate_foundational_first,
            self.generate_goal_first,
            self.generate_quick_wins,
            self.generate_domain_clustered,
            lambda: self.generate_beam_search(beam_width=beam_width, time_budget_ms=time_budget_ms),
        ]

        seen_paths: set[tuple[str, ...]] = set()
        for fn in strategies:
            cand = fn()
            tpl = tuple(cand.skill_ids)
            if tpl not in seen_paths and len(cand.skill_ids) == len(self.subgraph.nodes):
                seen_paths.add(tpl)
                candidates.append(cand)

        # Fallback to standard topological sort if none generated
        if not candidates:
            t0 = time.perf_counter()
            std = list(nx.topological_sort(self.subgraph))
            candidates.append(
                CandidatePath(
                    strategy="topological_fallback",
                    skill_ids=std,
                    generation_time_ms=(time.perf_counter() - t0) * 1000,
                )
            )

        return candidates

    def generate_foundational_first(self) -> CandidatePath:
        """Prioritizes lowest prerequisite depth, low difficulty, and high unblocking impact."""
        t0 = time.perf_counter()

        def key_fn(u: str) -> tuple[int, int, float, str]:
            node_data = self.subgraph.nodes.get(u, {})
            diff = int(node_data.get("difficulty", 1))
            depth = self.metrics.get_depth(u)
            unblocks = self.metrics.get_unblocks_count(u)
            return (depth, diff, -unblocks, u)

        path = self._topological_priority_traversal(key_fn)
        elapsed = (time.perf_counter() - t0) * 1000
        assert self._verify_topological_invariant(path), "Foundational-first violated DAG invariant"
        return CandidatePath(strategy="foundational_first", skill_ids=path, generation_time_ms=elapsed)

    def generate_goal_first(self) -> CandidatePath:
        """Prioritizes highest career importance and target relevance first."""
        t0 = time.perf_counter()

        def key_fn(u: str) -> tuple[int, float, int, str]:
            importance = self._importance_map.get(u, 1)
            relevance = self._mandatory_map.get(u, 0.5)
            depth = self.metrics.get_depth(u)
            return (-importance, -relevance, depth, u)

        path = self._topological_priority_traversal(key_fn)
        elapsed = (time.perf_counter() - t0) * 1000
        assert self._verify_topological_invariant(path), "Goal-first violated DAG invariant"
        return CandidatePath(strategy="career_goal_first", skill_ids=path, generation_time_ms=elapsed)

    def generate_quick_wins(self) -> CandidatePath:
        """Prioritizes low estimated hours and beginner difficulty."""
        t0 = time.perf_counter()

        def key_fn(u: str) -> tuple[int, int, int, str]:
            node_data = self.subgraph.nodes.get(u, {})
            hours = int(node_data.get("estimated_hours", 0))
            diff = int(node_data.get("difficulty", 1))
            importance = self._importance_map.get(u, 1)
            return (hours, diff, -importance, u)

        path = self._topological_priority_traversal(key_fn)
        elapsed = (time.perf_counter() - t0) * 1000
        assert self._verify_topological_invariant(path), "Quick-wins violated DAG invariant"
        return CandidatePath(strategy="quick_wins", skill_ids=path, generation_time_ms=elapsed)

    def generate_domain_clustered(self) -> CandidatePath:
        """Minimizes domain switching by clustering consecutive categories."""
        t0 = time.perf_counter()
        in_degree = {u: self.subgraph.in_degree(u) for u in self.subgraph.nodes}
        ready: list[str] = [u for u in self.subgraph.nodes if in_degree[u] == 0]
        path: list[str] = []
        current_category: str | None = None

        while ready:
            # Sort ready items preferring matching category
            def sort_key(u: str) -> tuple[int, int, int, str]:
                node_data = self.subgraph.nodes.get(u, {})
                cat = node_data.get("category", "")
                cat_match = 0 if current_category and cat == current_category else 1
                depth = self.metrics.get_depth(u)
                diff = int(node_data.get("difficulty", 1))
                return (cat_match, depth, diff, u)

            ready.sort(key=sort_key)
            u = ready.pop(0)
            path.append(u)
            current_category = self.subgraph.nodes.get(u, {}).get("category", current_category)

            for v in self.subgraph.successors(u):
                in_degree[v] -= 1
                if in_degree[v] == 0:
                    ready.append(v)

        elapsed = (time.perf_counter() - t0) * 1000
        assert self._verify_topological_invariant(path), "Domain-clustered violated DAG invariant"
        return CandidatePath(strategy="domain_clustered", skill_ids=path, generation_time_ms=elapsed)

    def generate_beam_search(self, beam_width: int = 5, time_budget_ms: float = 20.0) -> CandidatePath:
        """Explores topological space with bounded beam search."""
        t0 = time.perf_counter()
        deadline = t0 + (time_budget_ms / 1000.0)
        n_nodes = len(self.subgraph.nodes)

        initial_in_degree = {u: self.subgraph.in_degree(u) for u in self.subgraph.nodes}
        initial_ready = frozenset(u for u in self.subgraph.nodes if initial_in_degree[u] == 0)

        # Beam item: (score, path_tuple, in_degrees_dict_frozen, ready_set_frozen)
        beam: list[tuple[float, tuple[str, ...], dict[str, int], frozenset[str]]] = [
            (0.0, (), dict(initial_in_degree), initial_ready)
        ]

        for step in range(n_nodes):
            if time.perf_counter() > deadline:
                break

            candidates_pool: list[tuple[float, tuple[str, ...], dict[str, int], frozenset[str]]] = []

            for cum_score, cur_path, in_deg, ready_set in beam:
                for cand in ready_set:
                    node_data = self.subgraph.nodes.get(cand, {})
                    importance = self._importance_map.get(cand, 1)
                    diff = int(node_data.get("difficulty", 1))

                    # Immediate step reward: high importance discounted, smooth transition
                    prev_diff = int(self.subgraph.nodes.get(cur_path[-1], {}).get("difficulty", 1)) if cur_path else diff
                    step_reward = (importance * 2.0) - (abs(diff - prev_diff) * 0.5)

                    new_path = cur_path + (cand,)
                    new_in_deg = dict(in_deg)
                    new_ready = set(ready_set)
                    new_ready.remove(cand)

                    for v in self.subgraph.successors(cand):
                        new_in_deg[v] -= 1
                        if new_in_deg[v] == 0:
                            new_ready.add(v)

                    candidates_pool.append((cum_score + step_reward, new_path, new_in_deg, frozenset(new_ready)))

            if not candidates_pool:
                break

            # Retain top B partial sequences
            candidates_pool.sort(key=lambda x: -x[0])
            beam = candidates_pool[:beam_width]

        # Pick best complete or most completed path
        beam.sort(key=lambda x: (len(x[1]) == n_nodes, x[0]), reverse=True)
        best_path = list(beam[0][1])

        # If incomplete due to deadline, complete greedily
        if len(best_path) < n_nodes:
            remaining = set(self.subgraph.nodes) - set(best_path)
            sub_rem = self.subgraph.subgraph(remaining)
            best_path.extend(list(nx.topological_sort(sub_rem)))

        elapsed = (time.perf_counter() - t0) * 1000
        assert self._verify_topological_invariant(best_path), "Beam search violated DAG invariant"
        return CandidatePath(strategy="bounded_beam_search", skill_ids=best_path, generation_time_ms=elapsed)

    def _topological_priority_traversal(self, key_fn: Any) -> list[str]:
        """Generic priority-guided Kahn's topological sort."""
        in_degree = {u: self.subgraph.in_degree(u) for u in self.subgraph.nodes}
        ready = [u for u in self.subgraph.nodes if in_degree[u] == 0]
        path: list[str] = []

        while ready:
            ready.sort(key=key_fn)
            u = ready.pop(0)
            path.append(u)
            for v in self.subgraph.successors(u):
                in_degree[v] -= 1
                if in_degree[v] == 0:
                    ready.append(v)

        return path
