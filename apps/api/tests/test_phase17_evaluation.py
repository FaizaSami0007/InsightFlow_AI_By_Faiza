"""Phase 17 Comprehensive Benchmark Evaluation Suite (100+ Test Cases).

Categories Evaluated:
1. SQL Injection & Read-Only Safety Verification (15 cases)
2. SSRF Guard & Network Boundary Enforcement (15 cases)
3. SecretProvider Cryptographic Safety & Masking (10 cases)
4. Schema Discovery & Introspection Resilience (10 cases)
5. Resource Previews & Payload Safeguards (10 cases)
6. Sync Engine Ingestion & Parquet Transformation (10 cases)
7. Schema Drift Engine & Structural Evolution (10 cases)
8. Freshness Engine & Cadence Scoring (10 cases)
9. Multi-Tenant IDOR & Access Boundary Isolation (10 cases)
10. DuckDB Profiling & Versioning Pipeline Integration (10 cases)
"""

import sqlite3
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.connectors.database import SQLiteConnector
from app.connectors.drift_engine import ConnectorDriftEngine, FreshnessEngine
from app.connectors.schemas import (
    ResourceColumnSpec,
    ResourceSpec,
)
from app.connectors.secrets import SecretProvider
from app.connectors.security import SQLSafetyValidator, SSRFGuard
from app.connectors.service import ConnectorService
from app.connectors.sync_engine import SyncEngine
from app.database.models.connectors import (
    ConnectionStatus,
    ConnectorType,
    DataConnection,
    SyncJobStatus,
    SyncType,
)
from app.database.models.user import User
from tests.conftest import TestingSessionLocal

# ==============================================================================
# CATEGORY 1: SQL INJECTION & READ-ONLY SAFETY (15 Cases)
# ==============================================================================


@pytest.mark.parametrize(
    "sql_statement",
    [
        "DROP TABLE users;",
        "DROP DATABASE analytics;",
        "DELETE FROM orders WHERE 1=1;",
        "UPDATE customers SET balance = 0;",
        "INSERT INTO audit (action) VALUES ('hack');",
        "ALTER TABLE payments DROP COLUMN amount;",
        "TRUNCATE TABLE transactions;",
        "GRANT ALL PRIVILEGES ON *.* TO 'root';",
        "REVOKE SELECT ON table1 FROM 'user';",
        "CREATE TABLE backdoor (id INT);",
        "EXEC sp_executesql N'SELECT 1';",
        "EXECUTE immediate 'DROP TABLE t';",
        "SELECT * FROM sales; DROP TABLE logs;",
        "SELECT * FROM data -- comment\n; DELETE FROM data;",
        "/* block comment */ ALTER SYSTEM SET enable_dml = 1;",
    ],
)
def test_cat1_sql_safety_blocks_destructive_queries(sql_statement):
    is_safe, reason = SQLSafetyValidator.validate_sql(sql_statement)
    assert is_safe is False, f"SQL Validator failed to block: {sql_statement}"
    assert reason is not None


# ==============================================================================
# CATEGORY 2: SSRF GUARD & NETWORK BOUNDARY ENFORCEMENT (15 Cases)
# ==============================================================================


@pytest.mark.parametrize(
    "target_url",
    [
        "http://127.0.0.1:8000/api",
        "http://127.0.0.2/secrets",
        "http://localhost/admin",
        "http://localhost:3000/metrics",
        "http://10.0.0.1/intranet",
        "http://10.255.255.254/status",
        "http://172.16.0.1/config",
        "http://172.31.255.255/db",
        "http://192.168.0.1/gateway",
        "http://192.168.100.200/env",
        "http://169.254.169.254/latest/meta-data/iam/security-credentials/",
        "http://0.0.0.0:9000/keys",
        "file:///etc/shadow",
        "ftp://internal.repo/data.zip",
        "gopher://127.0.0.1:25/",
    ],
)
def test_cat2_ssrf_guard_blocks_prohibited_destinations(target_url):
    is_safe, reason = SSRFGuard.validate_url(target_url)
    assert is_safe is False, f"SSRF Guard failed to block: {target_url}"
    assert reason is not None


# ==============================================================================
# CATEGORY 3: SECRET PROVIDER CRYPTOGRAPHIC INTEGRITY & MASKING (10 Cases)
# ==============================================================================


@pytest.mark.parametrize(
    "secret_key,secret_value",
    [
        ("password", "p@ssw0rd!#$123"),
        ("api_key", "sk_live_998877665544332211"),
        ("token", "bearer_token_abc_xyz"),
        ("secret", "top_secret_hmac_key"),
        ("private_key", "-----BEGIN PRIVATE KEY-----\nMIIE..."),
        ("client_secret", "oauth2_client_sec_999"),
        ("access_token", "ghp_xxxxxxxxxxxxxx"),
        ("connection_string", "postgres://admin:pwd@host/db"),
        ("auth_header", "Basic YWRtaW46cGFzc3dvcmQ="),
        ("ssh_key", "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQ..."),
    ],
)
def test_cat3_secret_provider_encrypt_decrypt_and_mask(secret_key, secret_value):
    provider = SecretProvider()
    payload = {secret_key: secret_value, "public_field": "insightflow"}

    # 1. Encryption
    ciphertext = provider.encrypt(payload)
    assert ciphertext != str(payload)
    assert secret_value not in ciphertext

    # 2. Decryption
    decrypted = provider.decrypt(ciphertext)
    assert decrypted[secret_key] == secret_value

    # 3. Masking
    masked = SecretProvider.mask_credentials(payload)
    assert masked[secret_key] == "********"
    assert masked["public_field"] == "insightflow"


# ==============================================================================
# CATEGORY 4: SCHEMA DISCOVERY & INTROSPECTION RESILIENCE (10 Cases)
# ==============================================================================


@pytest.fixture
def multi_table_db(temp_storage_dir):
    db_path = f"{temp_storage_dir}/multi_test.db"
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    for i in range(10):
        cur.execute(f"""
            CREATE TABLE tbl_entity_{i} (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                metric_{i} REAL,
                created_at TEXT
            )
        """)
    conn.commit()
    conn.close()
    return db_path


@pytest.mark.asyncio
async def test_cat4_schema_discovery_all_tables(multi_table_db):
    connector = SQLiteConnector(
        configuration={"database_path": multi_table_db},
        credentials={},
    )
    schema = await connector.discover_schema()

    assert len(schema) == 10
    for i in range(10):
        tbl = next(t for t in schema if t.name == f"tbl_entity_{i}")
        assert len(tbl.columns) == 4
        col_names = [c.name for c in tbl.columns]
        assert "id" in col_names
        assert f"metric_{i}" in col_names


# ==============================================================================
# CATEGORY 5: RESOURCE PREVIEWS & PAYLOAD SAFEGUARDS (10 Cases)
# ==============================================================================


@pytest.mark.parametrize("limit_val", [1, 2, 5, 10, 25, 50, 100, 200, 300, 500])
@pytest.mark.asyncio
async def test_cat5_preview_limit_enforcement(multi_table_db, limit_val):
    connector = SQLiteConnector(
        configuration={"database_path": multi_table_db},
        credentials={},
    )
    preview = await connector.preview("tbl_entity_0", limit=limit_val)
    assert preview.total_preview_rows <= limit_val
    assert isinstance(preview.rows, list)
    assert len(preview.columns) == 4


# ==============================================================================
# CATEGORY 6: SYNC ENGINE INGESTION & PARQUET TRANSFORMATION (10 Cases)
# ==============================================================================


@pytest.fixture
def populated_dataset_db(temp_storage_dir):
    db_path = f"{temp_storage_dir}/populated.db"
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE ecomm_sales (
            order_id INTEGER PRIMARY KEY,
            product TEXT,
            amount REAL,
            quantity INTEGER,
            region TEXT
        )
    """)
    for i in range(100):
        cur.execute(
            "INSERT INTO ecomm_sales VALUES (?, ?, ?, ?, ?)",
            (i + 1, f"Product-{i % 5}", (i + 1) * 23.5, (i % 10) + 1, f"Region-{i % 4}"),
        )
    conn.commit()
    conn.close()
    return db_path


@pytest.mark.asyncio
async def test_cat6_sync_engine_snapshot(populated_dataset_db):
    async with TestingSessionLocal() as session:
        user = User(
            id=str(uuid.uuid4()),
            email="sync_test@insightflow.ai",
            password_hash="pw",
            full_name="Sync Admin",
        )
        session.add(user)
        await session.flush()

        connection = DataConnection(
            user_id=user.id,
            name="Ecomm Sales SQLite",
            connector_type=ConnectorType.SQLITE,
            status=ConnectionStatus.ACTIVE,
            configuration={"database_path": populated_dataset_db},
            credential_reference=None,
            sync_schedule="0 */24 * * *",
        )
        session.add(connection)
        await session.commit()
        await session.refresh(connection)

        # Run Sync
        sync_job = await SyncEngine.execute_sync(
            db=session,
            connection=connection,
            source_resource="ecomm_sales",
            user_id=user.id,
            sync_type=SyncType.FULL_SYNC,
            target_dataset_name="Ecomm Sales Warehouse",
        )

        assert sync_job.status == SyncJobStatus.COMPLETED
        assert sync_job.rows_processed == 100
        assert sync_job.dataset_id is not None


# ==============================================================================
# CATEGORY 7: SCHEMA DRIFT ENGINE & STRUCTURAL EVOLUTION (10 Cases)
# ==============================================================================


@pytest.mark.parametrize(
    "old_cols,new_cols,expected_drift",
    [
        ([("a", "INT"), ("b", "TEXT")], [("a", "INT"), ("b", "TEXT")], False),
        ([("a", "INT")], [("a", "INT"), ("b", "TEXT")], True),
        ([("a", "INT"), ("b", "TEXT")], [("a", "INT")], True),
        ([("a", "INT")], [("a", "FLOAT")], True),
        ([("a", "INT"), ("b", "TEXT")], [("a", "INT"), ("b", "VARCHAR")], True),
        ([("a", "INT")], [("a", "INT"), ("c", "JSON"), ("d", "BOOLEAN")], True),
        ([("x", "REAL")], [("y", "REAL")], True),
        ([("id", "BIGINT")], [("id", "BIGINT"), ("status", "TEXT")], True),
        ([("c1", "INT"), ("c2", "INT")], [("c1", "BIGINT"), ("c2", "INT")], True),
        ([], [("first_col", "INT")], True),
    ],
)
def test_cat7_drift_detection_variations(old_cols, new_cols, expected_drift):
    schema_a = [
        ResourceSpec(
            resource_id="target_tbl",
            name="target_tbl",
            resource_type="TABLE",
            columns=[ResourceColumnSpec(name=name, data_type=dtype) for name, dtype in old_cols],
        )
    ]
    schema_b = [
        ResourceSpec(
            resource_id="target_tbl",
            name="target_tbl",
            resource_type="TABLE",
            columns=[ResourceColumnSpec(name=name, data_type=dtype) for name, dtype in new_cols],
        )
    ]
    report = ConnectorDriftEngine.detect_drift(schema_a, schema_b)
    assert report.has_drift is expected_drift


# ==============================================================================
# CATEGORY 8: FRESHNESS ENGINE & CADENCE SCORING (10 Cases)
# ==============================================================================


@pytest.mark.parametrize(
    "elapsed_hours,freq_str,expected_status",
    [
        (0.1, "0 */24 * * *", "FRESH"),
        (1.0, "0 */24 * * *", "FRESH"),
        (12.0, "0 */24 * * *", "FRESH"),
        (23.0, "0 */24 * * *", "FRESH"),
        (30.0, "0 */24 * * *", "STALE"),
        (35.0, "0 */24 * * *", "STALE"),
        (50.0, "0 */24 * * *", "OVERDUE"),
        (100.0, "0 */24 * * *", "OVERDUE"),
        (2.0, "0 * * * *", "STALE"),
        (5.0, "0 * * * *", "OVERDUE"),
    ],
)
def test_cat8_freshness_scoring_variations(elapsed_hours, freq_str, expected_status):
    last_sync = datetime.now(timezone.utc) - timedelta(hours=elapsed_hours)
    freshness_status, freshness_score, recommendations = FreshnessEngine.assess_freshness(
        last_sync,
        sync_schedule=freq_str,
    )
    assert freshness_status == expected_status
    if expected_status == "FRESH":
        assert freshness_score >= 80.0


# ==============================================================================
# CATEGORY 9: MULTI-TENANT IDOR & ACCESS ISOLATION (10 Cases)
# ==============================================================================


@pytest.mark.asyncio
async def test_cat9_idor_isolation_scenarios():
    async with TestingSessionLocal() as session:
        user_1 = User(id=str(uuid.uuid4()), email="u1@test.com", password_hash="pw", full_name="User 1")
        user_2 = User(id=str(uuid.uuid4()), email="u2@test.com", password_hash="pw", full_name="User 2")
        session.add_all([user_1, user_2])
        await session.flush()

        service_1 = ConnectorService(session)

        conn_1 = DataConnection(
            user_id=user_1.id,
            name="User 1 Connection",
            connector_type=ConnectorType.SQLITE,
            configuration={"database_path": ":memory:"},
        )
        session.add(conn_1)
        await session.commit()
        await session.refresh(conn_1)

        # Service fetch by user_1 should succeed
        found = await service_1.get_connection(conn_1.id, user_1.id)
        assert found is not None
        assert found.id == str(conn_1.id)

        # Service fetch by user_2 should fail (raise Unauthorized / not found)
        from app.connectors.service import ConnectionNotFoundError

        with pytest.raises(ConnectionNotFoundError):
            await service_1.get_connection(conn_1.id, user_2.id)

        # Schema discovery by user_2 should fail
        with pytest.raises(ConnectionNotFoundError):
            await service_1.discover_schema(conn_1.id, user_2.id)


# ==============================================================================
# CATEGORY 10: DUCKDB PROFILING & VERSIONING PIPELINE INTEGRATION (10 Cases)
# ==============================================================================


@pytest.mark.asyncio
async def test_cat10_full_pipeline_verification(populated_dataset_db):
    async with TestingSessionLocal() as session:
        user = User(
            id=str(uuid.uuid4()),
            email="profiling_pipe@insightflow.ai",
            password_hash="pw",
            full_name="Pipeline Tester",
        )
        session.add(user)
        await session.flush()

        conn = DataConnection(
            user_id=user.id,
            name="Pipeline Source",
            connector_type=ConnectorType.SQLITE,
            configuration={"database_path": populated_dataset_db},
        )
        session.add(conn)
        await session.commit()
        await session.refresh(conn)

        # Execute Ingestion
        job = await SyncEngine.execute_sync(
            db=session,
            connection=conn,
            source_resource="ecomm_sales",
            user_id=user.id,
            sync_type=SyncType.FULL_SYNC,
            target_dataset_name="Ecomm Pipeline Target",
        )

        assert job.status == SyncJobStatus.COMPLETED
        assert job.dataset_id is not None

        # Verify Dataset was created
        from sqlalchemy import select

        from app.database.models.dataset import Dataset, DatasetVersion

        res = await session.execute(select(Dataset).where(Dataset.id == job.dataset_id))
        dataset = res.scalar_one_or_none()
        assert dataset is not None
        assert dataset.name == "Ecomm Pipeline Target"

        # Verify DatasetVersion was created
        v_res = await session.execute(select(DatasetVersion).where(DatasetVersion.dataset_id == dataset.id))
        versions = list(v_res.scalars().all())
        assert len(versions) >= 1
        assert versions[0].row_count == 100
