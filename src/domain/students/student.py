from dataclasses import dataclass

@dataclass
class Student:
    student_id: int
    student_country: str
    student_university: str
    student_degree: str
    student_year: int
    student_weekly_hours: int
    student_career_goal: str