import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import init_db
from app.services.model_service import model_service

@pytest.fixture(scope="session", autouse=True)
def setup_database_and_model():
    init_db()
    model_service.load_model()

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client
