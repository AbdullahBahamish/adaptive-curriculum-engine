"""Curriculum explainer service powered by LLM or deterministic heuristics."""
from ace.domain.learning_path import LearningPath
from ace.explain.structured_rationale import generate_deterministic_explanation
from ace.infrastructure.llm.client import LLMProvider, MockLLMProvider, get_llm_provider


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

        # If Mock provider or LLM disabled, use deterministic explanation
        if isinstance(self.provider, MockLLMProvider):
            return generate_deterministic_explanation(path)

        step_summaries = []
        for s in path.steps[:10]:
            badges = ", ".join(s.reason_codes[:3])
            step_summaries.append(
                f"Step {s.order}: {s.skill_name} ({s.category}, ~{s.estimated_hours}h) "
                f"[Unblocks: {s.unblocks_count}, Reasons: {badges}] - {s.rationale}"
            )
        steps_text = "\n".join(step_summaries)

        tradeoffs_text = ""
        if path.pareto_tradeoffs:
            tradeoffs_text = "\n\nPareto Alternatives Evaluated:\n" + "\n".join(
                f"- {alt.get('strategy')}: {'; '.join(alt.get('tradeoffs_vs_primary', []))}"
                for alt in path.pareto_tradeoffs if not alt.get("is_recommended", False)
            )

        system_prompt = (
            "You are an expert academic advisor and senior software engineering mentor. "
            "Explain to the student why their personalized curriculum roadmap is structured "
            "the way it is. Ground your explanation strictly on the provided factual prerequisites, "
            "unblocking steps, and reason codes. DO NOT invent false prerequisites."
        )

        user_prompt = (
            f"Student Career Goal: {path.career_name}\n"
            f"Strategy Archetype: {path.strategy}\n"
            f"Total Skills in Roadmap: {path.total_skills}\n"
            f"Total Estimated Hours: {path.total_estimated_hours} hours\n\n"
            f"Factual Topologically Sequenced Steps:\n{steps_text}{tradeoffs_text}\n\n"
            f"Provide a concise, 2-3 paragraph breakdown explaining:\n"
            f"1. Why starting with the foundational steps prepares them for success.\n"
            f"2. How subsequent skills build on earlier prerequisites.\n"
            f"3. Practical advice for executing this study plan."
        )

        try:
            return self.provider.complete(prompt=user_prompt, system_prompt=system_prompt)
        except Exception:
            return generate_deterministic_explanation(path)

    def explain_path_deterministic(self, path: LearningPath) -> str:
        """Directly produce the deterministic structured explanation."""
        return generate_deterministic_explanation(path)

