from dataclasses import dataclass

@dataclass
class Roadmap:
    roadmap_id: int
    student_id: int
    roadmap_title: str
    roadmap_duration_weeks: int