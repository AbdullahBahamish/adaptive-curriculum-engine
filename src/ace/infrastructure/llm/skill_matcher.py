"""Semantic skill matching between natural language input and standardized skill IDs."""
import json
import re
from collections.abc import Sequence

from ace.domain.skill import Skill
from ace.infrastructure.llm.client import LLMProvider, MockLLMProvider, get_llm_provider
from ace.semantic.vector_index import SkillVectorIndex


class SkillMatcher:
    """Matches free-form text skill descriptions to curriculum skill IDs."""

    def __init__(
        self,
        provider: LLMProvider | None = None,
        vector_index: SkillVectorIndex | None = None,
    ):
        self.provider = provider or get_llm_provider()
        self.vector_index = vector_index

    def match_skills(self, text: str, available_skills: Sequence[Skill]) -> list[str]:
        """Return list of skill IDs that the text indicates the user possesses."""
        if not text.strip() or not available_skills:
            return []

        available_ids = {s.id for s in available_skills}

        # If vector index is available, leverage semantic vector search
        if self.vector_index is not None and self.vector_index.is_indexed:
            semantic_matches = self.vector_index.search(text, top_k=10, min_score=0.42)
            vector_ids = [sid for sid, _ in semantic_matches if sid in available_ids]
            # Also combine with heuristic to ensure high precision on exact keyword mentions
            heuristic_ids = self._heuristic_match(text, available_skills)
            return list(dict.fromkeys(heuristic_ids + vector_ids))

        # If Mock provider or LLM disabled, use keyword token matching
        if isinstance(self.provider, MockLLMProvider):
            return self._heuristic_match(text, available_skills)

        return self._llm_match(text, available_skills)


    def _heuristic_match(self, text: str, available_skills: Sequence[Skill]) -> list[str]:
        """Fast keyword/regex heuristic matcher."""
        lowered = text.lower()
        matched_ids = []
        for skill in available_skills:
            # Check ID tokens and name tokens
            name_lowered = skill.name.lower()
            id_tokens = skill.id.lower().split("_")

            if skill.id.lower() in lowered or name_lowered in lowered:
                matched_ids.append(skill.id)
            elif any(len(token) > 3 and token in lowered for token in id_tokens):
                # If specific technical token matches (e.g. 'docker', 'react', 'kubernetes')
                matched_ids.append(skill.id)

        return list(dict.fromkeys(matched_ids))

    def _llm_match(self, text: str, available_skills: Sequence[Skill]) -> list[str]:
        """LLM-assisted semantic matcher."""
        skill_catalog = [{"id": s.id, "name": s.name} for s in available_skills]

        system_prompt = (
            "You are a technical skills classifier. "
            "Given a candidate's description of their technical background, identify all "
            "matching skill IDs from the provided catalog. Output ONLY a valid JSON array of matching skill ID strings."
        )
        user_prompt = (
            f"Available Catalog:\n{json.dumps(skill_catalog, indent=1)}\n\n"
            f"Candidate Description:\n\"{text}\"\n\n"
            f"Return JSON array of matching IDs, e.g. [\"python_basics\", \"html5\"]:"
        )

        try:
            raw = self.provider.complete(prompt=user_prompt, system_prompt=system_prompt)
            # Extract JSON array from possible markdown block
            match = re.search(r"\[.*?\]", raw, re.DOTALL)
            if match:
                parsed = json.loads(match.group(0))
                if isinstance(parsed, list):
                    catalog_ids = {s.id for s in available_skills}
                    return [str(s) for s in parsed if str(s) in catalog_ids]
        except Exception:
            pass

        return self._heuristic_match(text, available_skills)
