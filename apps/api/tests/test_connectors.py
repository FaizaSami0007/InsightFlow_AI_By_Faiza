"""Unit and integration tests for Phase 17 Enterprise Data Connectors & Ingestion."""

import json
import sqlite3
import uuid

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient

from app.connectors.database import SQLiteConnector
from app.connectors.drift_engine import ConnectorDriftEngine, FreshnessEngine
from app.connectors.registry import ConnectorRegistry
from app.connectors.schemas import (
    ResourceColumnSpec,
    ResourceSpec,
)
from app.connectors.secrets import SecretProvider
from app.connectors.security import SQLSafetyValidator, SSRFGuard, SSRFSecurityError
from app.database.models.connectors import (
    ConnectorType,
    SyncJobStatus,
    SyncType,
)
from app.database.models.user import User
from tests.conftest import TestingSessionLocal

# ==============================================================================
# 1. UNIT TESTS: SECRET PROVIDER
# ==============================================================================


def test_secret_provider_encrypt_decrypt():
    provider = SecretProvider()
    raw_creds = {"password": "SuperSecretPassword123!", "api_key": "sk_live_abcdef12345"}
    encrypted = provider.encrypt(raw_creds)

    assert encrypted != json.dumps(raw_creds)
    assert isinstance(encrypted, str)

    decrypted = provider.decrypt(encrypted)
    assert decrypted == raw_creds
    assert decrypted["password"] == "SuperSecretPassword123!"


def test_secret_provider_mask_credentials():
    raw_creds = {
        "host": "db.production.internal",
        "port": 5432,
        "database": "analytics",
        "username": "admin_user",
        "password": "SuperSecretPassword123!",
        "api_key": "sk-1234567890abcdef",
        "client_secret": "my-secret-key",
    }
    masked = SecretProvider.mask_credentials(raw_creds)
    assert masked["host"] == "db.production.internal"
    assert masked["port"] == 5432
    assert masked["database"] == "analytics"
    assert masked["username"] == "admin_user"
    assert masked["password"] == "********"
    assert masked["api_key"] == "********"
    assert masked["client_secret"] == "********"


# ==============================================================================
# 2. UNIT TESTS: SSRF GUARD
# ==============================================================================


def test_ssrf_guard_blocks_private_networks():
    blocked_urls = [
        "http://127.0.0.1:8080/api/v1/data",
        "http://localhost:5000/metrics",
        "http://10.0.0.1/internal/admin",
        "http://172.16.0.5/api",
        "http://192.168.1.1/router",
        "http://169.254.169.254/latest/meta-data/",
        "http://0.0.0.0:8000/secrets",
    ]
    for url in blocked_urls:
        is_safe, reason = SSRFGuard.validate_url(url)
        assert is_safe is False, f"URL should be blocked: {url}"
        assert reason is not None


def test_ssrf_guard_blocks_dangerous_schemes():
    blocked_schemes = [
        "file:///etc/passwd",
        "ftp://internal.server/data.csv",
        "gopher://localhost:70/",
        "dict://localhost:2628/",
    ]
    for url in blocked_schemes:
        is_safe, reason = SSRFGuard.validate_url(url)
        assert is_safe is False, f"Scheme should be blocked: {url}"


def test_ssrf_guard_allows_public_urls():
    allowed_urls = [
        "https://api.github.com/repos/insightflow/data",
        "https://jsonplaceholder.typicode.com/posts",
        "https://api.stripe.com/v1/charges",
    ]
    for url in allowed_urls:
        is_safe, reason = SSRFGuard.validate_url(url)
        assert is_safe is True, f"Public URL should be allowed: {url}"


def test_ssrf_guard_assert_safe_raises():
    with pytest.raises(SSRFSecurityError):
        SSRFGuard.enforce_safe_url("http://169.254.169.254/latest/meta-data/")


# ==============================================================================
# 3. UNIT TESTS: SQL SAFETY VALIDATOR
# ==============================================================================


def test_sql_safety_validator_blocks_dml_and_ddl():
    dangerous_queries = [
        "DROP TABLE users;",
        "DELETE FROM orders WHERE id > 0;",
        "UPDATE accounts SET balance = 1000000;",
        "INSERT INTO audit_log VALUES ('evil');",
        "ALTER TABLE customers DROP COLUMN email;",
        "TRUNCATE TABLE transactions;",
        "GRANT ALL PRIVILEGES ON *.* TO 'hacker';",
        "REVOKE SELECT ON users FROM 'analyst';",
        "EXEC xp_cmdshell('dir');",
    ]
    for query in dangerous_queries:
        is_safe, reason = SQLSafetyValidator.validate_sql(query)
        assert is_safe is False, f"Query should be blocked: {query}"


def test_sql_safety_validator_blocks_multi_statements():
    query = "SELECT * FROM sales; DROP TABLE sales;"
    is_safe, reason = SQLSafetyValidator.validate_sql(query)
    assert is_safe is False
    assert "Multiple SQL statements" in reason


def test_sql_safety_validator_allows_readonly_queries():
    safe_queries = [
        "SELECT id, name, revenue FROM customers WHERE revenue > 1000",
        "SELECT dept, AVG(salary) FROM employees GROUP BY dept ORDER BY 2 DESC",
        "WITH monthly_sales AS (SELECT date_trunc('month', created_at) as m, sum(amount) as total FROM sales GROUP BY 1) SELECT * FROM monthly_sales",
        "EXPLAIN SELECT * FROM inventory",
    ]
    for query in safe_queries:
        is_safe, reason = SQLSafetyValidator.validate_sql(query)
        assert is_safe is True, f"Safe query was rejected: {query} (Reason: {reason})"


# ==============================================================================
# 4. UNIT TESTS: CONNECTOR REGISTRY
# ==============================================================================


def test_connector_registry_catalog():
    catalog_resp = ConnectorRegistry.get_catalog()
    assert catalog_resp.total >= 6
    types = [item.connector_type.value for item in catalog_resp.items]
    assert ConnectorType.POSTGRESQL.value in types
    assert ConnectorType.MYSQL.value in types
    assert ConnectorType.SQLITE.value in types
    assert ConnectorType.REST_API.value in types
    assert ConnectorType.OBJECT_STORAGE.value in types
    assert ConnectorType.GOOGLE_SHEETS.value in types


def test_connector_registry_factory():
    connector = ConnectorRegistry.create_connector(
        connector_type=ConnectorType.SQLITE,
        configuration={"database_path": ":memory:"},
        credentials={},
    )
    assert isinstance(connector, SQLiteConnector)


# ==============================================================================
# 5. INTEGRATION TESTS: SQLITE CONNECTOR
# ==============================================================================


@pytest.fixture
def sample_sqlite_db(temp_storage_dir):
    db_path = f"{temp_storage_dir}/sample_test.db"
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE customers (
            customer_id INTEGER PRIMARY KEY,
            company_name TEXT NOT NULL,
            annual_revenue REAL,
            is_active INTEGER
        )
    """)
    cur.execute("""
        CREATE TABLE orders (
            order_id INTEGER PRIMARY KEY,
            customer_id INTEGER,
            order_amount REAL,
            order_date TEXT
        )
    """)
    for i in range(1, 21):
        cur.execute(
            "INSERT INTO customers VALUES (?, ?, ?, ?)",
            (i, f"Company {i}", i * 15000.5, 1 if i % 2 == 0 else 0),
        )
    conn.commit()
    conn.close()
    return db_path


@pytest.mark.asyncio
async def test_sqlite_connector_lifecycle(sample_sqlite_db):
    connector = SQLiteConnector(
        configuration={"database_path": sample_sqlite_db},
        credentials={},
    )

    # 1. Test Connection
    test_res = await connector.validate_connection()
    assert test_res.success is True
    assert test_res.latency_ms is not None

    # 2. Discover Schema
    schema = await connector.discover_schema()
    assert len(schema) == 2
    table_names = [t.name for t in schema]
    assert "customers" in table_names
    assert "orders" in table_names

    customers_table = next(t for t in schema if t.name == "customers")
    col_names = [c.name for c in customers_table.columns]
    assert "customer_id" in col_names
    assert "company_name" in col_names
    assert "annual_revenue" in col_names

    # 3. Preview Resource
    preview = await connector.preview("customers", limit=5)
    assert preview.total_preview_rows == 5
    assert len(preview.columns) == 4
    assert len(preview.rows) == 5
    assert preview.rows[0]["company_name"] == "Company 1"

    # 4. Ingest Records
    records, metadata = await connector.ingest("customers", sync_type=SyncType.FULL_SYNC)
    assert len(records) == 20
    assert metadata["rows_extracted"] == 20
    assert "annual_revenue" in records[0]


# ==============================================================================
# 6. UNIT TESTS: SCHEMA DRIFT & FRESHNESS ENGINE
# ==============================================================================


def test_drift_engine_detects_changes():
    old_schema = [
        ResourceSpec(
            resource_id="users",
            name="users",
            resource_type="TABLE",
            columns=[
                ResourceColumnSpec(name="id", data_type="INTEGER", nullable=False, is_primary_key=True),
                ResourceColumnSpec(name="email", data_type="VARCHAR", nullable=False),
                ResourceColumnSpec(name="old_column", data_type="TEXT", nullable=True),
            ],
        )
    ]
    new_schema = [
        ResourceSpec(
            resource_id="users",
            name="users",
            resource_type="TABLE",
            columns=[
                ResourceColumnSpec(name="id", data_type="BIGINT", nullable=False, is_primary_key=True),  # Type changed
                ResourceColumnSpec(name="email", data_type="VARCHAR", nullable=False),
                ResourceColumnSpec(name="new_column", data_type="FLOAT", nullable=True),  # Added
                # old_column removed
            ],
        ),
        ResourceSpec(
            resource_id="new_table",
            name="new_table",
            resource_type="TABLE",
            columns=[ResourceColumnSpec(name="id", data_type="INTEGER", nullable=False)],
        ),
    ]

    drift_report = ConnectorDriftEngine.detect_drift(old_schema, new_schema)
    assert drift_report.has_drift is True
    assert "users.new_column" in drift_report.added_columns
    assert "users.old_column" in drift_report.removed_columns
    assert "users.id" in drift_report.type_changes


def test_freshness_engine_scoring():
    from datetime import datetime, timedelta, timezone

    now = datetime.now(timezone.utc)

    # Very fresh (< 1h)
    f1_status, f1_score, f1_recs = FreshnessEngine.assess_freshness(
        now - timedelta(minutes=15),
        sync_schedule="0 */24 * * *",
    )
    assert f1_status == "FRESH"
    assert f1_score >= 90.0

    # Stale (> 48h)
    f2_status, f2_score, f2_recs = FreshnessEngine.assess_freshness(
        now - timedelta(hours=50),
        sync_schedule="0 */24 * * *",
    )
    assert f2_status == "OVERDUE" or f2_status == "STALE"


# ==============================================================================
# 7. INTEGRATION TESTS: FASTAPI CONNECTOR ENDPOINTS & IDOR
# ==============================================================================


@pytest_asyncio.fixture
async def auth_user_a() -> User:
    async with TestingSessionLocal() as session:
        user = User(
            id=str(uuid.uuid4()),
            email="tenant_a@insightflow.ai",
            password_hash="hashed_pw_tenant_a",
            full_name="Tenant A Admin",
            is_active=True,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


@pytest_asyncio.fixture
async def auth_user_b() -> User:
    async with TestingSessionLocal() as session:
        user = User(
            id=str(uuid.uuid4()),
            email="tenant_b@insightflow.ai",
            password_hash="hashed_pw_tenant_b",
            full_name="Tenant B Admin",
            is_active=True,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


def test_connector_api_lifecycle(client: TestClient, auth_user_a: User, auth_user_b: User, sample_sqlite_db: str):
    from app.main import app
    from app.users.dependencies import get_current_user

    # Override current user as Tenant A
    app.dependency_overrides[get_current_user] = lambda: auth_user_a

    # 1. Get Catalog
    catalog_res = client.get("/api/v1/connectors/catalog")
    assert catalog_res.status_code == 200
    catalog = catalog_res.json()
    assert catalog["total"] >= 6

    # 2. Test Direct Connection (without saving)
    test_payload = {
        "connector_type": "sqlite",
        "configuration": {"database_path": sample_sqlite_db},
        "credentials": {},
    }
    test_res = client.post("/api/v1/connectors/test-direct", json=test_payload)
    assert test_res.status_code == 200
    assert test_res.json()["success"] is True

    # 3. Create Connection for Tenant A
    create_payload = {
        "name": "Production SQLite Source",
        "description": "Primary analytics source",
        "connector_type": "sqlite",
        "configuration": {"database_path": sample_sqlite_db},
        "credentials": {},
        "sync_schedule": "0 */12 * * *",
    }
    create_res = client.post("/api/v1/connectors/connections", json=create_payload)
    assert create_res.status_code == 201
    conn_data = create_res.json()
    connection_id = conn_data["id"]
    assert conn_data["name"] == "Production SQLite Source"

    # 4. Discover Schema via API
    schema_res = client.post(f"/api/v1/connectors/connections/{connection_id}/discover")
    assert schema_res.status_code == 200
    schema_data = schema_res.json()
    assert len(schema_data["resources"]) == 2

    # 5. Preview Resource via API
    preview_payload = {"resource_id": "customers", "row_limit": 10}
    preview_res = client.post(f"/api/v1/connectors/connections/{connection_id}/preview", json=preview_payload)
    assert preview_res.status_code == 200
    preview_data = preview_res.json()
    assert preview_data["total_preview_rows"] == 10
    assert len(preview_data["rows"]) == 10

    # 6. Trigger Ingestion Sync Job
    sync_payload = {
        "source_resource": "customers",
        "sync_type": "FULL_SYNC",
        "dataset_name": "Synced Customers Warehouse",
    }
    sync_res = client.post(f"/api/v1/connectors/connections/{connection_id}/sync", json=sync_payload)
    assert sync_res.status_code == 201
    sync_job = sync_res.json()
    assert sync_job["status"] == SyncJobStatus.COMPLETED.value
    assert sync_job["rows_processed"] == 20
    assert sync_job["dataset_id"] is not None

    # 7. Check Drift
    drift_res = client.get(f"/api/v1/connectors/connections/{connection_id}/drift")
    assert drift_res.status_code == 200

    # 8. Check Health
    health_res = client.get(f"/api/v1/connectors/connections/{connection_id}/health")
    assert health_res.status_code == 200

    # 9. Check IDOR isolation: Tenant B cannot access Tenant A's connection
    app.dependency_overrides[get_current_user] = lambda: auth_user_b
    idor_res = client.get(f"/api/v1/connectors/connections/{connection_id}")
    assert idor_res.status_code == 404

    idor_sync_res = client.post(f"/api/v1/connectors/connections/{connection_id}/sync", json=sync_payload)
    assert idor_sync_res.status_code == 404

    # Cleanup dependency overrides
    app.dependency_overrides.pop(get_current_user, None)
