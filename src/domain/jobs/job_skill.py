from dataclasses import dataclass

@dataclass
class JobSkill:
    job_id: int
    skill_id: int
    relevance_score: float
    source: str