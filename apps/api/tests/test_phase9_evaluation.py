"""Comprehensive Phase 9 Evaluation Benchmark Test Suite."""

import io

import pytest
from fastapi.testclient import TestClient

from app.exports.engine import sanitize_filename
from app.main import app

client = TestClient(app)


def setup_golden_dashboard(email_prefix: str):
    email = f"{email_prefix}@example.com"
    client.post("/api/v1/auth/register", json={"email": email, "password": "Password123!", "full_name": "Golden User"})
    login_resp = client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"})
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    csv_data = (
        b"month,region,category,revenue,units,quality_score\n"
        b"2026-01-01,Americas,Software,650000.0,120,99.2\n"
        b"2026-02-01,EMEA,Hardware,820000.0,180,98.5\n"
        b"2026-03-01,APAC,Services,980000.0,220,99.8\n"
        b"2026-04-01,Americas,Software,710000.0,140,99.0\n"
    )
    up_resp = client.post(
        "/api/v1/datasets",
        files={"file": ("golden_eval.csv", io.BytesIO(csv_data), "text/csv")},
        data={"name": "Golden Enterprise Suite"},
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
            "intent": "Executive Sales & Operations Overview",
        },
        headers=headers,
    )
    dash_data = gen_resp.json()
    dashboard_id = dash_data["id"]
    return headers, dashboard_id


@pytest.mark.parametrize("page_size,orientation", [
    ("A4", "landscape"),
    ("A4", "portrait"),
    ("Letter", "landscape"),
    ("Letter", "portrait"),
])
def test_evaluation_pdf_matrix(page_size: str, orientation: str):
    headers, dashboard_id = setup_golden_dashboard(f"pdf_eval_{page_size}_{orientation}")
    req = {
        "format": "pdf",
        "page_size": page_size,
        "orientation": orientation,
        "include_provenance": True,
        "include_filters": True,
        "filter_values": {"region": "Americas"},
    }
    resp = client.post(f"/api/v1/dashboards/{dashboard_id}/exports", json=req, headers=headers)
    assert resp.status_code == 201
    exp = resp.json()
    assert exp["status"] == "COMPLETED"
    assert exp["file_size_bytes"] > 1000


def test_evaluation_filename_sanitization():
    unsafe_names = [
        ("../../etc/passwd", "etcpasswd"),
        ("..\\..\\Windows\\System32", "windowssystem32"),
        ("Sales & Finance Report #1 (2026)!!", "sales-finance-report-1-2026"),
        ("   ---Leading/Trailing---   ", "leadingtrailing"),
    ]
    for unsafe, expected in unsafe_names:
        sanitized = sanitize_filename(unsafe)
        assert "/" not in sanitized
        assert "\\" not in sanitized
        assert ".." not in sanitized
        assert sanitized == expected


def test_evaluation_snapshot_immutability():
    headers, dashboard_id = setup_golden_dashboard("snap_immut_eval")
    # 1. Create snapshot share
    share_res = client.post(f"/api/v1/dashboards/{dashboard_id}/shares", json={"is_snapshot": True}, headers=headers)
    assert share_res.status_code == 201
    token = share_res.json()["share_token"]

    # 2. Modify original dashboard via update endpoint
    patch_res = client.patch(
        f"/api/v1/dashboards/{dashboard_id}",
        json={"name": "MUTATED NEW TITLE"},
        headers=headers,
    )
    assert patch_res.status_code == 200

    # 3. Verify snapshot retained original frozen state
    view_res = client.get(f"/api/v1/shared/dashboards/{token}")
    assert view_res.status_code == 200
    snap = view_res.json()
    assert snap["is_snapshot"] is True
    assert snap["title"] != "MUTATED NEW TITLE"


def test_evaluation_token_security_and_revocation():
    headers, dashboard_id = setup_golden_dashboard("token_sec_eval")
    # 1. Invalid or randomized tokens return 404
    invalid_res = client.get("/api/v1/shared/dashboards/invalid-fake-token-12345")
    assert invalid_res.status_code == 404

    # 2. Valid share creation
    share_res = client.post(f"/api/v1/dashboards/{dashboard_id}/shares", json={}, headers=headers)
    share_data = share_res.json()
    share_id = share_data["id"]
    token = share_data["share_token"]

    # 3. Access works
    v1 = client.get(f"/api/v1/shared/dashboards/{token}")
    assert v1.status_code == 200

    # 4. Revocation immediately cuts off access
    rev_res = client.post(f"/api/v1/shares/{share_id}/revoke", headers=headers)
    assert rev_res.status_code == 200

    v2 = client.get(f"/api/v1/shared/dashboards/{token}")
    assert v2.status_code == 404
