from sqlalchemy import create_engine 
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql+psycopg2://postgres@127.0.0.1:5432/adaptive_curriculum_db"

engine = create_engine(
    DATABASE_URL, 
    echo=True
)

SessionLocal = sessionmaker(
    autoflush = False,
    autocommit = False,
    bind = engine
)