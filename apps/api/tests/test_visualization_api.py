"""Integration tests for the Visualization API endpoints."""

import io

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_list_chart_types():
    """Verify listing all registered chart types and constraints."""
    # Register & Login User
    email = "viz_user@example.com"
    client.post("/api/v1/auth/register", json={"email": email, "password": "Password123!", "full_name": "Viz User"})
    login_resp = client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"})
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get("/api/v1/visualizations/charts", headers=headers)
    assert resp.status_code == 200
    charts = resp.json()
    assert len(charts) >= 10
    chart_types = [c["chart_type"] for c in charts]
    assert "bar" in chart_types
    assert "line" in chart_types
    assert "kpi" in chart_types
    assert "table" in chart_types


def test_recommend_and_validate_visualization():
    """Verify recommendation and validation flow on an executed analysis."""
    # Register & Login User
    email = "viz_analyst@example.com"
    client.post("/api/v1/auth/register", json={"email": email, "password": "Password123!", "full_name": "Analyst"})
    login_resp = client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"})
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Upload Dataset
    csv_content = b"region,revenue\nNorth,1000\nSouth,1500\nEast,800\nWest,1200\n"
    up_resp = client.post(
        "/api/v1/datasets",
        files={"file": ("sales.csv", io.BytesIO(csv_content), "text/csv")},
        data={"name": "Sales Dataset"},
        headers=headers,
    )
    assert up_resp.status_code == 201
    ds_data = up_resp.json()
    dataset_id = ds_data["id"]
    version_id = ds_data["latest_version"]["id"]

    # Run Analysis (Group By)
    analysis_resp = client.post(
        "/api/v1/analytics/run",
        json={
            "dataset_id": dataset_id,
            "dataset_version_id": version_id,
            "operation": "group_by",
            "parameters": {
                "dimensions": ["region"],
                "aggregations": [{"column": "revenue", "agg_type": "SUM", "alias": "total_revenue"}],
            },
        },
        headers=headers,
    )
    assert analysis_resp.status_code == 200
    analysis_id = analysis_resp.json()["analysis_id"]

    # Request Recommendation
    rec_resp = client.post(
        "/api/v1/visualizations/recommend",
        json={"analysis_id": analysis_id},
        headers=headers,
    )
    assert rec_resp.status_code == 200
    spec = rec_resp.json()
    assert spec["chart_type"] in ("donut", "pie", "bar")
    assert spec["x_axis"] == "region"
    assert spec["y_axis"] == "total_revenue"
    assert spec["provenance"]["analysis_id"] == analysis_id

    # Validate the Spec
    val_resp = client.post(
        "/api/v1/visualizations/validate",
        json={"analysis_id": analysis_id, "spec": spec},
        headers=headers,
    )
    assert val_resp.status_code == 200
    val_data = val_resp.json()
    assert val_data["valid"] is True
    assert len(val_data["errors"]) == 0


def test_visualization_unauthorized_cross_tenant_access():
    """Verify that User B cannot access or recommend visualizations for User A's analysis."""
    # User A creates analysis
    client.post(
        "/api/v1/auth/register",
        json={"email": "usera_viz@example.com", "password": "Password123!", "full_name": "User A"},
    )
    login_a = client.post("/api/v1/auth/login", json={"email": "usera_viz@example.com", "password": "Password123!"})
    token_a = login_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    csv_content = b"region,revenue\nNorth,1000\nSouth,1500\n"
    up_resp = client.post(
        "/api/v1/datasets",
        files={"file": ("sales_a.csv", io.BytesIO(csv_content), "text/csv")},
        data={"name": "Sales A"},
        headers=headers_a,
    )
    assert up_resp.status_code == 201
    ds_data = up_resp.json()
    an_resp = client.post(
        "/api/v1/analytics/run",
        json={
            "dataset_id": ds_data["id"],
            "dataset_version_id": ds_data["latest_version"]["id"],
            "operation": "group_by",
            "parameters": {
                "dimensions": ["region"],
                "aggregations": [{"column": "revenue", "agg_type": "SUM", "alias": "total_revenue"}],
            },
        },
        headers=headers_a,
    )
    assert an_resp.status_code == 200
    analysis_id = an_resp.json()["analysis_id"]

    # User B tries to recommend on User A's analysis
    client.post(
        "/api/v1/auth/register",
        json={"email": "userb_viz@example.com", "password": "Password123!", "full_name": "User B"},
    )
    login_b = client.post("/api/v1/auth/login", json={"email": "userb_viz@example.com", "password": "Password123!"})
    token_b = login_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    rec_resp = client.post(
        "/api/v1/visualizations/recommend",
        json={"analysis_id": analysis_id},
        headers=headers_b,
    )
    assert rec_resp.status_code == 404
