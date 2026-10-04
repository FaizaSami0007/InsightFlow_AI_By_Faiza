import os
import tempfile

import pytest

from app.analytics.duckdb.dataset import AnalyticalDataset
from app.analytics.duckdb.manager import DuckDBManager, DuckDBSecurityError


def test_duckdb_registration_and_query():
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".csv", delete=False) as f:
        f.write("region,sales,quantity\nNorth,500.0,5\nNorth,300.0,3\nSouth,200.0,2\n")
        f.flush()
        file_path = f.name

    try:
        manager = DuckDBManager()
        version_id = "test-version-uuid-123"
        manager.register_dataset(version_id, file_path, "CSV")
        assert manager.is_registered(version_id)

        # Basic SELECT
        res = manager.execute_query(version_id, "SELECT region, SUM(sales) as total_sales FROM dataset GROUP BY region ORDER BY total_sales DESC")
        assert res["columns"] == ["region", "total_sales"]
        assert len(res["rows"]) == 2
        assert res["rows"][0][0] == "North"
        assert res["rows"][0][1] == 800.0

        # Explain query
        plan = manager.explain_query(version_id, "SELECT * FROM dataset WHERE sales > 250")
        assert "FILTER" in plan or "sales" in plan or len(plan) > 0

        # Clean unregister
        manager.unregister_dataset(version_id)
        assert not manager.is_registered(version_id)
    finally:
        os.remove(file_path)


def test_duckdb_security_rejections():
    manager = DuckDBManager()

    # Non-SELECT statements
    with pytest.raises(DuckDBSecurityError):
        manager.validate_query_safety("DROP TABLE users")

    with pytest.raises(DuckDBSecurityError):
        manager.validate_query_safety("DELETE FROM dataset WHERE 1=1")

    with pytest.raises(DuckDBSecurityError):
        manager.validate_query_safety("INSERT INTO dataset VALUES ('East', 100, 1)")

    with pytest.raises(DuckDBSecurityError):
        manager.validate_query_safety("ATTACH 'evil.db' AS evil")

    with pytest.raises(DuckDBSecurityError):
        manager.validate_query_safety("PRAGMA version")

    # Multi-statement injection attempt
    with pytest.raises(DuckDBSecurityError):
        manager.validate_query_safety("SELECT * FROM dataset; DROP TABLE datasets")


def test_analytical_dataset_wrapper():
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".csv", delete=False) as f:
        f.write("id,value\n1,10\n2,20\n3,30\n")
        f.flush()
        file_path = f.name

    try:
        ds = AnalyticalDataset(
            dataset_id="ds-1",
            version_id="ver-1",
            file_path=file_path,
            file_format="CSV",
        )
        res = ds.query("SELECT AVG(value) as avg_val FROM data")
        assert res["rows"][0][0] == 20.0
        ds.close()
    finally:
        os.remove(file_path)
