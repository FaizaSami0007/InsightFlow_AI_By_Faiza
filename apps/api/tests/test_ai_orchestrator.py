"""Integration tests for AIOrchestrator tool execution loop and grounded answers."""

import io

from fastapi.testclient import TestClient


def get_auth_token(client: TestClient, email="orch_user@example.com", password="Password123!"):
    client.post("/api/v1/auth/register", json={"email": email, "password": password, "full_name": "Orchestrator User"})
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return res.json()["access_token"]


def upload_sales_dataset(client: TestClient, token: str):
    csv_content = (
        b"region,category,revenue\n"
        b"North,Electronics,1200000\n"
        b"North,Furniture,620000\n"
        b"South,Electronics,450000\n"
        b"South,Furniture,310000\n"
        b"East,Electronics,890000\n"
    )
    res = client.post(
        "/api/v1/datasets",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("sales_data.csv", io.BytesIO(csv_content), "text/csv")},
        data={"name": "Regional Sales Data"},
    )
    assert res.status_code == 201
    data = res.json()
    ver_id = data["latest_version"]["id"] if data.get("latest_version") else None
    return {"id": data["id"], "current_version_id": ver_id}


def test_orchestrator_multi_turn_tool_calling_and_grounding(client: TestClient):
    token = get_auth_token(client, "orch_test_1@example.com")
    ds = upload_sales_dataset(client, token)

    chat_res = client.post(
        "/api/v1/ai/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "dataset_id": ds["id"],
            "dataset_version_id": ds["current_version_id"],
            "message": "What is the highest revenue by region?",
        },
    )

    assert chat_res.status_code == 200
    chat_resp = chat_res.json()
    assert chat_resp["conversation_id"] is not None
    assert len(chat_resp["tool_calls"]) >= 1
    assert chat_resp["tool_calls"][0]["name"] == "group_by"
    assert len(chat_resp["tool_results"]) >= 1
    assert len(chat_resp["analysis_ids"]) >= 1
    assert len(chat_resp["provenance"]) >= 1
    assert "North" in chat_resp["message"]
    assert chat_resp["needs_clarification"] is False


def test_orchestrator_ambiguity_clarification(client: TestClient):
    token = get_auth_token(client, "orch_clarify@example.com")
    ds = upload_sales_dataset(client, token)

    # Ambiguous question mentioning category with multiple options in text
    chat_res = client.post(
        "/api/v1/ai/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "dataset_id": ds["id"],
            "dataset_version_id": ds["current_version_id"],
            "message": "Show sales by category considering product_category and customer_category",
        },
    )

    assert chat_res.status_code == 200
    chat_resp = chat_res.json()
    assert chat_resp["needs_clarification"] is True
    assert "Which category" in chat_resp["message"]
