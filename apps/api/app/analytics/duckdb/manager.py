import re
import threading
import time
from typing import Any, Dict, List, Optional

import duckdb


class DuckDBSecurityError(Exception):
    """Raised when a query attempts prohibited destructive or unsafe SQL operations."""
    pass


class DuckDBManager:
    """Thread-safe controlled DuckDB analytical execution manager with read-only enforcement."""

    PROHIBITED_KEYWORDS = {
        r"\bCREATE\b",
        r"\bDROP\b",
        r"\bALTER\b",
        r"\bINSERT\b",
        r"\bUPDATE\b",
        r"\bDELETE\b",
        r"\bATTACH\b",
        r"\bDETACH\b",
        r"\bLOAD\b",
        r"\bINSTALL\b",
        r"\bCOPY\b",
        r"\bEXPORT\b",
        r"\bIMPORT\b",
        r"\bPRAGMA\b",
        r"\bCALL\b",
        r"\bVACUUM\b",
        r"\bSYSTEM\b",
        r"\bSET\b",
        r"\bRESET\b",
    }

    _instance: Optional["DuckDBManager"] = None
    _lock = threading.Lock()

    def __init__(self, max_result_rows: int = 1000, default_timeout_seconds: float = 10.0):
        self.max_result_rows = max_result_rows
        self.default_timeout_seconds = default_timeout_seconds
        # In-memory analytical DuckDB instance
        self._conn = duckdb.connect(database=":memory:", read_only=False)
        self._registered_tables: Dict[str, str] = {}  # version_id -> internal_table_name
        self._exec_lock = threading.Lock()

    @classmethod
    def get_instance(cls) -> "DuckDBManager":
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def _generate_table_name(self, dataset_version_id: str) -> str:
        clean_id = re.sub(r"[^a-zA-Z0-9_]", "_", dataset_version_id)
        return f"tbl_{clean_id}"

    def register_dataset(self, dataset_version_id: str, file_path: str, file_format: str) -> str:
        """Register a dataset version into DuckDB as a virtual view or table."""
        table_name = self._generate_table_name(dataset_version_id)
        clean_path = str(file_path).replace("\\", "/").replace("'", "''")
        with self._exec_lock:
            fmt = file_format.upper()
            if "PARQUET" in fmt:
                sql = f"CREATE OR REPLACE VIEW {table_name} AS SELECT * FROM read_parquet('{clean_path}')"
            else:
                sql = f"CREATE OR REPLACE VIEW {table_name} AS SELECT * FROM read_csv_auto('{clean_path}')"

            self._conn.execute(sql)
            self._registered_tables[dataset_version_id] = table_name
        return table_name

    def unregister_dataset(self, dataset_version_id: str) -> None:
        """Unregister a dataset version view from DuckDB."""
        with self._exec_lock:
            table_name = self._registered_tables.pop(dataset_version_id, None)
            if table_name:
                self._conn.execute(f"DROP VIEW IF EXISTS {table_name}")

    def is_registered(self, dataset_version_id: str) -> bool:
        return dataset_version_id in self._registered_tables

    def get_table_name(self, dataset_version_id: str) -> Optional[str]:
        return self._registered_tables.get(dataset_version_id)

    def validate_query_safety(self, sql_query: str) -> None:
        """Enforce strict read-only analytical SQL operations."""
        cleaned_sql = re.sub(r"--.*?$|/\*.*?\*/", "", sql_query, flags=re.MULTILINE | re.DOTALL).strip()

        # Must start with SELECT or WITH
        if not re.match(r"^(SELECT|WITH)\b", cleaned_sql, re.IGNORECASE):
            raise DuckDBSecurityError("Prohibited SQL: Query must be a read-only SELECT or WITH statement.")

        for pattern in self.PROHIBITED_KEYWORDS:
            if re.search(pattern, cleaned_sql, re.IGNORECASE):
                keyword = pattern.replace(r"\b", "")
                raise DuckDBSecurityError(f"Prohibited SQL operation: '{keyword}' is forbidden in analytical queries.")

        # Disallow multi-statement execution via semicolon
        statements = [s.strip() for s in cleaned_sql.split(";") if s.strip()]
        if len(statements) > 1:
            raise DuckDBSecurityError("Prohibited SQL: Multiple statements are not allowed in a single query.")

    def execute_query(
        self,
        dataset_version_id: str,
        sql_query: str,
        parameters: Optional[List[Any]] = None,
        max_rows: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Execute a validated read-only SQL query against the registered dataset version."""
        self.validate_query_safety(sql_query)

        table_name = self.get_table_name(dataset_version_id)
        if not table_name:
            raise ValueError(f"Dataset version '{dataset_version_id}' is not registered in DuckDB.")

        # Replace generic table aliases 'dataset' or 'data' with the internal safe table name
        safe_sql = re.sub(r"\b(dataset|data)\b", table_name, sql_query, flags=re.IGNORECASE)

        limit_to_apply = max_rows or self.max_result_rows
        # Enforce bounded limit if not present
        if not re.search(r"\bLIMIT\s+\d+", safe_sql, re.IGNORECASE):
            safe_sql = f"{safe_sql} LIMIT {limit_to_apply}"

        start_time = time.perf_counter()
        with self._exec_lock:
            try:
                rel = self._conn.execute(safe_sql, parameters or [])
                columns = [desc[0] for desc in rel.description] if rel.description else []
                rows = rel.fetchall()
            except duckdb.Error as e:
                raise ValueError(f"DuckDB execution error: {str(e)}")

        execution_time_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

        # Truncate if exceeds limit
        if len(rows) > limit_to_apply:
            rows = rows[:limit_to_apply]

        return {
            "columns": columns,
            "rows": rows,
            "row_count": len(rows),
            "execution_time_ms": execution_time_ms,
            "metadata": {
                "dataset_version_id": dataset_version_id,
                "table_name": table_name,
                "executed_query": safe_sql,
            },
        }

    def explain_query(self, dataset_version_id: str, sql_query: str) -> str:
        """Obtain the DuckDB query execution plan."""
        self.validate_query_safety(sql_query)
        table_name = self.get_table_name(dataset_version_id)
        if not table_name:
            raise ValueError(f"Dataset version '{dataset_version_id}' is not registered in DuckDB.")

        safe_sql = re.sub(r"\b(dataset|data)\b", table_name, sql_query, flags=re.IGNORECASE)
        explain_sql = f"EXPLAIN {safe_sql}"

        with self._exec_lock:
            result = self._conn.execute(explain_sql).fetchall()
        return "\n".join([str(r[1]) for r in result if len(r) > 1])

    def get_schema(self, dataset_version_id: str) -> Dict[str, str]:
        """Retrieve schema dictionary (column_name -> dtype) for a registered dataset."""
        table_name = self.get_table_name(dataset_version_id)
        if not table_name:
            raise ValueError(f"Dataset version '{dataset_version_id}' is not registered in DuckDB.")

        with self._exec_lock:
            res = self._conn.execute(f"DESCRIBE {table_name}").fetchall()
            # DuckDB describe returns: column_name, column_type, null, key, default, extra
            return {str(r[0]): str(r[1]) for r in res}

    def health_check(self) -> Dict[str, Any]:
        """Verify DuckDB analytical engine responsiveness."""
        with self._exec_lock:
            res = self._conn.execute("SELECT 1 as ping").fetchone()
            return {
                "status": "healthy" if res and res[0] == 1 else "unhealthy",
                "registered_datasets_count": len(self._registered_tables),
            }


# Global Singleton instance
duckdb_manager = DuckDBManager.get_instance()
