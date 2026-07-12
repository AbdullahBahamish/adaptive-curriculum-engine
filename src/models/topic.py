from dataclasses import dataclass
from typing import Optional

@dataclass
class Topic:
    topic_id: int
    course_id: int
    topic_name: str
    topic_difficulty: int
    topic_estimated_hours: int
    topic_description: Optional[str] = None