from typing import Any, Dict, List, Optional

from app.analytics.duckdb.manager import DuckDBManager


class AnalyticalDataset:
    """Encapsulates a registered dataset version ready for analytical SQL query execution."""

    def __init__(
        self,
        dataset_id: str,
        version_id: str,
        file_path: str,
        file_format: str,
        duckdb_manager: Optional[DuckDBManager] = None,
    ):
        self.dataset_id = dataset_id
        self.version_id = version_id
        self.file_path = file_path
        self.file_format = file_format
        self.duckdb_manager = duckdb_manager or DuckDBManager.get_instance()
        self.table_name = self.duckdb_manager.register_dataset(version_id, file_path, file_format)

    def query(
        self,
        sql_query: str,
        parameters: Optional[List[Any]] = None,
        max_rows: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Execute a safe read-only analytical query against this dataset version."""
        return self.duckdb_manager.execute_query(
            dataset_version_id=self.version_id,
            sql_query=sql_query,
            parameters=parameters,
            max_rows=max_rows,
        )

    def explain(self, sql_query: str) -> str:
        """Explain the execution plan for a query against this dataset."""
        return self.duckdb_manager.explain_query(self.version_id, sql_query)

    def close(self) -> None:
        """Unregister the dataset table/view from DuckDB memory."""
        self.duckdb_manager.unregister_dataset(self.version_id)
