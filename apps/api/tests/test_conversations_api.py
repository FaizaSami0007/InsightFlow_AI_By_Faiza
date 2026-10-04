import io

from fastapi.testclient import TestClient


def get_auth_token(client: TestClient, email: str = "conv_user_1@example.com") -> str:
    client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "Password123!",
            "full_name": "Conversation User",
        },
    )
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123!"},
    )
    return login_res.json()["access_token"]


def upload_test_dataset(client: TestClient, token: str) -> dict:
    csv_content = b"region,category,revenue,profit\nNorth,Hardware,1000,200\nSouth,Software,2000,400\n"
    res = client.post(
        "/api/v1/datasets",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("sales.csv", io.BytesIO(csv_content), "text/csv")},
        data={"name": "Sales Data"},
    )
    assert res.status_code == 201
    data = res.json()
    ver_id = data["latest_version"]["id"] if data.get("latest_version") else None
    return {"id": data["id"], "current_version_id": ver_id}


def test_conversation_lifecycle_and_starters(client: TestClient):
    token = get_auth_token(client, "conv_lifecycle@example.com")
    ds = upload_test_dataset(client, token)

    # 1. Get dynamic starter questions
    starters_res = client.get(
        f"/api/v1/ai/datasets/{ds['id']}/versions/{ds['current_version_id']}/starters",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert starters_res.status_code == 200
    starters = starters_res.json()
    assert isinstance(starters, list)
    assert len(starters) >= 1

    # 2. Create conversation
    create_res = client.post(
        "/api/v1/ai/conversations",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "dataset_id": ds["id"],
            "dataset_version_id": ds["current_version_id"],
            "title": "Quarterly Performance Review",
        },
    )
    assert create_res.status_code == 201
    conv = create_res.json()
    conv_id = conv["id"]
    assert conv["title"] == "Quarterly Performance Review"
    assert conv["dataset_id"] == ds["id"]

    # 3. List conversations
    list_res = client.get(
        f"/api/v1/ai/conversations?dataset_id={ds['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert list_res.status_code == 200
    items = list_res.json()
    assert len(items) >= 1
    assert any(c["id"] == conv_id for c in items)

    # 4. Get conversation detail
    detail_res = client.get(
        f"/api/v1/ai/conversations/{conv_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["id"] == conv_id

    # 5. Delete conversation
    del_res = client.delete(
        f"/api/v1/ai/conversations/{conv_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert del_res.status_code == 204

    # 6. Verify 404 after deletion
    get_after_del = client.get(
        f"/api/v1/ai/conversations/{conv_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_after_del.status_code == 404


def test_conversation_user_isolation(client: TestClient):
    token_a = get_auth_token(client, "user_a@example.com")
    token_b = get_auth_token(client, "user_b@example.com")

    ds_a = upload_test_dataset(client, token_a)

    # User A creates conversation
    create_res = client.post(
        "/api/v1/ai/conversations",
        headers={"Authorization": f"Bearer {token_a}"},
        json={
            "dataset_id": ds_a["id"],
            "dataset_version_id": ds_a["current_version_id"],
            "title": "User A Private Session",
        },
    )
    conv_id_a = create_res.json()["id"]

    # User B attempts to access User A's conversation -> 404 / Unauthorized
    res_b = client.get(
        f"/api/v1/ai/conversations/{conv_id_a}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert res_b.status_code == 404

    # User B attempts to delete User A's conversation -> 404
    del_b = client.delete(
        f"/api/v1/ai/conversations/{conv_id_a}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert del_b.status_code == 404
