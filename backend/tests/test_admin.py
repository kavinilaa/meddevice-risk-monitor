import pytest
import uuid

@pytest.fixture
def admin_headers(client):
    res = client.post("/api/auth/login", json={
        "email": "admin@meddevice.local",
        "password": "Admin@123456"
    })
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def user_headers(client):
    unique_email = f"tech_{uuid.uuid4().hex[:8]}@hospital.org"
    res = client.post("/api/auth/signup", json={
        "full_name": "Tech Alex",
        "email": unique_email,
        "password": "Password123!",
        "confirm_password": "Password123!",
        "role": "MAINTENANCE_TEAM"
    })
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_admin_dashboard(client, admin_headers):
    response = client.get("/api/admin/dashboard", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert "total_users" in data
    assert "total_historical_events" in data
    assert data["total_historical_events"] > 0

def test_user_cannot_access_admin(client, user_headers):
    response = client.get("/api/admin/dashboard", headers=user_headers)
    assert response.status_code == 403

def test_admin_users_and_logs(client, admin_headers):
    # Get users
    res = client.get("/api/admin/users", headers=admin_headers)
    assert res.status_code == 200
    users = res.json()
    assert len(users) >= 1

    # Get logs
    logs_res = client.get("/api/admin/logs", headers=admin_headers)
    assert logs_res.status_code == 200
    logs = logs_res.json()
    assert len(logs) >= 1
