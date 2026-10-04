"""Integration tests for conversational visualization intelligence and natural language chart switching."""

import io

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_conversational_visualization_and_presentation_follow_ups():
    """Verify natural-language analytical question receives visualization, and visual follow-ups update presentation."""
    email = "chat_viz_user@example.com"
    client.post("/api/v1/auth/register", json={"email": email, "password": "Password123!", "full_name": "Chat Viz User"})
    login_resp = client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"})
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Upload Dataset
    csv_data = b"region,revenue\nNorth,1820000\nSouth,1450000\nEast,1200000\nWest,950000\n"
    up_resp = client.post(
        "/api/v1/datasets",
        files={"file": ("regional_sales.csv", io.BytesIO(csv_data), "text/csv")},
        data={"name": "Regional Sales"},
        headers=headers,
    )
    assert up_resp.status_code == 201
    dataset_info = up_resp.json()
    dataset_id = dataset_info["id"]
    version_id = dataset_info["latest_version"]["id"]

    # Step 1: Initial Analytical Query
    chat_resp1 = client.post(
        "/api/v1/ai/chat",
        json={
            "dataset_id": dataset_id,
            "dataset_version_id": version_id,
            "message": "Which region generated the highest revenue?",
        },
        headers=headers,
    )
    assert chat_resp1.status_code == 200
    data1 = chat_resp1.json()
    conv_id = data1["conversation_id"]
    assert len(data1["analysis_ids"]) >= 1
    assert data1["visualization"] is not None
    assert data1["visualization"]["chart_type"] in ("donut", "pie", "bar", "horizontal_bar")
    assert data1["visualization"]["x_axis"] in ("region", "revenue", "total_revenue")
    assert data1["visualization"]["provenance"]["dataset_id"] == dataset_id

    # Step 2: Visual Follow-up: "Make it horizontal"
    chat_resp2 = client.post(
        "/api/v1/ai/chat",
        json={
            "dataset_id": dataset_id,
            "dataset_version_id": version_id,
            "conversation_id": conv_id,
            "message": "Make it horizontal",
        },
        headers=headers,
    )
    assert chat_resp2.status_code == 200
    data2 = chat_resp2.json()
    assert "Horizontal Bar Chart" in data2["message"]
    assert data2["visualization"] is not None
    assert data2["visualization"]["chart_type"] == "horizontal_bar"

    # Step 3: Visual Follow-up: "Display it as a table"
    chat_resp3 = client.post(
        "/api/v1/ai/chat",
        json={
            "dataset_id": dataset_id,
            "dataset_version_id": version_id,
            "conversation_id": conv_id,
            "message": "Display it as a table",
        },
        headers=headers,
    )
    assert chat_resp3.status_code == 200
    data3 = chat_resp3.json()
    assert data3["visualization"] is not None
    assert data3["visualization"]["chart_type"] == "table"

    # Step 4: Visual Follow-up: "Show this as a bar chart"
    chat_resp4 = client.post(
        "/api/v1/ai/chat",
        json={
            "dataset_id": dataset_id,
            "dataset_version_id": version_id,
            "conversation_id": conv_id,
            "message": "Show this as a bar chart",
        },
        headers=headers,
    )
    assert chat_resp4.status_code == 200
    data4 = chat_resp4.json()
    assert data4["visualization"] is not None
    assert data4["visualization"]["chart_type"] == "bar"
