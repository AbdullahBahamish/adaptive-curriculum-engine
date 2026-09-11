"""Explainability package — structured reason codes and deterministic explanations."""
from ace.explain.structured_rationale import (
    generate_deterministic_explanation,
    populate_step_rationales,
)

__all__ = [
    "populate_step_rationales",
    "generate_deterministic_explanation",
]
