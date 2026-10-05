"""Unit and Integration tests for Phase 10 Multi-Dataset Intelligence and Federation."""

import io

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@pytest.fixture
def auth_header():
    email = "fed_user@example.com"
    pwd = "Password123!"
    client.post("/api/v1/auth/register", json={"email": email, "password": pwd, "full_name": "Fed User"})
    login = client.post("/api/v1/auth/login", json={"email": email, "password": pwd})
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def customer_dataset(auth_header):
    csv_data = (
        b"customer_id,name,segment,city\n"
        b"C1,Alice,Enterprise,Peshawar\n"
        b"C2,Bob,SMB,Islamabad\n"
        b"C3,Charlie,Enterprise,Lahore\n"
        b"C4,David,Consumer,Karachi\n"
    )
    files = {"file": ("customers.csv", io.BytesIO(csv_data), "text/csv")}
    res = client.post("/api/v1/datasets", headers=auth_header, files=files, data={"name": "Customers"})
    assert res.status_code == 201
    return res.json()


@pytest.fixture
def orders_dataset(auth_header):
    csv_data = (
        b"order_id,customer_id,product_id,revenue\n"
        b"O101,C1,P1,500.0\n"
        b"O102,C1,P2,250.0\n"
        b"O103,C2,P1,150.0\n"
        b"O104,C3,P2,1000.0\n"
    )
    files = {"file": ("orders.csv", io.BytesIO(csv_data), "text/csv")}
    res = client.post("/api/v1/datasets", headers=auth_header, files=files, data={"name": "Orders"})
    assert res.status_code == 201
    return res.json()


@pytest.fixture
def products_dataset(auth_header):
    csv_data = (
        b"product_id,product_name,category,unit_cost\n"
        b"P1,Analytics Suite,Software,100.0\n"
        b"P2,Data Pipeline,Infrastructure,200.0\n"
        b"P3,Cloud Storage,Storage,50.0\n"
    )
    files = {"file": ("products.csv", io.BytesIO(csv_data), "text/csv")}
    res = client.post("/api/v1/datasets", headers=auth_header, files=files, data={"name": "Products"})
    assert res.status_code == 201
    return res.json()



def test_collection_lifecycle(auth_header, customer_dataset, orders_dataset):
    """Test creating, fetching, updating, and deleting a dataset collection."""
    # 1. Create collection
    create_res = client.post(
        "/api/v1/collections",
        headers=auth_header,
        json={
            "name": "Sales Analytics Collection",
            "description": "Cross-functional sales and customer data",
            "dataset_ids": [customer_dataset["id"], orders_dataset["id"]],
        },
    )
    assert create_res.status_code == 201
    collection = create_res.json()
    assert collection["name"] == "Sales Analytics Collection"
    assert len(collection["items"]) == 2

    # 2. List collections
    list_res = client.get("/api/v1/collections", headers=auth_header)
    assert list_res.status_code == 200
    assert list_res.json()["total"] >= 1

    # 3. Get single collection
    get_res = client.get(f"/api/v1/collections/{collection['id']}", headers=auth_header)
    assert get_res.status_code == 200
    assert get_res.json()["id"] == collection["id"]

    # 4. Remove dataset
    del_item_res = client.delete(
        f"/api/v1/collections/{collection['id']}/datasets/{orders_dataset['id']}",
        headers=auth_header,
    )
    assert del_item_res.status_code == 200
    assert len(del_item_res.json()["items"]) == 1

    # 5. Delete collection
    del_res = client.delete(f"/api/v1/collections/{collection['id']}", headers=auth_header)
    assert del_res.status_code == 204


def test_relationship_discovery_and_validation(auth_header, customer_dataset, orders_dataset):
    """Test candidate relationship discovery and DuckDB validation."""
    # Profile both datasets first
    client.post(
        f"/api/v1/datasets/{customer_dataset['id']}/versions/{customer_dataset['latest_version']['id']}/profile",
        headers=auth_header,
    )
    client.post(
        f"/api/v1/datasets/{orders_dataset['id']}/versions/{orders_dataset['latest_version']['id']}/profile",
        headers=auth_header,
    )

    # 1. Create collection
    col_res = client.post(
        "/api/v1/collections",
        headers=auth_header,
        json={
            "name": "E-Commerce Collection",
            "dataset_ids": [customer_dataset["id"], orders_dataset["id"]],
        },
    )
    col_id = col_res.json()["id"]

    # 2. Discover candidate relationships
    disc_res = client.post(f"/api/v1/collections/{col_id}/discover-relationships", headers=auth_header)
    assert disc_res.status_code == 200
    cands = disc_res.json()["candidates"]
    assert len(cands) >= 1
    cand = cands[0]
    assert cand["source_field"] == "customer_id" or cand["target_field"] == "customer_id"

    # 3. Propose relationship Customers.customer_id -> Orders.customer_id
    prop_res = client.post(
        "/api/v1/relationships",
        headers=auth_header,
        json={
            "collection_id": col_id,
            "source_dataset_id": customer_dataset["id"],
            "source_version_id": customer_dataset["latest_version"]["id"],
            "source_field": "customer_id",
            "target_dataset_id": orders_dataset["id"],
            "target_version_id": orders_dataset["latest_version"]["id"],
            "target_field": "customer_id",
        },
    )
    assert prop_res.status_code == 201
    rel = prop_res.json()
    assert rel["status"] == "VALIDATED"
    assert rel["coverage_ratio"] > 0.0
    assert rel["quality_score"] > 50.0

    # 4. Update status
    patch_res = client.patch(
        f"/api/v1/relationships/{rel['id']}/status",
        headers=auth_header,
        json={"status": "DISABLED"},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "DISABLED"


def test_two_dataset_federated_analysis(auth_header, customer_dataset, orders_dataset):
    """Test calculating revenue by customer segment across Customers and Orders."""
    # Create validated relationship
    client.post(
        "/api/v1/relationships",
        headers=auth_header,
        json={
            "source_dataset_id": customer_dataset["id"],
            "source_version_id": customer_dataset["latest_version"]["id"],
            "source_field": "customer_id",
            "target_dataset_id": orders_dataset["id"],
            "target_version_id": orders_dataset["latest_version"]["id"],
            "target_field": "customer_id",
        },
    )

    # Execute federated query: Revenue by Customer Segment
    fed_res = client.post(
        "/api/v1/federation/analyze",
        headers=auth_header,
        json={
            "dataset_version_ids": [
                customer_dataset["latest_version"]["id"],
                orders_dataset["latest_version"]["id"],
            ],
            "dimensions": ["Customers.segment"],
            "measures": [{"field": "Orders.revenue", "agg": "SUM", "alias": "total_revenue"}],
        },
    )
    assert fed_res.status_code == 200
    data = fed_res.json()
    assert data["row_count"] >= 1
    assert "total_revenue" in data["columns"]

    # Mathematical verification:
    # Enterprise (C1: 500+250 = 750, C3: 1000) -> 1750.0
    # SMB (C2: 150) -> 150.0
    rows = data["rows"]
    enterprise_row = next((r for r in rows if r.get("Customers_segment") == "Enterprise"), None)
    assert enterprise_row is not None
    assert float(enterprise_row["total_revenue"]) == 1750.0


def test_three_dataset_multihop_federation(auth_header, customer_dataset, orders_dataset, products_dataset):
    """Test multi-hop join: Customers -> Orders -> Products."""
    # 1. Customers <-> Orders
    client.post(
        "/api/v1/relationships",
        headers=auth_header,
        json={
            "source_dataset_id": customer_dataset["id"],
            "source_version_id": customer_dataset["latest_version"]["id"],
            "source_field": "customer_id",
            "target_dataset_id": orders_dataset["id"],
            "target_version_id": orders_dataset["latest_version"]["id"],
            "target_field": "customer_id",
        },
    )

    # 2. Orders <-> Products
    client.post(
        "/api/v1/relationships",
        headers=auth_header,
        json={
            "source_dataset_id": orders_dataset["id"],
            "source_version_id": orders_dataset["latest_version"]["id"],
            "source_field": "product_id",
            "target_dataset_id": products_dataset["id"],
            "target_version_id": products_dataset["latest_version"]["id"],
            "target_field": "product_id",
        },
    )

    # Execute 3-dataset query: Revenue by Product Category & Customer Segment
    fed_res = client.post(
        "/api/v1/federation/analyze",
        headers=auth_header,
        json={
            "dataset_version_ids": [
                customer_dataset["latest_version"]["id"],
                orders_dataset["latest_version"]["id"],
                products_dataset["latest_version"]["id"],
            ],
            "dimensions": ["Customers.segment", "Products.category"],
            "measures": [{"field": "Orders.revenue", "agg": "SUM", "alias": "category_revenue"}],
        },
    )
    assert fed_res.status_code == 200
    data = fed_res.json()
    assert data["row_count"] >= 1
    assert len(data["relationships_used"]) == 2


def test_idor_and_unauthorized_dataset_isolation(auth_header, customer_dataset):
    """Test that User B cannot access or create relationships with User A's private datasets."""
    email_b = "user_b@example.com"
    pwd_b = "SecurePassword123!"
    client.post(
        "/api/v1/auth/register",
        json={"email": email_b, "password": pwd_b, "full_name": "User B"},
    )
    user_b_token = client.post(
        "/api/v1/auth/login",
        json={"email": email_b, "password": pwd_b},
    ).json()["access_token"]
    user_b_header = {"Authorization": f"Bearer {user_b_token}"}

    # User B attempts to access User A's collection
    res = client.post(
        "/api/v1/collections",
        headers=user_b_header,
        json={"name": "Attacker Collection", "dataset_ids": [customer_dataset["id"]]},
    )
    assert res.status_code == 201
    assert len(res.json()["items"]) == 0  # User A's dataset was rejected and not included

    # User B attempts to execute federated analysis on User A's dataset
    fed_res = client.post(
        "/api/v1/federation/analyze",
        headers=user_b_header,
        json={
            "dataset_version_ids": [customer_dataset["latest_version"]["id"]],
            "dimensions": ["Customers.segment"],
            "measures": [{"field": "revenue", "agg": "SUM"}],
        },
    )
    assert fed_res.status_code in [400, 403, 404]
