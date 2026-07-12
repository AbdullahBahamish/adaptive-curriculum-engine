from dataclasses import dataclass

@dataclass
class Prerequisite:
    prerequisite_id: int
    topic_id: int
    required_topic_id: int