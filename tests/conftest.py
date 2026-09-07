"""Shared pytest fixtures for the ACE AI Engine test suite."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from ace.core.config import settings
from ace.infrastructure.database.base import Base
from ace.infrastructure.database.session import get_db
from ace.api.main import app

SQLITE_URL = "sqlite:///:memory:"


@pytest.fixture
def test_db():
    """Create a fresh in-memory SQLite database with StaticPool for each test."""
    engine = create_engine(
        SQLITE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(test_db: Session) -> TestClient:
    """FastAPI test client with DB dependency overridden and valid API key."""
    def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, headers={"X-Service-API-Key": settings.service_api_key}) as c:
        yield c
    app.dependency_overrides.clear()