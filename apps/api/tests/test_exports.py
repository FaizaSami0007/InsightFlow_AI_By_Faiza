"""Unit and Integration tests for Phase 9 Dashboard Exports (PDF, PNG, CSV, JSON)."""

import io

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def setup_user_and_dashboard(email_prefix: str):
    email = f"{email_prefix}@example.com"
    client.post("/api/v1/auth/register", json={"email": email, "password": "Password123!", "full_name": "Test User"})
    login_resp = client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"})
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    csv_data = (
        b"date,region,category,sales,quantity\n"
        b"2025-01-01,North,Electronics,500,2\n"
        b"2025-01-02,South,Furniture,300,1\n"
        b"2025-01-03,North,Electronics,700,3\n"
        b"2025-01-04,West,Appliances,400,2\n"
        b"2025-01-05,East,Electronics,600,4\n"
    )
    up_resp = client.post(
        "/api/v1/datasets",
        files={"file": ("sales_data.csv", io.BytesIO(csv_data), "text/csv")},
        data={"name": "Sales Records"},
        headers=headers,
    )
    ds_data = up_resp.json()
    dataset_id = ds_data["id"]
    version_id = ds_data["latest_version"]["id"]

    # Profile dataset
    client.post(f"/api/v1/datasets/{dataset_id}/versions/{version_id}/profile", headers=headers)

    # Generate dashboard
    gen_resp = client.post(
        "/api/v1/dashboards/generate",
        json={
            "dataset_id": dataset_id,
            "dataset_version_id": version_id,
            "purpose": "sales",
        },
        headers=headers,
    )
    dash_data = gen_resp.json()
    dashboard_id = dash_data["id"]
    return headers, dashboard_id


def test_create_pdf_export():
    headers, dashboard_id = setup_user_and_dashboard("export_user_pdf")
    payload = {
        "format": "pdf",
        "page_size": "A4",
        "orientation": "landscape",
        "include_provenance": True,
        "include_filters": True,
        "filter_values": {"region": "North"},
    }
    resp = client.post(f"/api/v1/dashboards/{dashboard_id}/exports", json=payload, headers=headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["format"] == "pdf"
    assert data["status"] == "COMPLETED"
    assert data["file_size_bytes"] > 0
    assert "download_url" in data

    # Test download endpoint
    export_id = data["id"]
    dl_resp = client.get(f"/api/v1/exports/{export_id}/download", headers=headers)
    assert dl_resp.status_code == 200
    assert dl_resp.headers["content-type"] == "application/pdf"
    assert len(dl_resp.content) == data["file_size_bytes"]


def test_create_png_export():
    headers, dashboard_id = setup_user_and_dashboard("export_user_png")
    payload = {
        "format": "png",
        "orientation": "landscape",
        "filter_values": {"year": 2026},
    }
    resp = client.post(f"/api/v1/dashboards/{dashboard_id}/exports", json=payload, headers=headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["format"] == "png"
    assert data["status"] == "COMPLETED"
    assert data["file_size_bytes"] > 0

    export_id = data["id"]
    dl_resp = client.get(f"/api/v1/exports/{export_id}/download", headers=headers)
    assert dl_resp.status_code == 200
    assert dl_resp.headers["content-type"] == "image/png"


def test_create_csv_export():
    headers, dashboard_id = setup_user_and_dashboard("export_user_csv")
    payload = {
        "format": "csv",
        "filter_values": {"region": "West"},
    }
    resp = client.post(f"/api/v1/dashboards/{dashboard_id}/exports", json=payload, headers=headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["format"] == "csv"
    assert data["status"] == "COMPLETED"

    export_id = data["id"]
    dl_resp = client.get(f"/api/v1/exports/{export_id}/download", headers=headers)
    assert dl_resp.status_code == 200
    content_str = dl_resp.text
    assert "# InsightFlow AI Dashboard Export" in content_str


def test_create_json_export():
    headers, dashboard_id = setup_user_and_dashboard("export_user_json")
    payload = {
        "format": "json",
    }
    resp = client.post(f"/api/v1/dashboards/{dashboard_id}/exports", json=payload, headers=headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["format"] == "json"

    export_id = data["id"]
    dl_resp = client.get(f"/api/v1/exports/{export_id}/download", headers=headers)
    assert dl_resp.status_code == 200
    json_data = dl_resp.json()
    assert "dashboard" in json_data
    assert "widgets" in json_data


def test_list_dashboard_exports():
    headers, dashboard_id = setup_user_and_dashboard("export_user_list")
    # Generate an export
    client.post(f"/api/v1/dashboards/{dashboard_id}/exports", json={"format": "pdf"}, headers=headers)

    resp = client.get(f"/api/v1/dashboards/{dashboard_id}/exports", headers=headers)
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) >= 1
    assert items[0]["dashboard_id"] == dashboard_id


def test_export_security_idor_isolation():
    headers_u1, dashboard_id = setup_user_and_dashboard("export_user_idor1")
    headers_u2, _ = setup_user_and_dashboard("export_user_idor2")

    # User 1 creates an export
    resp = client.post(f"/api/v1/dashboards/{dashboard_id}/exports", json={"format": "pdf"}, headers=headers_u1)
    assert resp.status_code == 201
    export_id = resp.json()["id"]

    # User 2 attempts to get or download User 1's export
    unauth_resp = client.get(f"/api/v1/exports/{export_id}", headers=headers_u2)
    assert unauth_resp.status_code == 404

    unauth_dl = client.get(f"/api/v1/exports/{export_id}/download", headers=headers_u2)
    assert unauth_dl.status_code == 404
