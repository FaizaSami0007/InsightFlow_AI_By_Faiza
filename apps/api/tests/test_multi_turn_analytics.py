import io

from fastapi.testclient import TestClient


def get_auth_token(client: TestClient, email: str = "multi_turn_user@example.com") -> str:
    client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "Password123!",
            "full_name": "Multi Turn User",
        },
    )
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123!"},
    )
    return login_res.json()["access_token"]


def upload_sales_dataset(client: TestClient, token: str) -> dict:
    csv_data = (
        b"region,category,revenue,profit\n"
        b"North,Hardware,1820000,450000\n"
        b"South,Software,1200000,300000\n"
        b"East,Services,950000,210000\n"
        b"West,Hardware,800000,180000\n"
    )
    res = client.post(
        "/api/v1/datasets",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("sales_data.csv", io.BytesIO(csv_data), "text/csv")},
        data={"name": "Sales Multi-Turn Dataset"},
    )
    assert res.status_code == 201
    data = res.json()
    ver_id = data["latest_version"]["id"] if data.get("latest_version") else None
    return {"id": data["id"], "current_version_id": ver_id}


def test_multi_turn_flow_and_follow_up_questions(client: TestClient):
    token = get_auth_token(client, "multi_turn_flow@example.com")
    ds = upload_sales_dataset(client, token)

    # Turn 1: Initial Question: "What region has the highest revenue?"
    turn1_res = client.post(
        "/api/v1/ai/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "dataset_id": ds["id"],
            "dataset_version_id": ds["current_version_id"],
            "message": "What region has the highest revenue?",
        },
    )
    assert turn1_res.status_code == 200
    turn1 = turn1_res.json()
    conv_id = turn1["conversation_id"]
    assert len(turn1["tool_calls"]) >= 1
    assert turn1["tool_calls"][0]["name"] == "group_by"
    assert "North" in turn1["message"] or "1,820,000" in turn1["message"]
    assert "suggested_questions" in turn1
    assert "evidence" in turn1
    assert turn1["evidence"]["dataset_id"] == ds["id"]

    # Turn 2: Follow-up question: "What about profit?" (maintains region grouping)
    turn2_res = client.post(
        "/api/v1/ai/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "dataset_id": ds["id"],
            "dataset_version_id": ds["current_version_id"],
            "conversation_id": conv_id,
            "message": "What about profit across regions?",
        },
    )
    assert turn2_res.status_code == 200
    turn2 = turn2_res.json()
    assert turn2["conversation_id"] == conv_id
    assert len(turn2["tool_calls"]) >= 1
    assert turn2["tool_calls"][0]["name"] == "group_by"
    assert "profit" in str(turn2["tool_calls"][0]["arguments"])

    # Turn 3: Follow-up question: "Show the top 3" (modifies limit)
    turn3_res = client.post(
        "/api/v1/ai/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "dataset_id": ds["id"],
            "dataset_version_id": ds["current_version_id"],
            "conversation_id": conv_id,
            "message": "Show the top 3",
        },
    )
    assert turn3_res.status_code == 200
    turn3 = turn3_res.json()
    assert len(turn3["tool_calls"]) >= 1
    assert turn3["tool_calls"][0]["arguments"]["limit"] == 3

    # Turn 4: Follow-up question: "Sort ascending" (modifies sort direction)
    turn4_res = client.post(
        "/api/v1/ai/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "dataset_id": ds["id"],
            "dataset_version_id": ds["current_version_id"],
            "conversation_id": conv_id,
            "message": "Sort ascending",
        },
    )
    assert turn4_res.status_code == 200
    turn4 = turn4_res.json()
    assert len(turn4["tool_calls"]) >= 1


def test_ambiguity_clarification_flow(client: TestClient):
    token = get_auth_token(client, "ambiguity_user@example.com")

    # Dataset with product_category and customer_category
    csv_ambig = b"product_category,customer_category,revenue\nHardware,Enterprise,5000\nSoftware,SMB,3000\n"
    ds_res = client.post(
        "/api/v1/datasets",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("ambig.csv", io.BytesIO(csv_ambig), "text/csv")},
        data={"name": "Ambiguous Categories"},
    )
    assert ds_res.status_code == 201
    ds_data = ds_res.json()
    ver_id = ds_data["latest_version"]["id"] if ds_data.get("latest_version") else None
    ds = {"id": ds_data["id"], "current_version_id": ver_id}

    # Step 1: User asks ambiguous question
    chat_res = client.post(
        "/api/v1/ai/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "dataset_id": ds["id"],
            "dataset_version_id": ds["current_version_id"],
            "message": "Show sales by category",
        },
    )
    assert chat_res.status_code == 200
    resp1 = chat_res.json()
    assert resp1["needs_clarification"] is True
    assert "Which category" in resp1["message"] or "product_category" in resp1["message"]
    conv_id = resp1["conversation_id"]

    # Step 2: User responds to clarification with specific column
    chat_res2 = client.post(
        "/api/v1/ai/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "dataset_id": ds["id"],
            "dataset_version_id": ds["current_version_id"],
            "conversation_id": conv_id,
            "message": "Use product_category",
        },
    )
    assert chat_res2.status_code == 200
    resp2 = chat_res2.json()
    assert len(resp2["tool_calls"]) >= 1
    assert resp2["tool_calls"][0]["arguments"]["dimensions"] == ["product_category"]


def test_unsupported_request_handling(client: TestClient):
    token = get_auth_token(client, "unsupported_user@example.com")
    ds = upload_sales_dataset(client, token)

    chat_res = client.post(
        "/api/v1/ai/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "dataset_id": ds["id"],
            "dataset_version_id": ds["current_version_id"],
            "message": "Predict next year's sales and generate dashboard",
        },
    )
    assert chat_res.status_code == 200
    resp = chat_res.json()
    assert "not currently supported" in resp["message"].lower() or "available" in resp["message"].lower()
    assert len(resp["tool_calls"]) == 0
