import pytest
import uuid

def test_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert data["model"] == "loaded"

def test_signup_biomedical_engineer(client):
    unique_email = f"test_bio_{uuid.uuid4().hex[:8]}@hospital.org"
    payload = {
        "full_name": "Dr. Sarah Lin",
        "email": unique_email,
        "password": "Password123!",
        "confirm_password": "Password123!",
        "role": "BIOMEDICAL_ENGINEER"
    }
    response = client.post("/api/auth/signup", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == unique_email
    assert data["user"]["role"] == "BIOMEDICAL_ENGINEER"

def test_signup_duplicate_email(client):
    payload = {
        "full_name": "Dr. Sarah Lin",
        "email": "admin@meddevice.local",
        "password": "Password123!",
        "confirm_password": "Password123!",
        "role": "BIOMEDICAL_ENGINEER"
    }
    response = client.post("/api/auth/signup", json=payload)
    assert response.status_code == 400

def test_admin_login(client):
    payload = {
        "email": "admin@meddevice.local",
        "password": "Admin@123456"
    }
    response = client.post("/api/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["role"] == "ADMIN"
