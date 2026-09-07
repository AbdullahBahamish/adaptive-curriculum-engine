"""Curriculum explainer service powered by LLM or deterministic heuristics."""
from ace.domain.learning_path import LearningPath
from ace.infrastructure.llm.client import LLMProvider, get_llm_provider


class CurriculumExplainer:
    """Generates natural language narrative explaining a learner's personalized curriculum."""

    def __init__(self, provider: LLMProvider | None = None):
        self.provider = provider or get_llm_provider()

    def explain_path(self, path: LearningPath) -> str:
        """Generate a personalized curriculum walkthrough."""
        if not path.steps:
            return (
                f"Congratulations! You have already acquired all prerequisite skills "
                f"for the {path.career_name} career profile."
            )

        step_summaries = [
            f"Step {s.order}: {s.skill_name} ({s.category}, ~{s.estimated_hours}h) - {s.rationale}"
            for s in path.steps[:10]  # First 10 steps to keep prompt concise
        ]
        steps_text = "\n".join(step_summaries)

        system_prompt = (
            "You are an expert academic advisor and senior software engineering mentor. "
            "Explain to the student why their personalized curriculum roadmap is structured "
            "the way it is. Be encouraging, precise, and emphasize the prerequisite foundation."
        )

        user_prompt = (
            f"Student Career Goal: {path.career_name}\n"
            f"Total Skills in Roadmap: {path.total_skills}\n"
            f"Total Estimated Hours: {path.total_estimated_hours} hours\n\n"
            f"Key Learning Steps (Topologically Sequenced):\n{steps_text}\n\n"
            f"Provide a concise, 2-3 paragraph breakdown explaining:\n"
            f"1. Why starting with the foundational steps prepares them for success.\n"
            f"2. How subsequent skills build on earlier prerequisites.\n"
            f"3. Practical advice for executing this study plan."
        )

        return self.provider.complete(prompt=user_prompt, system_prompt=system_prompt)
