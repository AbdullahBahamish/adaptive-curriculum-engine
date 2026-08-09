from dataclasses import dataclass
from typing import Optional

@dataclass
class Skill:
    skill_id: int
    skill_name: str
    skill_category: str
    skill_difficulty: int
    skill_description: Optional[str] = None