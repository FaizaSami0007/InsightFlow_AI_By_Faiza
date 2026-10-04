import io

from fastapi.testclient import TestClient


def register_and_login(client: TestClient, email: str, password: str = "Password123!") -> str:
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "Test User"},
    )
    res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    return res.json()["access_token"]


def upload_dataset(client: TestClient, token: str, filename: str, content: str) -> dict:
    files = {"file": (filename, io.BytesIO(content.encode("utf-8")), "text/csv")}
    headers = {"Authorization": f"Bearer {token}"}
    res = client.post(
        "/api/v1/datasets",
        data={"name": "Sales Data", "description": "Q4 regional sales"},
        files=files,
        headers=headers,
    )
    assert res.status_code == 201
    return res.json()


def test_profile_endpoint_full_flow(client: TestClient):
    token = register_and_login(client, "profiler_user@example.com")
    csv_data = "customer_id,region,sales,is_active,created_at\n1,North,500.50,true,2026-01-01\n2,South,300.00,false,2026-01-02\n3,North,200.00,true,2026-01-03\n"
    ds = upload_dataset(client, token, "sales.csv", csv_data)
    dataset_id = ds["id"]
    version_id = ds["latest_version"]["id"]

    headers = {"Authorization": f"Bearer {token}"}

    # 1. Trigger profiling
    res = client.post(
        f"/api/v1/datasets/{dataset_id}/versions/{version_id}/profile",
        headers=headers,
    )
    assert res.status_code == 200
    profile = res.json()
    assert profile["status"] == "COMPLETED"
    assert profile["row_count"] == 3
    assert profile["column_count"] == 5
    assert len(profile["column_profiles"]) == 5

    # Check Quality Report
    quality = profile["quality_report"]
    assert quality is not None
    assert quality["overall_score"] > 80.0
    assert quality["grade"] in ["A", "B"]

    # Check Semantic Columns
    semantics = profile["semantic_columns"]
    assert len(semantics) == 5
    sem_dict = {s["column_name"]: s for s in semantics}
    assert sem_dict["sales"]["inferred_role"] == "MEASURE"
    assert sem_dict["sales"]["is_measure"] is True
    assert sem_dict["sales"]["possible_currency"] is True
    assert sem_dict["region"]["inferred_role"] == "DIMENSION"
    assert sem_dict["customer_id"]["inferred_role"] == "IDENTIFIER"

    # 2. GET latest profile endpoint
    get_res = client.get(f"/api/v1/datasets/{dataset_id}/profile", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["id"] == profile["id"]


def test_multi_tenant_isolation_profiling(client: TestClient):
    token_a = register_and_login(client, "user_a@example.com")
    token_b = register_and_login(client, "user_b@example.com")

    csv_data = "id,value\n1,100\n2,200\n"
    ds_a = upload_dataset(client, token_a, "private_a.csv", csv_data)
    dataset_id = ds_a["id"]
    version_id = ds_a["latest_version"]["id"]

    # User B attempts to profile User A's dataset
    res = client.post(
        f"/api/v1/datasets/{dataset_id}/versions/{version_id}/profile",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert res.status_code == 404


def test_version_specific_profiling_independence(client: TestClient):
    token = register_and_login(client, "version_user@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Upload Version 1 (2 rows)
    csv_v1 = "id,val\n1,10\n2,20\n"
    ds = upload_dataset(client, token, "data_v1.csv", csv_v1)
    dataset_id = ds["id"]
    v1_id = ds["latest_version"]["id"]

    # Profile v1
    res_v1 = client.post(f"/api/v1/datasets/{dataset_id}/versions/{v1_id}/profile", headers=headers)
    assert res_v1.status_code == 200
    prof_v1 = res_v1.json()
    assert prof_v1["row_count"] == 2

    # Upload Version 2 (4 rows)
    csv_v2 = "id,val\n1,10\n2,20\n3,30\n4,40\n"
    files = {"file": ("data_v2.csv", io.BytesIO(csv_v2.encode("utf-8")), "text/csv")}
    v2_upload = client.post(f"/api/v1/datasets/{dataset_id}/versions", files=files, headers=headers)
    assert v2_upload.status_code == 201
    v2_id = v2_upload.json()["id"]

    # Profile v2
    res_v2 = client.post(f"/api/v1/datasets/{dataset_id}/versions/{v2_id}/profile", headers=headers)
    assert res_v2.status_code == 200
    prof_v2 = res_v2.json()
    assert prof_v2["row_count"] == 4

    # Verify v1 profile is still intact and has 2 rows
    v1_check = client.get(f"/api/v1/datasets/{dataset_id}/versions/{v1_id}/profile", headers=headers)
    assert v1_check.status_code == 200
    assert v1_check.json()["row_count"] == 2


def test_semantic_override_endpoint(client: TestClient):
    token = register_and_login(client, "override_user@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    csv_data = "code,status\n101,pending\n102,active\n"
    ds = upload_dataset(client, token, "items.csv", csv_data)
    dataset_id = ds["id"]
    version_id = ds["latest_version"]["id"]

    # Profile first
    client.post(f"/api/v1/datasets/{dataset_id}/versions/{version_id}/profile", headers=headers)

    # Override column 'code' to MEASURE
    res = client.patch(
        f"/api/v1/datasets/{dataset_id}/versions/{version_id}/semantics/code",
        json={"user_role": "MEASURE", "description": "Numeric tracking code"},
        headers=headers,
    )
    assert res.status_code == 200
    updated = res.json()
    assert updated["user_role"] == "MEASURE"
    assert updated["is_measure"] is True
    assert updated["description"] == "Numeric tracking code"


def test_analytical_query_endpoint(client: TestClient):
    token = register_and_login(client, "query_user@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    csv_data = "department,salary\nEngineering,120000\nEngineering,110000\nSales,90000\n"
    ds = upload_dataset(client, token, "employees.csv", csv_data)
    dataset_id = ds["id"]
    version_id = ds["latest_version"]["id"]

    # Run analytical SQL query
    res = client.post(
        f"/api/v1/datasets/{dataset_id}/versions/{version_id}/query",
        json={"query": "SELECT department, AVG(salary) as avg_sal FROM dataset GROUP BY department ORDER BY avg_sal DESC"},
        headers=headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["columns"] == ["department", "avg_sal"]
    assert len(data["rows"]) == 2
    assert data["rows"][0][0] == "Engineering"
    assert data["rows"][0][1] == 115000.0
    assert data["execution_time_ms"] >= 0.0

    # Destructive SQL rejection
    bad_res = client.post(
        f"/api/v1/datasets/{dataset_id}/versions/{version_id}/query",
        json={"query": "DROP TABLE dataset"},
        headers=headers,
    )
    assert bad_res.status_code == 400
