from abc import ABC, abstractmethod
from typing import Any, List, Optional, Tuple

from app.analytics.duckdb.dataset import AnalyticalDataset
from app.analytics.duckdb.manager import duckdb_manager
from app.analytics.engine.contracts import AnalysisToolMetadata, SortSpecification


class AnalysisTool(ABC):
    """
    Abstract Base Class for all deterministic analytical tools.
    Every tool provides machine-readable metadata, input validation, and execution.
    """

    @property
    @abstractmethod
    def metadata(self) -> AnalysisToolMetadata:
        """Machine-readable metadata, parameter requirements, and schema."""
        pass

    @abstractmethod
    def validate(
        self,
        dataset: AnalyticalDataset,
        parameters: dict[str, Any],
        filters: Optional[Any] = None,
    ) -> None:
        """
        Validate inputs against dataset schema, column types, and mathematical requirements.
        Raises ValueError or TypeError if invalid.
        """
        pass

    @abstractmethod
    def execute(
        self,
        dataset: AnalyticalDataset,
        parameters: dict[str, Any],
        filters: Optional[Any] = None,
        sort_by: Optional[List[SortSpecification]] = None,
        limit: int = 1000,
        offset: int = 0,
    ) -> Tuple[List[str], List[dict[str, Any]], Optional[dict[str, Any]]]:
        """
        Executes the analysis deterministically.
        Returns (columns_list, rows_list_of_dicts, summary_metadata_dict).
        """
        pass

    def _execute_sql(
        self,
        dataset: AnalyticalDataset,
        sql: str,
        parameters: Optional[List[Any]] = None,
    ) -> Tuple[List[str], List[dict[str, Any]]]:
        """Helper to run parameterized SQL against the registered dataset view."""
        res = duckdb_manager.execute_query(
            dataset_version_id=dataset.version_id,
            sql_query=sql,
            parameters=parameters or [],
            max_rows=10000,
        )
        columns = res["columns"]
        raw_rows = res["rows"]
        dict_rows = [
            r if isinstance(r, dict) else dict(zip(columns, r))
            for r in raw_rows
        ]
        return columns, dict_rows
