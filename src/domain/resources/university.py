from dataclasses import dataclass
from typing import Optional

@dataclass
class University:
    university_id: int
    university_name: str
    university_abbreviation: Optional[str] = None
    university_country: str = ""
    university_region: str = ""
    university_website: Optional[str] = None
    university_world_rank: Optional[int] = None
    university_degree_system: Optional[str] = None