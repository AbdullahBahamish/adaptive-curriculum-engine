from database.base import Base
from database.models.university import University
from database.models.course import Course

print(Base.metadata.tables.keys())