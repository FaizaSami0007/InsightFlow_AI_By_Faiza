from fastapi import APIRouter
from fastapi.testclient import TestClient

from app.core.exceptions import (
    AppError,
    NotFoundError,
    PermissionDeniedError,
)
from app.main import app

# Add temporary sample routes to verify error handling
sample_error_router = APIRouter(prefix="/test-errors", tags=["testing"])


@sample_error_router.get("/custom-not-found")
async def trigger_not_found():
    raise NotFoundError("Dataset 123 was not found", details={"dataset_id": "123"})


@sample_error_router.get("/permission-denied")
async def trigger_permission_denied():
    raise PermissionDeniedError("You lack permission to edit this dashboard")


@sample_error_router.get("/generic-app-error")
async def trigger_generic_app_error():
    raise AppError(message="Custom analytical failure", code="ANALYTICS_FAILED", status_code=400)


@sample_error_router.get("/unhandled-exception")
async def trigger_unhandled():
    raise RuntimeError("Unexpected internal crash")


app.include_router(sample_error_router)


def test_404_not_found() -> None:
    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/non-existent-route-404")
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "NOT_FOUND"
    assert "request_id" in data["error"]


def test_custom_domain_not_found(client: TestClient) -> None:
    response = client.get("/test-errors/custom-not-found")
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "NOT_FOUND"
    assert data["error"]["message"] == "Dataset 123 was not found"
    assert data["error"]["details"]["dataset_id"] == "123"


def test_permission_denied(client: TestClient) -> None:
    response = client.get("/test-errors/permission-denied")
    assert response.status_code == 403
    data = response.json()
    assert data["error"]["code"] == "PERMISSION_DENIED"


def test_generic_app_error(client: TestClient) -> None:
    response = client.get("/test-errors/generic-app-error")
    assert response.status_code == 400
    data = response.json()
    assert data["error"]["code"] == "ANALYTICS_FAILED"
    assert data["error"]["message"] == "Custom analytical failure"


def test_unhandled_exception_sanitization() -> None:
    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/test-errors/unhandled-exception")
    assert response.status_code == 500
    data = response.json()
    assert data["error"]["code"] == "INTERNAL_SERVER_ERROR"
    # Ensure raw internal trace is not leaked in message
    assert "Unexpected internal crash" not in data["error"]["message"]
