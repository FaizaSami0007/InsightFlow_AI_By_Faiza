import io

import polars as pl
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def auth_header_user_a(client: TestClient) -> dict:
    reg_payload = {"email": "user_a@insightflow.ai", "password": "Password123!", "full_name": "User A"}
    client.post("/api/v1/auth/register", json=reg_payload)
    login_resp = client.post(
        "/api/v1/auth/login", json={"email": reg_payload["email"], "password": reg_payload["password"]}
    )
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_header_user_b(client: TestClient) -> dict:
    reg_payload = {"email": "user_b@insightflow.ai", "password": "Password123!", "full_name": "User B"}
    client.post("/api/v1/auth/register", json=reg_payload)
    login_resp = client.post(
        "/api/v1/auth/login", json={"email": reg_payload["email"], "password": reg_payload["password"]}
    )
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_csv_bytes() -> bytes:
    csv_content = (
        "date,region,revenue,units\n"
        "2025-01-01,North,1500.50,12\n"
        "2025-01-02,South,2300.00,18\n"
        "2025-01-03,East,950.25,7\n"
        "2025-01-04,West,3100.75,25\n"
    )
    return csv_content.encode("utf-8")


@pytest.fixture
def sample_parquet_bytes() -> bytes:
    df = pl.DataFrame(
        {
            "customer_id": [101, 102, 103],
            "churn": [False, True, False],
            "score": [0.85, 0.42, 0.91],
        }
    )
    buf = io.BytesIO()
    df.write_parquet(buf)
    return buf.getvalue()


def test_upload_csv_dataset_success(client: TestClient, auth_header_user_a: dict, sample_csv_bytes: bytes) -> None:
    files = {"file": ("sales_data.csv", sample_csv_bytes, "text/csv")}
    data = {"name": "Q1 Regional Sales", "description": "Regional revenue figures for Q1"}

    response = client.post("/api/v1/datasets", files=files, data=data, headers=auth_header_user_a)
    assert response.status_code == 201
    res_data = response.json()
    assert res_data["name"] == "Q1 Regional Sales"
    assert res_data["status"] == "READY"
    assert res_data["version_count"] == 1
    assert res_data["latest_version"] is not None
    assert res_data["latest_version"]["file_format"] == "CSV"
    assert res_data["latest_version"]["row_count"] == 4
    assert res_data["latest_version"]["column_count"] == 4
    assert len(res_data["latest_version"]["checksum"]) == 64


def test_upload_parquet_dataset_success(
    client: TestClient, auth_header_user_a: dict, sample_parquet_bytes: bytes
) -> None:
    files = {"file": ("customer_churn.parquet", sample_parquet_bytes, "application/octet-stream")}
    data = {"name": "Customer Churn Analysis"}

    response = client.post("/api/v1/datasets", files=files, data=data, headers=auth_header_user_a)
    assert response.status_code == 201
    res_data = response.json()
    assert res_data["latest_version"]["file_format"] == "PARQUET"
    assert res_data["latest_version"]["row_count"] == 3
    assert res_data["latest_version"]["column_count"] == 3


def test_upload_unauthenticated(client: TestClient, sample_csv_bytes: bytes) -> None:
    files = {"file": ("sales.csv", sample_csv_bytes, "text/csv")}
    data = {"name": "Unauth dataset"}
    response = client.post("/api/v1/datasets", files=files, data=data)
    assert response.status_code == 401


def test_upload_unsupported_format(client: TestClient, auth_header_user_a: dict) -> None:
    files = {"file": ("script.exe", b"MZexecutabledata", "application/octet-stream")}
    data = {"name": "Dangerous executable"}
    response = client.post("/api/v1/datasets", files=files, data=data, headers=auth_header_user_a)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_upload_empty_file(client: TestClient, auth_header_user_a: dict) -> None:
    files = {"file": ("empty.csv", b"", "text/csv")}
    data = {"name": "Empty dataset"}
    response = client.post("/api/v1/datasets", files=files, data=data, headers=auth_header_user_a)
    assert response.status_code == 422


def test_dataset_versioning_increment(client: TestClient, auth_header_user_a: dict, sample_csv_bytes: bytes) -> None:
    # 1. Create dataset v1
    files_v1 = {"file": ("sales_v1.csv", sample_csv_bytes, "text/csv")}
    r1 = client.post("/api/v1/datasets", files=files_v1, data={"name": "Sales Over Time"}, headers=auth_header_user_a)
    dataset_id = r1.json()["id"]

    # 2. Upload dataset v2
    v2_csv = (
        "date,region,revenue,units\n"
        "2025-01-01,North,1500.50,12\n"
        "2025-01-02,South,2300.00,18\n"
        "2025-01-03,East,950.25,7\n"
        "2025-01-04,West,3100.75,25\n"
        "2025-01-05,Central,4200.00,30\n"
    ).encode("utf-8")
    files_v2 = {"file": ("sales_v2.csv", v2_csv, "text/csv")}

    r2 = client.post(f"/api/v1/datasets/{dataset_id}/versions", files=files_v2, headers=auth_header_user_a)
    assert r2.status_code == 201
    v2_data = r2.json()
    assert v2_data["version_number"] == 2
    assert v2_data["row_count"] == 5

    # 3. Verify version list
    v_list = client.get(f"/api/v1/datasets/{dataset_id}/versions", headers=auth_header_user_a)
    assert v_list.status_code == 200
    versions = v_list.json()
    assert len(versions) == 2
    assert versions[0]["version_number"] == 2
    assert versions[1]["version_number"] == 1


def test_user_ownership_isolation(
    client: TestClient,
    auth_header_user_a: dict,
    auth_header_user_b: dict,
    sample_csv_bytes: bytes,
) -> None:
    # User A creates a dataset
    files = {"file": ("user_a_private.csv", sample_csv_bytes, "text/csv")}
    r_create = client.post(
        "/api/v1/datasets", files=files, data={"name": "User A Secret Data"}, headers=auth_header_user_a
    )
    dataset_id = r_create.json()["id"]

    # User B attempts to access User A's dataset
    r_get = client.get(f"/api/v1/datasets/{dataset_id}", headers=auth_header_user_b)
    assert r_get.status_code in [403, 404]

    # User B attempts to upload a version to User A's dataset
    files_v2 = {"file": ("malicious.csv", sample_csv_bytes, "text/csv")}
    r_ver = client.post(f"/api/v1/datasets/{dataset_id}/versions", files=files_v2, headers=auth_header_user_b)
    assert r_ver.status_code in [403, 404]

    # User B attempts to download User A's dataset
    r_dl = client.get(f"/api/v1/datasets/{dataset_id}/download", headers=auth_header_user_b)
    assert r_dl.status_code in [403, 404]

    # User B dataset listing should not contain User A's dataset
    r_list = client.get("/api/v1/datasets", headers=auth_header_user_b)
    assert r_list.status_code == 200
    assert len(r_list.json()["items"]) == 0


def test_dataset_listing_and_pagination(client: TestClient, auth_header_user_a: dict, sample_csv_bytes: bytes) -> None:
    # Upload 3 datasets
    for i in range(3):
        files = {"file": (f"data_{i}.csv", sample_csv_bytes, "text/csv")}
        client.post("/api/v1/datasets", files=files, data={"name": f"Dataset {i}"}, headers=auth_header_user_a)

    # Fetch page 1 with page_size=2
    response = client.get("/api/v1/datasets?page=1&page_size=2", headers=auth_header_user_a)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["items"]) == 2
    assert data["page"] == 1
    assert data["page_size"] == 2
    assert data["total_pages"] == 2


def test_dataset_download_success(client: TestClient, auth_header_user_a: dict, sample_csv_bytes: bytes) -> None:
    files = {"file": ("download_test.csv", sample_csv_bytes, "text/csv")}
    r_create = client.post(
        "/api/v1/datasets", files=files, data={"name": "Downloadable Data"}, headers=auth_header_user_a
    )
    dataset_id = r_create.json()["id"]

    response = client.get(f"/api/v1/datasets/{dataset_id}/download", headers=auth_header_user_a)
    assert response.status_code == 200
    assert response.content == sample_csv_bytes
    assert "text/csv" in response.headers["content-type"]
