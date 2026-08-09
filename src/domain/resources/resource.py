from dataclasses import dataclass

@dataclass
class Resource:
    resource_id: int
    resource_title: str
    resource_type: str
    resource_url: str
    resource_estimated_hours: int
    resource_provider: str
    resource_difficulty: int
    resource_language: str
    resource_is_free: bool