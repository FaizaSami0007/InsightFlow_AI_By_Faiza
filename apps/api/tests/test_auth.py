from datetime import timedelta

from fastapi.testclient import TestClient

from app.users.security import create_access_token


def test_user_registration_success(client: TestClient) -> None:
    payload = {
        "email": "analyst@insightflow.ai",
        "password": "Password123!",
        "full_name": "Data Analyst",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "analyst@insightflow.ai"
    assert data["full_name"] == "Data Analyst"
    assert "id" in data
    assert "password" not in data
    assert "password_hash" not in data


def test_user_registration_duplicate_email(client: TestClient) -> None:
    payload = {
        "email": "duplicate@insightflow.ai",
        "password": "Password123!",
        "full_name": "First User",
    }
    r1 = client.post("/api/v1/auth/register", json=payload)
    assert r1.status_code == 201

    # Second attempt with same email
    r2 = client.post("/api/v1/auth/register", json=payload)
    assert r2.status_code == 409
    data = r2.json()
    assert "error" in data
    assert data["error"]["code"] == "CONFLICT"


def test_user_registration_invalid_email(client: TestClient) -> None:
    payload = {
        "email": "not-an-email",
        "password": "Password123!",
        "full_name": "Invalid Email",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_user_registration_weak_password(client: TestClient) -> None:
    payload = {
        "email": "weak@insightflow.ai",
        "password": "short",
        "full_name": "Weak Password",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422


def test_user_login_success(client: TestClient) -> None:
    # 1. Register user
    reg_payload = {
        "email": "login_test@insightflow.ai",
        "password": "SecurePassword1!",
        "full_name": "Login Tester",
    }
    client.post("/api/v1/auth/register", json=reg_payload)

    # 2. Login
    login_payload = {
        "email": "login_test@insightflow.ai",
        "password": "SecurePassword1!",
    }
    response = client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "login_test@insightflow.ai"


def test_user_login_incorrect_password(client: TestClient) -> None:
    reg_payload = {
        "email": "wrongpass@insightflow.ai",
        "password": "SecurePassword1!",
        "full_name": "Wrong Pass Tester",
    }
    client.post("/api/v1/auth/register", json=reg_payload)

    login_payload = {
        "email": "wrongpass@insightflow.ai",
        "password": "IncorrectPassword!",
    }
    response = client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_ERROR"


def test_get_current_user_me(client: TestClient) -> None:
    # 1. Register & login
    reg_payload = {
        "email": "me_test@insightflow.ai",
        "password": "SecurePassword1!",
        "full_name": "Profile Tester",
    }
    client.post("/api/v1/auth/register", json=reg_payload)
    login_resp = client.post(
        "/api/v1/auth/login", json={"email": reg_payload["email"], "password": reg_payload["password"]}
    )
    token = login_resp.json()["access_token"]

    # 2. Call /me with bearer header
    headers = {"Authorization": f"Bearer {token}"}
    me_resp = client.get("/api/v1/auth/me", headers=headers)
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert me_data["email"] == "me_test@insightflow.ai"
    assert me_data["full_name"] == "Profile Tester"
    assert me_data["is_active"] is True


def test_get_me_missing_token(client: TestClient) -> None:
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_ERROR"


def test_get_me_expired_token(client: TestClient) -> None:
    # Generate already expired token
    expired_token = create_access_token(
        data={"sub": "any-user-id", "email": "expired@insightflow.ai"},
        expires_delta=timedelta(minutes=-10),
    )
    headers = {"Authorization": f"Bearer {expired_token}"}
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_ERROR"


def test_logout_endpoint(client: TestClient) -> None:
    reg_payload = {
        "email": "logout@insightflow.ai",
        "password": "SecurePassword1!",
        "full_name": "Logout Tester",
    }
    client.post("/api/v1/auth/register", json=reg_payload)
    login_resp = client.post(
        "/api/v1/auth/login", json={"email": reg_payload["email"], "password": reg_payload["password"]}
    )
    token = login_resp.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    logout_resp = client.post("/api/v1/auth/logout", headers=headers)
    assert logout_resp.status_code == 200
    assert logout_resp.json()["status"] == "ok"
