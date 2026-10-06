"""Unit and Integration tests for Phase 9 Dashboard Sharing and Public Links."""

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
        b"facility,throughput,latency_ms\n"
        b"Facility A,95,12.4\n"
        b"Facility B,88,18.2\n"
        b"Facility C,92,15.1\n"
        b"Facility A,99,10.8\n"
    )
    up_resp = client.post(
        "/api/v1/datasets",
        files={"file": ("ops_data.csv", io.BytesIO(csv_data), "text/csv")},
        data={"name": "Operations Records"},
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
            "purpose": "operations",
        },
        headers=headers,
    )
    dash_data = gen_resp.json()
    dashboard_id = dash_data["id"]
    return headers, dashboard_id


def test_create_and_view_live_share_link():
    headers, dashboard_id = setup_user_and_dashboard("share_user_live")
    # 1. Create Share Link
    payload = {
        "expires_in_days": 14,
        "is_snapshot": False,
        "allowed_filters": ["facility"],
    }
    resp = client.post(f"/api/v1/dashboards/{dashboard_id}/shares", json=payload, headers=headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["is_active"] is True
    assert data["is_snapshot"] is False
    assert len(data["share_token"]) >= 32
    token = data["share_token"]

    # 2. Public / Unauthenticated Viewer access
    view_resp = client.get(f"/api/v1/shared/dashboards/{token}")
    assert view_resp.status_code == 200
    view_data = view_resp.json()
    assert len(view_data["widgets"]) >= 1
    assert view_data["is_snapshot"] is False


def test_create_snapshot_share_link():
    headers, dashboard_id = setup_user_and_dashboard("share_user_snap")
    payload = {
        "is_snapshot": True,
    }
    resp = client.post(f"/api/v1/dashboards/{dashboard_id}/shares", json=payload, headers=headers)
    assert resp.status_code == 201
    token = resp.json()["share_token"]

    # View snapshot
    view_resp = client.get(f"/api/v1/shared/dashboards/{token}")
    assert view_resp.status_code == 200
    view_data = view_resp.json()
    assert view_data["is_snapshot"] is True


def test_revoke_share_link():
    headers, dashboard_id = setup_user_and_dashboard("share_user_rev")
    # 1. Create Share
    create_resp = client.post(f"/api/v1/dashboards/{dashboard_id}/shares", json={"expires_in_days": 7}, headers=headers)
    assert create_resp.status_code == 201
    share_id = create_resp.json()["id"]
    token = create_resp.json()["share_token"]

    # 2. View works
    v1 = client.get(f"/api/v1/shared/dashboards/{token}")
    assert v1.status_code == 200

    # 3. Revoke Share
    revoke_resp = client.delete(f"/api/v1/shares/{share_id}", headers=headers)
    assert revoke_resp.status_code == 200
    assert revoke_resp.json()["is_active"] is False

    # 4. View fails immediately
    v2 = client.get(f"/api/v1/shared/dashboards/{token}")
    assert v2.status_code == 404


def test_shared_viewer_isolated_filter_refresh():
    headers, dashboard_id = setup_user_and_dashboard("share_user_filter")
    create_resp = client.post(f"/api/v1/dashboards/{dashboard_id}/shares", json={"is_snapshot": False}, headers=headers)
    token = create_resp.json()["share_token"]

    # Viewer applies temporary filter
    refresh_payload = {"filter_values": {"facility": "Facility A"}}
    filter_resp = client.post(f"/api/v1/shared/dashboards/{token}/refresh", json=refresh_payload)
    assert filter_resp.status_code == 200
    refreshed_data = filter_resp.json()
    assert "widgets" in refreshed_data


def test_sharing_security_idor_isolation():
    headers_u1, dashboard_id = setup_user_and_dashboard("share_user_idor1")
    headers_u2, _ = setup_user_and_dashboard("share_user_idor2")

    # User 1 creates share
    create_resp = client.post(f"/api/v1/dashboards/{dashboard_id}/shares", json={}, headers=headers_u1)
    share_id = create_resp.json()["id"]

    # User 2 cannot list or delete User 1's share
    u2_list = client.get(f"/api/v1/dashboards/{dashboard_id}/shares", headers=headers_u2)
    assert u2_list.status_code == 200
    assert len(u2_list.json()) == 0  # No shares visible to user 2 for this dashboard

    u2_revoke = client.delete(f"/api/v1/shares/{share_id}", headers=headers_u2)
    assert u2_revoke.status_code == 404
