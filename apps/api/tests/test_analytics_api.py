import io

from fastapi.testclient import TestClient


def get_auth_token(client: TestClient, email="analyst@example.com", password="Password123!"):
    client.post("/api/v1/auth/register", json={"email": email, "password": password, "full_name": "Analyst User"})
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return res.json()["access_token"]


def upload_sample_dataset(client: TestClient, token: str):
    csv_content = b"region,sales,units\nNorth,100,2\nNorth,200,4\nSouth,300,6\nSouth,400,8\n"
    res = client.post(
        "/api/v1/datasets",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("sales_analytics.csv", io.BytesIO(csv_content), "text/csv")},
        data={"name": "Sales Analytics Test Dataset"},
    )
    assert res.status_code == 201
    data = res.json()
    ver_id = data["latest_version"]["id"] if data.get("latest_version") else None
    return {"id": data["id"], "current_version_id": ver_id}


def test_list_analytics_tools(client: TestClient):
    token = get_auth_token(client, "tools_user@example.com")
    res = client.get(
        "/api/v1/analytics/tools",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "tools" in data
    tool_names = [t["name"] for t in data["tools"]]
    assert "group_by" in tool_names
    assert "correlation" in tool_names
    assert "describe_dataset" in tool_names


def test_run_group_by_analysis(client: TestClient):
    token = get_auth_token(client, "group_user@example.com")
    ds_data = upload_sample_dataset(client, token)
    ds_id = ds_data["id"]
    ver_id = ds_data["current_version_id"]

    res = client.post(
        "/api/v1/analytics/run",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "dataset_id": ds_id,
            "dataset_version_id": ver_id,
            "operation": "group_by",
            "parameters": {
                "dimensions": ["region"],
                "aggregations": [
                    {"column": "sales", "agg_type": "SUM", "alias": "total_sales"},
                    {"column": "*", "agg_type": "COUNT", "alias": "count"},
                ],
            },
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "COMPLETED"
    assert data["row_count"] == 2
    assert "provenance" in data
    assert data["provenance"]["dataset_version_id"] == ver_id

    # Retrieve by analysis ID
    analysis_id = data["analysis_id"]
    get_res = client.get(
        f"/api/v1/analytics/{analysis_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_res.status_code == 200
    assert get_res.json()["analysis_id"] == analysis_id


def test_analytics_history(client: TestClient):
    token = get_auth_token(client, "history_user@example.com")
    ds_data = upload_sample_dataset(client, token)
    ds_id = ds_data["id"]
    ver_id = ds_data["current_version_id"]

    # Run analysis
    client.post(
        "/api/v1/analytics/run",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "dataset_id": ds_id,
            "dataset_version_id": ver_id,
            "operation": "describe_dataset",
            "parameters": {},
        },
    )

    # Fetch history
    res = client.get(
        f"/api/v1/analytics/history?dataset_id={ds_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    history = res.json()
    assert len(history) >= 1
    assert history[0]["operation"] == "describe_dataset"


def test_cross_user_analytics_isolation(client: TestClient):
    token_a = get_auth_token(client, "user_a_analytics@example.com")
    token_b = get_auth_token(client, "user_b_analytics@example.com")

    ds_data_a = upload_sample_dataset(client, token_a)
    ds_id_a = ds_data_a["id"]
    ver_id_a = ds_data_a["current_version_id"]

    # User B attempts to analyze User A's dataset
    res = client.post(
        "/api/v1/analytics/run",
        headers={"Authorization": f"Bearer {token_b}"},
        json={
            "dataset_id": ds_id_a,
            "dataset_version_id": ver_id_a,
            "operation": "describe_dataset",
            "parameters": {},
        },
    )
    assert res.status_code == 404
