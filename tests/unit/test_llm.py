"""Unit tests for optional LLM components (mock provider, explainer, and matcher)."""
from ace.domain.learning_path import LearningPath, LearningStep
from ace.domain.skill import Skill
from ace.infrastructure.llm.client import MockLLMProvider, get_llm_provider
from ace.infrastructure.llm.explainer import CurriculumExplainer
from ace.infrastructure.llm.skill_matcher import SkillMatcher


def test_mock_llm_provider():
    provider = MockLLMProvider()
    response = provider.complete("Test prompt")
    assert isinstance(response, str)
    assert len(response) > 0


def test_curriculum_explainer_with_mock():
    explainer = CurriculumExplainer(provider=MockLLMProvider())
    path = LearningPath(
        learner_id="test-1",
        career_id="frontend_dev",
        career_name="Frontend Developer",
        total_skills=2,
        total_estimated_hours=35,
        steps=[
            LearningStep(
                order=1,
                skill_id="html5",
                skill_name="HTML5",
                category="frontend",
                estimated_hours=15,
                rationale="Start here",
                prerequisites_satisfied=[],
            ),
            LearningStep(
                order=2,
                skill_id="css3",
                skill_name="CSS3",
                category="frontend",
                estimated_hours=20,
                rationale="Requires HTML5",
                prerequisites_satisfied=["html5"],
            ),
        ],
    )
    explanation = explainer.explain_path(path)
    assert isinstance(explanation, str)
    assert len(explanation) > 10


def test_skill_matcher_heuristic():
    matcher = SkillMatcher(provider=MockLLMProvider())
    skills = [
        Skill(id="python_basics", name="Python Basics", category="backend"),
        Skill(id="react_basics", name="React Basics", category="frontend"),
        Skill(id="docker", name="Docker Containerization", category="cloud_devops"),
    ]

    matched = matcher.match_skills("I have extensive background in Python and Docker deployments", skills)
    assert "python_basics" in matched
    assert "docker" in matched
    assert "react_basics" not in matched
