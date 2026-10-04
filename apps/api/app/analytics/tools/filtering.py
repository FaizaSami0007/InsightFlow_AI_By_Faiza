from typing import Any, List, Optional, Tuple

from app.analytics.duckdb.dataset import AnalyticalDataset
from app.analytics.engine.contracts import AnalysisToolMetadata, SortSpecification
from app.analytics.engine.sanitizer import ResultSanitizer
from app.analytics.engine.sql_builder import SafeSQLBuilder
from app.analytics.tools.base import AnalysisTool


class FilterDataTool(AnalysisTool):
    """
    Filters rows from the dataset based on structured, typed criteria.
    """

    @property
    def metadata(self) -> AnalysisToolMetadata:
        return AnalysisToolMetadata(
            name="filter_data",
            display_name="Filter Data",
            description="Filters dataset rows using typed conditions and logical operators.",
            category="filtering",
            optional_params=["columns", "limit", "offset"],
            input_schema={
                "type": "object",
                "properties": {
                    "columns": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Columns to select. Defaults to all columns.",
                    }
                },
            },
            output_schema={
                "type": "object",
                "properties": {
                    "columns": {"type": "array", "items": {"type": "string"}},
                    "rows": {"type": "array", "items": {"type": "object"}},
                },
            },
            semantic_prerequisites={},
        )

    def validate(
        self,
        dataset: AnalyticalDataset,
        parameters: dict[str, Any],
        filters: Optional[Any] = None,
    ) -> None:
        target_cols = parameters.get("columns")
        if target_cols:
            if not isinstance(target_cols, list):
                raise ValueError("'columns' parameter must be a list of strings")
            for col in target_cols:
                SafeSQLBuilder.validate_identifier(col, dataset.columns)
        if filters:
            SafeSQLBuilder.build_filter_clause(filters, dataset.columns)

    def execute(
        self,
        dataset: AnalyticalDataset,
        parameters: dict[str, Any],
        filters: Optional[Any] = None,
        sort_by: Optional[List[SortSpecification]] = None,
        limit: int = 1000,
        offset: int = 0,
    ) -> Tuple[List[str], List[dict[str, Any]], Optional[dict[str, Any]]]:
        target_cols = parameters.get("columns") or dataset.columns
        select_cols = ", ".join([SafeSQLBuilder.quote_identifier(c) for c in target_cols])
        table_name = dataset.view_name

        where_sql, params = SafeSQLBuilder.build_filter_clause(filters, dataset.columns)
        where_clause = f"WHERE {where_sql}" if where_sql else ""
        order_clause = SafeSQLBuilder.build_order_by(sort_by, dataset.columns)

        sql = f"""
        SELECT {select_cols}
        FROM {table_name}
        {where_clause}
        {order_clause}
        LIMIT {limit} OFFSET {offset}
        """

        count_sql = f"SELECT COUNT(*) AS total_count FROM {table_name} {where_clause}"
        _, count_rows = self._execute_sql(dataset, count_sql, params)
        total_matched = count_rows[0].get("total_count", 0) if count_rows else 0

        cols, rows = self._execute_sql(dataset, sql, params)
        summary = {
            "total_matched_rows": total_matched,
            "returned_rows": len(rows),
            "offset": offset,
            "limit": limit,
        }
        return cols, ResultSanitizer.sanitize_rows(rows), summary


class SortDataTool(AnalysisTool):
    """
    Sorts dataset rows across one or multiple columns.
    """

    @property
    def metadata(self) -> AnalysisToolMetadata:
        return AnalysisToolMetadata(
            name="sort_data",
            display_name="Sort Data",
            description="Sorts rows by one or more columns in ascending or descending order.",
            category="descriptive",
            required_params=["sort_by"],
            optional_params=["columns", "limit", "offset"],
            input_schema={
                "type": "object",
                "properties": {
                    "sort_by": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "column": {"type": "string"},
                                "order": {"type": "string", "enum": ["ASC", "DESC"]},
                            },
                            "required": ["column"],
                        },
                    },
                    "columns": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["sort_by"],
            },
            output_schema={
                "type": "object",
                "properties": {
                    "columns": {"type": "array", "items": {"type": "string"}},
                    "rows": {"type": "array", "items": {"type": "object"}},
                },
            },
            semantic_prerequisites={},
        )

    def validate(
        self,
        dataset: AnalyticalDataset,
        parameters: dict[str, Any],
        filters: Optional[Any] = None,
    ) -> None:
        sort_by = parameters.get("sort_by")
        if not sort_by or not isinstance(sort_by, list):
            raise ValueError("'sort_by' must be a non-empty list of sort specifications")
        for item in sort_by:
            col = item.get("column") if isinstance(item, dict) else getattr(item, "column", None)
            if not col:
                raise ValueError("Each sort specification must contain a 'column'")
            SafeSQLBuilder.validate_identifier(col, dataset.columns)

    def execute(
        self,
        dataset: AnalyticalDataset,
        parameters: dict[str, Any],
        filters: Optional[Any] = None,
        sort_by: Optional[List[SortSpecification]] = None,
        limit: int = 1000,
        offset: int = 0,
    ) -> Tuple[List[str], List[dict[str, Any]], Optional[dict[str, Any]]]:
        raw_sort = parameters.get("sort_by") or []
        sort_specs = [SortSpecification(**s) if isinstance(s, dict) else s for s in raw_sort] if raw_sort else sort_by

        target_cols = parameters.get("columns") or dataset.columns
        select_cols = ", ".join([SafeSQLBuilder.quote_identifier(c) for c in target_cols])
        table_name = dataset.view_name

        where_sql, params = SafeSQLBuilder.build_filter_clause(filters, dataset.columns)
        where_clause = f"WHERE {where_sql}" if where_sql else ""
        order_clause = SafeSQLBuilder.build_order_by(sort_specs, dataset.columns)

        sql = f"""
        SELECT {select_cols}
        FROM {table_name}
        {where_clause}
        {order_clause}
        LIMIT {limit} OFFSET {offset}
        """

        cols, rows = self._execute_sql(dataset, sql, params)
        summary = {"returned_rows": len(rows), "offset": offset, "limit": limit}
        return cols, ResultSanitizer.sanitize_rows(rows), summary
