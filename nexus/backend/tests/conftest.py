import os

os.environ["NEXUS_DATABASE_URL"] = "sqlite:///:memory:"
os.environ["NEXUS_JWT_SECRET"] = "test-secret"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def auth_headers(client):
    signup_payload = {
        "brand_name": "Test Brand",
        "category": "home",
        "full_name": "Test Founder",
        "email": "founder@test.com",
        "password": "password123",
    }
    response = client.post("/api/auth/signup", json=signup_payload)
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
