"""End-to-end API tests for AI Analyst conversation management and chat endpoints."""

import io

from fastapi.testclient import TestClient


def get_auth_token(client: TestClient, email="ai_api_user@example.com", password="Password123!"):
    client.post("/api/v1/auth/register", json={"email": email, "password": password, "full_name": "AI API User"})
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return res.json()["access_token"]


def upload_sample_dataset(client: TestClient, token: str):
    csv_content = b"region,revenue\nNorth,150000\nSouth,220000\nEast,180000\nWest,95000\n"
    res = client.post(
        "/api/v1/datasets",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("ai_sample.csv", io.BytesIO(csv_content), "text/csv")},
        data={"name": "AI Test Dataset"},
    )
    assert res.status_code == 201
    data = res.json()
    ver_id = data["latest_version"]["id"] if data.get("latest_version") else None
    return {"id": data["id"], "current_version_id": ver_id}


def test_ai_conversations_lifecycle(client: TestClient):
    token = get_auth_token(client, "ai_conv_user@example.com")
    ds = upload_sample_dataset(client, token)

    # 1. Create conversation
    create_res = client.post(
        "/api/v1/ai/conversations",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "dataset_id": ds["id"],
            "dataset_version_id": ds["current_version_id"],
            "title": "Revenue Exploration",
        },
    )
    assert create_res.status_code == 201
    conv_data = create_res.json()
    conv_id = conv_data["id"]
    assert conv_data["title"] == "Revenue Exploration"
    assert conv_data["dataset_id"] == ds["id"]

    # 2. List conversations
    list_res = client.get(
        "/api/v1/ai/conversations",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert list_res.status_code == 200
    conv_list = list_res.json()
    assert len(conv_list) >= 1
    assert any(c["id"] == conv_id for c in conv_list)

    # 3. Get single conversation
    get_res = client.get(
        f"/api/v1/ai/conversations/{conv_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_res.status_code == 200
    assert get_res.json()["id"] == conv_id

    # 4. Chat within existing conversation
    chat_res = client.post(
        "/api/v1/ai/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "dataset_id": ds["id"],
            "dataset_version_id": ds["current_version_id"],
            "conversation_id": conv_id,
            "message": "What is the highest revenue by region?",
        },
    )
    assert chat_res.status_code == 200
    chat_data = chat_res.json()
    assert chat_data["conversation_id"] == conv_id
    assert "message" in chat_data
    assert len(chat_data["tool_calls"]) >= 1

    # 5. Delete conversation
    del_res = client.delete(
        f"/api/v1/ai/conversations/{conv_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert del_res.status_code == 204

    # 6. Verify deleted
    get_after_del = client.get(
        f"/api/v1/ai/conversations/{conv_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_after_del.status_code == 404
