from typing import Any, List, Optional, Tuple

from app.analytics.duckdb.dataset import AnalyticalDataset
from app.analytics.engine.contracts import AnalysisToolMetadata, SortSpecification
from app.analytics.engine.sanitizer import ResultSanitizer
from app.analytics.engine.sql_builder import SafeSQLBuilder
from app.analytics.tools.base import AnalysisTool


class FrequencyTool(AnalysisTool):
    """
    Computes frequency distribution, proportions, and cumulative percentages for categorical variables.
    """

    @property
    def metadata(self) -> AnalysisToolMetadata:
        return AnalysisToolMetadata(
            name="frequency",
            display_name="Frequency Distribution",
            description="Calculates frequency counts, percentages, and cumulative percentages for a categorical column.",
            category="statistical",
            required_params=["column"],
            optional_params=["top_n", "include_nulls"],
            input_schema={
                "type": "object",
                "properties": {
                    "column": {"type": "string", "description": "Column name to calculate frequencies for."},
                    "top_n": {"type": "integer", "default": 20, "description": "Number of top categories to return."},
                    "include_nulls": {"type": "boolean", "default": True},
                },
                "required": ["column"],
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
        col = parameters.get("column")
        if not col:
            raise ValueError("Parameter 'column' is required")
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
        col = parameters["column"]
        top_n = min(parameters.get("top_n", 20), limit)
        quoted_col = SafeSQLBuilder.quote_identifier(col)
        table_name = dataset.view_name

        where_sql, params = SafeSQLBuilder.build_filter_clause(filters, dataset.columns)
        where_clause = f"WHERE {where_sql}" if where_sql else ""

        # Total count
        total_sql = f"SELECT COUNT(*) AS total FROM {table_name} {where_clause}"
        _, total_rows = self._execute_sql(dataset, total_sql, params)
        total_records = total_rows[0].get("total", 0) if total_rows else 0

        sql = f"""
        SELECT
            {quoted_col} AS value,
            COUNT(*) AS count
        FROM {table_name}
        {where_clause}
        GROUP BY {quoted_col}
        ORDER BY count DESC
        LIMIT {top_n}
        """

        cols, raw_rows = self._execute_sql(dataset, sql, params)

        rows = []
        cumulative = 0.0
        for r in raw_rows:
            cnt = r.get("count", 0)
            pct = (cnt / total_records * 100.0) if total_records > 0 else 0.0
            cumulative += pct
            rows.append(
                {
                    "value": r.get("value"),
                    "count": cnt,
                    "percentage": round(pct, 2),
                    "cumulative_percentage": round(min(cumulative, 100.0), 2),
                }
            )

        output_cols = ["value", "count", "percentage", "cumulative_percentage"]
        summary = {
            "column": col,
            "total_records": total_records,
            "unique_categories_returned": len(rows),
        }
        return output_cols, ResultSanitizer.sanitize_rows(rows), summary


class CorrelationTool(AnalysisTool):
    """
    Computes Pearson and Spearman pairwise correlation coefficients across numeric columns.
    """

    @property
    def metadata(self) -> AnalysisToolMetadata:
        return AnalysisToolMetadata(
            name="correlation",
            display_name="Correlation Matrix",
            description="Calculates Pearson or Spearman correlation coefficients and sample sizes for numeric columns.",
            category="statistical",
            required_params=["columns"],
            optional_params=["method"],
            input_schema={
                "type": "object",
                "properties": {
                    "columns": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of at least two numeric column names.",
                    },
                    "method": {
                        "type": "string",
                        "enum": ["pearson", "spearman"],
                        "default": "pearson",
                    },
                },
                "required": ["columns"],
            },
            output_schema={
                "type": "object",
                "properties": {
                    "columns": {"type": "array", "items": {"type": "string"}},
                    "rows": {"type": "array", "items": {"type": "object"}},
                    "summary": {"type": "object"},
                },
            },
            semantic_prerequisites={"columns": ["MEASURE", "INTEGER", "FLOAT"]},
        )

    def validate(
        self,
        dataset: AnalyticalDataset,
        parameters: dict[str, Any],
        filters: Optional[Any] = None,
    ) -> None:
        cols = parameters.get("columns")
        if not cols or not isinstance(cols, list) or len(cols) < 2:
            raise ValueError("Parameter 'columns' must be a list with at least two numeric columns")
        for c in cols:
            SafeSQLBuilder.validate_identifier(c, dataset.columns)
            col_type = dataset.schema.get(c, "VARCHAR").upper()
            if not any(t in col_type for t in ["INT", "DOUBLE", "FLOAT", "DECIMAL", "NUMERIC", "REAL", "BIGINT"]):
                raise ValueError(f"Column '{c}' must be numeric for correlation analysis, found {col_type}")

    def execute(
        self,
        dataset: AnalyticalDataset,
        parameters: dict[str, Any],
        filters: Optional[Any] = None,
        sort_by: Optional[List[SortSpecification]] = None,
        limit: int = 1000,
        offset: int = 0,
    ) -> Tuple[List[str], List[dict[str, Any]], Optional[dict[str, Any]]]:
        cols = parameters["columns"]
        method = (parameters.get("method") or "pearson").lower()
        table_name = dataset.view_name

        where_sql, params = SafeSQLBuilder.build_filter_clause(filters, dataset.columns)
        where_clause = f"WHERE {where_sql}" if where_sql else ""

        rows = []
        for i, col1 in enumerate(cols):
            row_dict: dict[str, Any] = {"column": col1}
            q_col1 = SafeSQLBuilder.quote_identifier(col1)

            for j, col2 in enumerate(cols):
                if i == j:
                    row_dict[col2] = 1.0
                elif j < i:
                    # Symmetric matrix
                    row_dict[col2] = rows[j][col1]
                else:
                    q_col2 = SafeSQLBuilder.quote_identifier(col2)
                    if method == "spearman":
                        # Spearman rank correlation via rank transform
                        sql = f"""
                        WITH ranked AS (
                            SELECT
                                RANK() OVER (ORDER BY {q_col1}) AS r1,
                                RANK() OVER (ORDER BY {q_col2}) AS r2
                            FROM {table_name}
                            {where_clause}
                            AND {q_col1} IS NOT NULL AND {q_col2} IS NOT NULL
                        )
                        SELECT CORR(r1, r2) AS r, COUNT(*) AS n FROM ranked
                        """
                    else:
                        # Pearson correlation
                        sql = f"""
                        SELECT CORR({q_col1}, {q_col2}) AS r, COUNT(*) AS n
                        FROM {table_name}
                        {where_clause}
                        """
                    _, res_rows = self._execute_sql(dataset, sql, params)
                    r_val = res_rows[0].get("r") if res_rows else None
                    row_dict[col2] = round(r_val, 4) if r_val is not None else None
            rows.append(row_dict)

        output_cols = ["column"] + cols
        summary = {
            "method": method,
            "matrix_size": len(cols),
            "analyzed_columns": cols,
        }
        return output_cols, ResultSanitizer.sanitize_rows(rows), summary


class DistributionTool(AnalysisTool):
    """
    Computes distribution metrics (skewness, kurtosis, quartiles) and histogram bins for a numeric column.
    """

    @property
    def metadata(self) -> AnalysisToolMetadata:
        return AnalysisToolMetadata(
            name="distribution",
            display_name="Distribution & Histogram",
            description="Calculates distribution shape metrics (skewness, kurtosis) and histogram frequency bins.",
            category="statistical",
            required_params=["column"],
            optional_params=["bins"],
            input_schema={
                "type": "object",
                "properties": {
                    "column": {"type": "string", "description": "Numeric column to evaluate."},
                    "bins": {"type": "integer", "default": 10, "minimum": 2, "maximum": 50},
                },
                "required": ["column"],
            },
            output_schema={
                "type": "object",
                "properties": {
                    "columns": {"type": "array", "items": {"type": "string"}},
                    "rows": {"type": "array", "items": {"type": "object"}},
                    "summary": {"type": "object"},
                },
            },
            semantic_prerequisites={"column": ["MEASURE", "INTEGER", "FLOAT"]},
        )

    def validate(
        self,
        dataset: AnalyticalDataset,
        parameters: dict[str, Any],
        filters: Optional[Any] = None,
    ) -> None:
        col = parameters.get("column")
        if not col:
            raise ValueError("Parameter 'column' is required")
        SafeSQLBuilder.validate_identifier(col, dataset.columns)
        col_type = dataset.schema.get(col, "VARCHAR").upper()
        if not any(t in col_type for t in ["INT", "DOUBLE", "FLOAT", "DECIMAL", "NUMERIC", "REAL", "BIGINT"]):
            raise ValueError(f"Column '{col}' must be numeric for distribution analysis, found {col_type}")

    def execute(
        self,
        dataset: AnalyticalDataset,
        parameters: dict[str, Any],
        filters: Optional[Any] = None,
        sort_by: Optional[List[SortSpecification]] = None,
        limit: int = 1000,
        offset: int = 0,
    ) -> Tuple[List[str], List[dict[str, Any]], Optional[dict[str, Any]]]:
        col = parameters["column"]
        bin_count = max(2, min(parameters.get("bins", 10), 50))
        quoted_col = SafeSQLBuilder.quote_identifier(col)
        table_name = dataset.view_name

        where_sql, params = SafeSQLBuilder.build_filter_clause(filters, dataset.columns)
        where_clause = f"WHERE {where_sql}" if where_sql else ""

        # Step 1: Compute basic min, max, moments
        stats_sql = f"""
        SELECT
            COUNT({quoted_col}) AS count,
            MIN({quoted_col}) AS min_val,
            MAX({quoted_col}) AS max_val,
            AVG({quoted_col}) AS mean_val,
            STDDEV({quoted_col}) AS std_val,
            MEDIAN({quoted_col}) AS median_val,
            SKEWNESS({quoted_col}) AS skewness,
            KURTOSIS({quoted_col}) AS kurtosis,
            QUANTILE_CONT({quoted_col}, 0.25) AS q1,
            QUANTILE_CONT({quoted_col}, 0.75) AS q3
        FROM {table_name}
        {where_clause}
        """
        _, stat_rows = self._execute_sql(dataset, stats_sql, params)
        stats = stat_rows[0] if stat_rows else {}
        min_v = stats.get("min_val")
        max_v = stats.get("max_val")
        total_cnt = stats.get("count", 0)

        # Step 2: Build histogram bins if valid min/max
        bin_rows = []
        if min_v is not None and max_v is not None and max_v > min_v and total_cnt > 0:
            bin_width = (max_v - min_v) / bin_count
            hist_where_clause = (
                f"WHERE {where_sql} AND {quoted_col} IS NOT NULL" if where_sql else f"WHERE {quoted_col} IS NOT NULL"
            )
            hist_sql = f"""
            SELECT
                FLOOR(({quoted_col} - {min_v}) / {bin_width}) AS bin_idx,
                COUNT(*) AS count
            FROM {table_name}
            {hist_where_clause}
            GROUP BY bin_idx
            ORDER BY bin_idx ASC
            """
            _, h_rows = self._execute_sql(dataset, hist_sql, params)
            h_map = {int(r["bin_idx"]): r["count"] for r in h_rows if r.get("bin_idx") is not None}

            for idx in range(bin_count):
                b_start = min_v + (idx * bin_width)
                b_end = min_v + ((idx + 1) * bin_width)
                cnt = h_map.get(idx, 0)
                pct = (cnt / total_cnt * 100.0) if total_cnt > 0 else 0.0
                bin_rows.append(
                    {
                        "bin_index": idx + 1,
                        "bin_start": round(b_start, 4),
                        "bin_end": round(b_end, 4),
                        "count": cnt,
                        "percentage": round(pct, 2),
                    }
                )
        else:
            bin_rows.append(
                {
                    "bin_index": 1,
                    "bin_start": min_v,
                    "bin_end": max_v,
                    "count": total_cnt,
                    "percentage": 100.0,
                }
            )

        output_cols = ["bin_index", "bin_start", "bin_end", "count", "percentage"]
        q1 = stats.get("q1")
        q3 = stats.get("q3")
        iqr = (q3 - q1) if (q1 is not None and q3 is not None) else None

        summary = {
            "column": col,
            "count": total_cnt,
            "min": min_v,
            "max": max_v,
            "mean": stats.get("mean_val"),
            "median": stats.get("median_val"),
            "std_dev": stats.get("std_val"),
            "skewness": stats.get("skewness"),
            "kurtosis": stats.get("kurtosis"),
            "q1": q1,
            "q3": q3,
            "iqr": iqr,
        }
        return output_cols, ResultSanitizer.sanitize_rows(bin_rows), summary
