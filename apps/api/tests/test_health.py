from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "InsightFlow AI"
    assert data["status"] == "online"


def test_health_liveness(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "InsightFlow AI"
    assert "timestamp" in data


def test_root_health_endpoint(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_health_readiness(client: TestClient) -> None:
    response = client.get("/api/v1/health/ready")
    # Response code is 200 (if db reachable) or 503 (if db unreachable in test environment without live postgres)
    assert response.status_code in [200, 503]
    data = response.json()
    assert "checks" in data
    assert "database" in data["checks"]
