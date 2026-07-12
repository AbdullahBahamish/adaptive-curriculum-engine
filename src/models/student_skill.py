from dataclasses import dataclass

@dataclass
class StudentSkill:
    student_id: int
    skill_id: int
    proficiency: float