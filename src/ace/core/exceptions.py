"""Domain and application exceptions for the ACE AI Engine."""


class AceError(Exception):
    """Base exception for all ACE AI Engine errors."""


# Graph / prerequisite errors

class CycleDetectedError(AceError):
    """Raised when a cycle is found in the prerequisite graph."""

    def __init__(self, cycle: list[str]) -> None:
        self.cycle = cycle
        cycle_str = " -> ".join(cycle)
        super().__init__(f"Prerequisite cycle detected: {cycle_str}")


class DisconnectedGraphError(AceError):
    """Raised when required skill nodes reference skills not in the graph."""


# Domain entity errors

class SkillNotFoundError(AceError):
    """Raised when a skill ID cannot be found in the database."""

    def __init__(self, skill_id: str) -> None:
        self.skill_id = skill_id
        super().__init__(f"Skill not found: '{skill_id}'")


class CareerNotFoundError(AceError):
    """Raised when a career ID cannot be found in the database."""

    def __init__(self, career_id: str) -> None:
        self.career_id = career_id
        super().__init__(f"Career not found: '{career_id}'")


class LearnerNotFoundError(AceError):
    """Raised when a learner ID cannot be found in the database."""

    def __init__(self, learner_id: str) -> None:
        self.learner_id = learner_id
        super().__init__(f"Learner not found: '{learner_id}'")


# Service / infrastructure errors

class LLMUnavailableError(AceError):
    """Raised when the LLM provider is disabled or unreachable."""


class EmbeddingError(AceError):
    """Raised when embedding generation fails."""


class DatabaseError(AceError):
    """Raised on unrecoverable database errors."""
