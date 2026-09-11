"""Property-based invariant tests verifying 0 prerequisite violations across all generated paths."""
import json
import random
import networkx as nx
import pytest

from ace.domain.career import Career, CareerSkillRequirement
from ace.domain.learner import ConfirmedSkill, LearnerProfile, LearningPreferences, PacePreference, SkillMasteryState
from ace.domain.prerequisite import Prerequisite
from ace.domain.skill import Skill
from ace.graph.builder import build_prerequisite_graph
from ace.graph.gap_analyzer import compute_skill_gaps
from ace.graph.solver import generate_learning_path


@pytest.fixture(scope="module")
def real_seed_graph():
    with open("data/seed/skills.json", "r", encoding="utf-8") as f:
        skills_raw = json.load(f)
    with open("data/seed/careers.json", "r", encoding="utf-8") as f:
        careers_raw = json.load(f)
    with open("data/seed/prerequisites.json", "r", encoding="utf-8") as f:
        prereqs_raw = json.load(f)

    skills = [Skill(**s) for s in skills_raw]
    prereqs = [Prerequisite(**p) for p in prereqs_raw]
    graph = build_prerequisite_graph(skills, prereqs)
    careers = [
        Career(
            id=c["id"],
            name=c["name"],
            required_skills=[CareerSkillRequirement(**r) for r in c["required_skills"]],
        )
        for c in careers_raw
    ]
    return graph, {s.id: s for s in skills}, careers


@pytest.mark.unit
def test_strict_dag_topological_invariants_across_cohort(real_seed_graph):
    """Generate 50 random learner profiles and assert 0 prerequisite violations on all paths."""
    graph, skill_map, careers = real_seed_graph
    all_skill_ids = list(skill_map.keys())

    random.seed(42)
    paces = [PacePreference.BALANCED, PacePreference.FOUNDATIONAL_FIRST, PacePreference.FAST_TRACK, PacePreference.DOMAIN_FOCUSED]

    total_paths_verified = 0
    total_prereq_violations = 0

    for i in range(50):
        target_career = random.choice(careers)
        # Randomly confirm between 0 and 25 skills
        n_confirmed = random.randint(0, 25)
        confirmed_ids = set(random.sample(all_skill_ids, n_confirmed))

        # Random mastery states
        masteries = {}
        for sid in list(confirmed_ids)[:10]:
            masteries[sid] = SkillMasteryState(
                skill_id=sid,
                estimated_mastery=random.uniform(0.5, 1.0),
                confidence=random.uniform(0.6, 0.95),
            )

        learner = LearnerProfile(
            id=f"rand_learner_{i+1}",
            confirmed_skills=[ConfirmedSkill(skill_id=sid) for sid in confirmed_ids],
            mastery_states=masteries,
            preferences=LearningPreferences(
                weekly_hours_budget=random.randint(5, 30),
                pace_preference=random.choice(paces),
            ),
        )

        gaps = compute_skill_gaps(target_career, learner, skill_map, graph=graph)
        path = generate_learning_path(
            gaps=gaps,
            graph=graph,
            learner_id=learner.id,
            career_id=target_career.id,
            career_name=target_career.name,
            confirmed_skill_ids=learner.confirmed_skill_ids,
            career=target_career,
            learner=learner,
            all_skills=skill_map,
            return_alternatives=True,
        )

        all_tested_paths = [path] + path.alternative_paths
        for p in all_tested_paths:
            total_paths_verified += 1
            pos = {s.skill_id: idx for idx, s in enumerate(p.steps)}

            # Assert for every edge in the graph where both skills are in the path:
            for u, v in graph.edges:
                if u in pos and v in pos:
                    if pos[u] >= pos[v]:
                        total_prereq_violations += 1
                        pytest.fail(f"Prerequisite violation: {u} (pos {pos[u]}) appears after {v} (pos {pos[v]}) in strategy {p.strategy}")

            # Verify total hours calculation
            assert p.total_estimated_hours == sum(s.estimated_hours for s in p.steps)

    assert total_prereq_violations == 0
    assert total_paths_verified >= 100
