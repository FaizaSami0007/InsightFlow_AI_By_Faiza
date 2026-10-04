"""Integration tests for Dashboard API endpoints and user ownership security."""

import io

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def setup_user_and_dataset(email_prefix: str):
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

    # Trigger profiling
    client.post(f"/api/v1/datasets/{dataset_id}/versions/{version_id}/profile", headers=headers)

    return headers, dataset_id, version_id


def test_generate_and_get_dashboard():
    headers, dataset_id, version_id = setup_user_and_dataset("dash_user_1")

    # 1. Preview plan first
    plan_resp = client.post(
        "/api/v1/dashboards/plan-preview",
        json={
            "dataset_id": dataset_id,
            "dataset_version_id": version_id,
            "purpose": "sales",
            "intent": "Sales Performance Summary",
        },
        headers=headers,
    )
    assert plan_resp.status_code == 200
    plan_data = plan_resp.json()
    assert len(plan_data["widgets"]) >= 3

    # 2. Generate dashboard
    gen_resp = client.post(
        "/api/v1/dashboards/generate",
        json={
            "dataset_id": dataset_id,
            "dataset_version_id": version_id,
            "purpose": "sales",
            "intent": "Sales Performance Summary",
        },
        headers=headers,
    )
    assert gen_resp.status_code == 201
    dash_data = gen_resp.json()
    dash_id = dash_data["id"]
    assert dash_data["name"] is not None
    assert dash_data["status"] == "READY"
    assert len(dash_data["widgets"]) >= 3
    assert len(dash_data["filters"]) >= 1

    # Verify widget provenance
    first_widget = dash_data["widgets"][0]
    assert first_widget["analysis_id"] is not None
    assert first_widget["chart_spec"] is not None

    # 3. Retrieve dashboard
    get_resp = client.get(f"/api/v1/dashboards/{dash_id}", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == dash_id

    # 4. List dashboards
    list_resp = client.get("/api/v1/dashboards", headers=headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) >= 1


def test_duplicate_and_delete_dashboard():
    headers, dataset_id, version_id = setup_user_and_dataset("dash_user_2")

    gen_resp = client.post(
        "/api/v1/dashboards/generate",
        json={
            "dataset_id": dataset_id,
            "dataset_version_id": version_id,
            "purpose": "operations",
        },
        headers=headers,
    )
    dash_id = gen_resp.json()["id"]

    # Duplicate
    dup_resp = client.post(f"/api/v1/dashboards/{dash_id}/duplicate", headers=headers)
    assert dup_resp.status_code == 201
    dup_id = dup_resp.json()["id"]
    assert dup_id != dash_id
    assert "(Copy)" in dup_resp.json()["name"]

    # Delete original
    del_resp = client.delete(f"/api/v1/dashboards/{dash_id}", headers=headers)
    assert del_resp.status_code == 204

    # Verify original is gone but duplicate persists
    get_resp = client.get(f"/api/v1/dashboards/{dash_id}", headers=headers)
    assert get_resp.status_code == 404

    get_dup = client.get(f"/api/v1/dashboards/{dup_id}", headers=headers)
    assert get_dup.status_code == 200


def test_cross_user_dashboard_authorization():
    headers_a, dataset_id_a, version_id_a = setup_user_and_dataset("user_a")
    headers_b, _, _ = setup_user_and_dataset("user_b")

    # User A creates dashboard
    gen_resp = client.post(
        "/api/v1/dashboards/generate",
        json={
            "dataset_id": dataset_id_a,
            "dataset_version_id": version_id_a,
            "purpose": "sales",
        },
        headers=headers_a,
    )
    dash_id = gen_resp.json()["id"]

    # User B attempts to access User A's dashboard -> 403 Forbidden
    resp_b = client.get(f"/api/v1/dashboards/{dash_id}", headers=headers_b)
    assert resp_b.status_code == 403

    # User B attempts to generate dashboard using User A's dataset -> 404/403
    resp_b_gen = client.post(
        "/api/v1/dashboards/generate",
        json={
            "dataset_id": dataset_id_a,
            "dataset_version_id": version_id_a,
        },
        headers=headers_b,
    )
    assert resp_b_gen.status_code in [403, 404]


def test_dashboard_refresh_with_filter():
    headers, dataset_id, version_id = setup_user_and_dataset("dash_user_refresh")

    gen_resp = client.post(
        "/api/v1/dashboards/generate",
        json={
            "dataset_id": dataset_id,
            "dataset_version_id": version_id,
            "purpose": "sales",
        },
        headers=headers,
    )
    dash_id = gen_resp.json()["id"]

    # Refresh dashboard with filter: region = 'North'
    ref_resp = client.post(
        f"/api/v1/dashboards/{dash_id}/refresh",
        params={"filter_overrides": {"region": "North"}},
        headers=headers,
    )
    assert ref_resp.status_code == 200
    ref_data = ref_resp.json()
    assert ref_data["status"] == "READY"


def test_dashboard_quality_score():
    headers, dataset_id, version_id = setup_user_and_dataset("dash_user_quality")

    gen_resp = client.post(
        "/api/v1/dashboards/generate",
        json={
            "dataset_id": dataset_id,
            "dataset_version_id": version_id,
            "purpose": "sales",
        },
        headers=headers,
    )
    dash_id = gen_resp.json()["id"]

    qual_resp = client.get(f"/api/v1/dashboards/{dash_id}/quality", headers=headers)
    assert qual_resp.status_code == 200
    q_data = qual_resp.json()
    assert q_data["overall_score"] >= 50.0
    assert q_data["valid_widget_ratio"] == 1.0
    assert "total_widgets" in q_data["breakdown"]
