from dataclasses import dataclass
from typing import Optional

@dataclass
class Job:
    job_id: int
    job_title: str
    job_country: str
    job_industry: str
    job_company: str
    job_location: str
    job_experience_level: str
    job_salary: Optional[float]