"""Integration tests for Dashboard Structured Patch Refinement."""

import io

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def setup_test_dashboard():
    email = "patch_user@example.com"
    client.post("/api/v1/auth/register", json={"email": email, "password": "Password123!", "full_name": "Patch User"})
    login_resp = client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"})
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    csv_data = (
        b"date,region,category,revenue,units\n"
        b"2025-01-01,North,Tech,1000,5\n"
        b"2025-01-02,South,Office,500,2\n"
        b"2025-01-03,East,Tech,800,4\n"
        b"2025-01-04,West,Furniture,600,3\n"
    )
    up_resp = client.post(
        "/api/v1/datasets",
        files={"file": ("sales_patch.csv", io.BytesIO(csv_data), "text/csv")},
        data={"name": "Patch Test Data"},
        headers=headers,
    )
    ds_data = up_resp.json()
    dataset_id = ds_data["id"]
    version_id = ds_data["latest_version"]["id"]

    client.post(f"/api/v1/datasets/{dataset_id}/versions/{version_id}/profile", headers=headers)

    gen_resp = client.post(
        "/api/v1/dashboards/generate",
        json={
            "dataset_id": dataset_id,
            "dataset_version_id": version_id,
            "purpose": "sales",
        },
        headers=headers,
    )
    return headers, dataset_id, version_id, gen_resp.json()


def test_rename_dashboard_patch():
    headers, _, _, dashboard = setup_test_dashboard()
    dash_id = dashboard["id"]

    patch_resp = client.post(
        f"/api/v1/dashboards/{dash_id}/patches",
        json={
            "patches": [
                {
                    "op": "RENAME_DASHBOARD",
                    "params": {"name": "Q1 Revenue Performance Dashboard"},
                }
            ]
        },
        headers=headers,
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["name"] == "Q1 Revenue Performance Dashboard"


def test_change_chart_patch():
    headers, _, _, dashboard = setup_test_dashboard()
    dash_id = dashboard["id"]
    # Find a chart widget
    chart_w = next(w for w in dashboard["widgets"] if w["widget_type"] == "chart")
    target_id = chart_w["id"]

    patch_resp = client.post(
        f"/api/v1/dashboards/{dash_id}/patches",
        json={
            "patches": [
                {
                    "op": "CHANGE_CHART",
                    "widget_id": target_id,
                    "params": {"chart_type": "horizontal_bar"},
                }
            ]
        },
        headers=headers,
    )
    assert patch_resp.status_code == 200
    updated_w = next(w for w in patch_resp.json()["widgets"] if w["id"] == target_id)
    assert updated_w["chart_spec"]["chart_type"] == "horizontal_bar"


def test_move_and_resize_widget_patch():
    headers, _, _, dashboard = setup_test_dashboard()
    dash_id = dashboard["id"]
    target_id = dashboard["widgets"][0]["id"]

    patch_resp = client.post(
        f"/api/v1/dashboards/{dash_id}/patches",
        json={
            "patches": [
                {
                    "op": "MOVE_WIDGET",
                    "widget_id": target_id,
                    "params": {"grid_x": 0, "grid_y": 2},
                },
                {
                    "op": "RESIZE_WIDGET",
                    "widget_id": target_id,
                    "params": {"grid_w": 12, "grid_h": 6},
                },
            ]
        },
        headers=headers,
    )
    assert patch_resp.status_code == 200
    updated_w = next(w for w in patch_resp.json()["widgets"] if w["id"] == target_id)
    assert updated_w["grid_x"] == 0
    assert updated_w["grid_y"] == 2
    assert updated_w["grid_w"] == 12
    assert updated_w["grid_h"] == 6


def test_add_and_remove_widget_patch():
    headers, dataset_id, version_id, dashboard = setup_test_dashboard()
    dash_id = dashboard["id"]
    initial_count = len(dashboard["widgets"])

    # 1. Add widget
    add_resp = client.post(
        f"/api/v1/dashboards/{dash_id}/patches",
        json={
            "patches": [
                {
                    "op": "ADD_WIDGET",
                    "params": {
                        "widget": {
                            "title": "Category Sales Volume",
                            "widget_type": "chart",
                            "operation": "group_by",
                            "params": {
                                "group_column": "category",
                                "aggregate_column": "revenue",
                                "aggregation": "sum",
                            },
                            "preferred_chart_type": "bar",
                        }
                    },
                }
            ]
        },
        headers=headers,
    )
    assert add_resp.status_code == 200
    new_dash = add_resp.json()
    assert len(new_dash["widgets"]) == initial_count + 1
    added_w = next(w for w in new_dash["widgets"] if w["title"] == "Category Sales Volume")
    assert added_w is not None

    # 2. Remove the added widget
    rem_resp = client.post(
        f"/api/v1/dashboards/{dash_id}/patches",
        json={
            "patches": [
                {
                    "op": "REMOVE_WIDGET",
                    "widget_id": added_w["id"],
                }
            ]
        },
        headers=headers,
    )
    assert rem_resp.status_code == 200
    assert len(rem_resp.json()["widgets"]) == initial_count


def test_invalid_patch_rejected():
    headers, _, _, dashboard = setup_test_dashboard()
    dash_id = dashboard["id"]

    # Attempt to move non-existent widget
    patch_resp = client.post(
        f"/api/v1/dashboards/{dash_id}/patches",
        json={
            "patches": [
                {
                    "op": "MOVE_WIDGET",
                    "widget_id": "non_existent_uuid",
                    "params": {"grid_x": 0, "grid_y": 0},
                }
            ]
        },
        headers=headers,
    )
    error_msg = patch_resp.json().get("detail") or patch_resp.json().get("error", {}).get("message", "")
    assert "Widget 'non_existent_uuid' not found" in error_msg
