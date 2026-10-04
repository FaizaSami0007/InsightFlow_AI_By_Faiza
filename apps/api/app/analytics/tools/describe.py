from typing import Any, List, Optional, Tuple

from app.analytics.duckdb.dataset import AnalyticalDataset
from app.analytics.engine.contracts import AnalysisToolMetadata, SortSpecification
from app.analytics.engine.sanitizer import ResultSanitizer
from app.analytics.engine.sql_builder import SafeSQLBuilder
from app.analytics.tools.base import AnalysisTool


class DescribeDatasetTool(AnalysisTool):
    """
    Computes summary descriptive statistics across specified columns or the entire dataset.
    """

    @property
    def metadata(self) -> AnalysisToolMetadata:
        return AnalysisToolMetadata(
            name="describe_dataset",
            display_name="Describe Dataset",
            description="Generates comprehensive descriptive statistics for numeric and categorical columns.",
            category="descriptive",
            optional_params=["columns"],
            input_schema={
                "type": "object",
                "properties": {
                    "columns": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional list of column names to describe. Defaults to all columns.",
                    }
                },
            },
            output_schema={
                "type": "object",
                "properties": {
                    "columns": {"type": "array", "items": {"type": "string"}},
                    "rows": {"type": "array", "items": {"type": "object"}},
                    "summary": {"type": "object"},
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
        table_name = dataset.view_name

        where_sql, params = SafeSQLBuilder.build_filter_clause(filters, dataset.columns)
        where_clause = f"WHERE {where_sql}" if where_sql else ""

        rows = []
        for col in target_cols:
            quoted_col = SafeSQLBuilder.quote_identifier(col)
            # Check type from dataset schema
            col_type = dataset.schema.get(col, "VARCHAR").upper()
            is_numeric = any(t in col_type for t in ["INT", "DOUBLE", "FLOAT", "DECIMAL", "NUMERIC", "REAL", "BIGINT"])

            if is_numeric:
                sql = f"""
                SELECT
                    COUNT({quoted_col}) AS count,
                    COUNT(*) - COUNT({quoted_col}) AS null_count,
                    COUNT(DISTINCT {quoted_col}) AS unique_count,
                    AVG({quoted_col}) AS mean,
                    MEDIAN({quoted_col}) AS median,
                    STDDEV({quoted_col}) AS std_dev,
                    MIN({quoted_col}) AS min,
                    MAX({quoted_col}) AS max,
                    QUANTILE_CONT({quoted_col}, 0.25) AS q1,
                    QUANTILE_CONT({quoted_col}, 0.75) AS q3
                FROM {table_name}
                {where_clause}
                """
                _, res_rows = self._execute_sql(dataset, sql, params)
                res = res_rows[0] if res_rows else {}
                q1 = res.get("q1")
                q3 = res.get("q3")
                iqr = (q3 - q1) if (q1 is not None and q3 is not None) else None

                rows.append({
                    "column": col,
                    "data_type": col_type,
                    "count": res.get("count", 0),
                    "null_count": res.get("null_count", 0),
                    "unique_count": res.get("unique_count", 0),
                    "mean": res.get("mean"),
                    "median": res.get("median"),
                    "std_dev": res.get("std_dev"),
                    "min": res.get("min"),
                    "max": res.get("max"),
                    "q1": q1,
                    "q3": q3,
                    "iqr": iqr,
                })
            else:
                sql = f"""
                SELECT
                    COUNT({quoted_col}) AS count,
                    COUNT(*) - COUNT({quoted_col}) AS null_count,
                    COUNT(DISTINCT {quoted_col}) AS unique_count,
                    MIN({quoted_col}) AS min_value,
                    MAX({quoted_col}) AS max_value
                FROM {table_name}
                {where_clause}
                """
                _, res_rows = self._execute_sql(dataset, sql, params)
                res = res_rows[0] if res_rows else {}
                rows.append({
                    "column": col,
                    "data_type": col_type,
                    "count": res.get("count", 0),
                    "null_count": res.get("null_count", 0),
                    "unique_count": res.get("unique_count", 0),
                    "mean": None,
                    "median": None,
                    "std_dev": None,
                    "min": res.get("min_value"),
                    "max": res.get("max_value"),
                    "q1": None,
                    "q3": None,
                    "iqr": None,
                })

        output_cols = [
            "column", "data_type", "count", "null_count", "unique_count",
            "mean", "median", "std_dev", "min", "max", "q1", "q3", "iqr"
        ]
        summary = {
            "total_columns_described": len(rows),
            "numeric_columns": sum(1 for r in rows if r["mean"] is not None),
            "categorical_columns": sum(1 for r in rows if r["mean"] is None),
        }
        return output_cols, ResultSanitizer.sanitize_rows(rows), summary
