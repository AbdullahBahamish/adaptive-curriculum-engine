from database.session import engine

try:
    with engine.connect() as connection:
        print("Connected successfully!")
except Exception as e:
    print(e)
    
from database.base import Base

from database.models.university import University
from database.models.course import Course

print(Base.metadata.tables.keys())