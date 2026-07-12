from dataclasses import dataclass
from typing import Optional

@dataclass
class Course:
    course_id: int
    university_id: int
    course_code: str
    course_name: str
    course_description: Optional[str] = None
    course_credits: int = 0
    course_semester: int = 1
    course_classification: str = "Core"
    course_estimated_hours: int = 0
    course_difficulty: int = 1
    course_practical_hours: int = 0
    course_theoretical_hours: int = 0   


# Classification
# Core
# Elective
# Major
# Minor
# General Education
# Capstone


# difficulty
# 1 = Very Easy
# 2 = Easy
# 3 = Intermediate
# 4 = Advanced
# 5 = Expert
