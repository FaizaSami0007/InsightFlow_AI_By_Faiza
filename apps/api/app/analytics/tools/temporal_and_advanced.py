from typing import Any, List, Optional, Tuple

from app.analytics.duckdb.dataset import AnalyticalDataset
from app.analytics.engine.contracts import AnalysisToolMetadata, SortSpecification
from app.analytics.engine.sanitizer import ResultSanitizer
from app.analytics.engine.sql_builder import SafeSQLBuilder
from app.analytics.tools.base import AnalysisTool


class TimeSeriesSummaryTool(AnalysisTool):
    """
    Aggregates metrics over temporal intervals (day, week, month, quarter, year).
    """

    SUPPORTED_PERIODS = ["day", "week", "month", "quarter", "year"]

    @property
    def metadata(self) -> AnalysisToolMetadata:
        return AnalysisToolMetadata(
            name="time_series_summary",
            display_name="Time Series Summary",
            description="Aggregates metrics over temporal date buckets (day, week, month, quarter, year).",
            category="temporal",
            required_params=["date_column"],
            optional_params=["metric_column", "period", "aggregation"],
            input_schema={
                "type": "object",
                "properties": {
                    "date_column": {"type": "string", "description": "Date or timestamp column to bucket by."},
                    "metric_column": {"type": "string", "description": "Optional numeric metric to aggregate."},
                    "period": {
                        "type": "string",
                        "enum": ["day", "week", "month", "quarter", "year"],
                        "default": "month",
                    },
                    "aggregation": {
                        "type": "string",
                        "enum": ["SUM", "AVG", "COUNT", "MIN", "MAX"],
                        "default": "SUM",
                    },
                },
                "required": ["date_column"],
            },
            output_schema={
                "type": "object",
                "properties": {
                    "columns": {"type": "array", "items": {"type": "string"}},
                    "rows": {"type": "array", "items": {"type": "object"}},
                    "summary": {"type": "object"},
                },
            },
            semantic_prerequisites={"date_column": ["DATE", "DATETIME"]},
        )

    def validate(
        self,
        dataset: AnalyticalDataset,
        parameters: dict[str, Any],
        filters: Optional[Any] = None,
    ) -> None:
        date_col = parameters.get("date_column")
        if not date_col:
            raise ValueError("Parameter 'date_column' is required")
        SafeSQLBuilder.validate_identifier(date_col, dataset.columns)

        period = (parameters.get("period") or "month").lower()
        if period not in self.SUPPORTED_PERIODS:
            raise ValueError(f"Unsupported period '{period}'. Must be one of: {self.SUPPORTED_PERIODS}")

        metric_col = parameters.get("metric_column")
        if metric_col:
            SafeSQLBuilder.validate_identifier(metric_col, dataset.columns)
            col_type = dataset.schema.get(metric_col, "VARCHAR").upper()
            if not any(t in col_type for t in ["INT", "DOUBLE", "FLOAT", "DECIMAL", "NUMERIC", "REAL", "BIGINT"]):
                raise ValueError(f"Metric column '{metric_col}' must be numeric, found {col_type}")

    def execute(
        self,
        dataset: AnalyticalDataset,
        parameters: dict[str, Any],
        filters: Optional[Any] = None,
        sort_by: Optional[List[SortSpecification]] = None,
        limit: int = 1000,
        offset: int = 0,
    ) -> Tuple[List[str], List[dict[str, Any]], Optional[dict[str, Any]]]:
        date_col = parameters["date_column"]
        period = (parameters.get("period") or "month").lower()
        metric_col = parameters.get("metric_column")
        agg = (parameters.get("aggregation") or "SUM").upper()

        quoted_date = SafeSQLBuilder.quote_identifier(date_col)
        table_name = dataset.view_name

        where_sql, params = SafeSQLBuilder.build_filter_clause(filters, dataset.columns)
        where_clause = (
            f"WHERE {where_sql} AND {quoted_date} IS NOT NULL" if where_sql else f"WHERE {quoted_date} IS NOT NULL"
        )

        if metric_col:
            quoted_metric = SafeSQLBuilder.quote_identifier(metric_col)
            metric_select = f", {agg}({quoted_metric}) AS metric_total"
        else:
            metric_select = ""

        sql = f"""
        SELECT
            CAST(DATE_TRUNC('{period}', CAST({quoted_date} AS TIMESTAMP)) AS VARCHAR) AS period_bucket,
            COUNT(*) AS record_count
            {metric_select}
        FROM {table_name}
        {where_clause}
        GROUP BY period_bucket
        ORDER BY period_bucket ASC
        LIMIT {limit} OFFSET {offset}
        """

        cols, rows = self._execute_sql(dataset, sql, params)
        summary = {
            "date_column": date_col,
            "period": period,
            "metric_column": metric_col,
            "aggregation": agg if metric_col else "COUNT",
            "total_buckets": len(rows),
        }
        return cols, ResultSanitizer.sanitize_rows(rows), summary


class PercentChangeTool(AnalysisTool):
    """
    Computes period-over-period or step-by-step percentage change across ordered observations.
    """

    @property
    def metadata(self) -> AnalysisToolMetadata:
        return AnalysisToolMetadata(
            name="percent_change",
            display_name="Percent Change & Growth",
            description="Calculates period-over-period delta and percent change across sequential observations.",
            category="temporal",
            required_params=["metric_column", "order_by_column"],
            optional_params=["group_by_column"],
            input_schema={
                "type": "object",
                "properties": {
                    "metric_column": {"type": "string", "description": "Numeric measure to calculate change for."},
                    "order_by_column": {
                        "type": "string",
                        "description": "Column defining sequence order (e.g. date, period).",
                    },
                    "group_by_column": {
                        "type": "string",
                        "description": "Optional dimension to partition calculation.",
                    },
                },
                "required": ["metric_column", "order_by_column"],
            },
            output_schema={
                "type": "object",
                "properties": {
                    "columns": {"type": "array", "items": {"type": "string"}},
                    "rows": {"type": "array", "items": {"type": "object"}},
                    "summary": {"type": "object"},
                },
            },
            semantic_prerequisites={"metric_column": ["MEASURE", "INTEGER", "FLOAT"]},
        )

    def validate(
        self,
        dataset: AnalyticalDataset,
        parameters: dict[str, Any],
        filters: Optional[Any] = None,
    ) -> None:
        metric_col = parameters.get("metric_column")
        order_col = parameters.get("order_by_column")
        if not metric_col or not order_col:
            raise ValueError("Parameters 'metric_column' and 'order_by_column' are required")
        SafeSQLBuilder.validate_identifier(metric_col, dataset.columns)
        SafeSQLBuilder.validate_identifier(order_col, dataset.columns)

        col_type = dataset.schema.get(metric_col, "VARCHAR").upper()
        if not any(t in col_type for t in ["INT", "DOUBLE", "FLOAT", "DECIMAL", "NUMERIC", "REAL", "BIGINT"]):
            raise ValueError(f"Metric column '{metric_col}' must be numeric, found {col_type}")

        group_col = parameters.get("group_by_column")
        if group_col:
            SafeSQLBuilder.validate_identifier(group_col, dataset.columns)

    def execute(
        self,
        dataset: AnalyticalDataset,
        parameters: dict[str, Any],
        filters: Optional[Any] = None,
        sort_by: Optional[List[SortSpecification]] = None,
        limit: int = 1000,
        offset: int = 0,
    ) -> Tuple[List[str], List[dict[str, Any]], Optional[dict[str, Any]]]:
        metric_col = parameters["metric_column"]
        order_col = parameters["order_by_column"]
        group_col = parameters.get("group_by_column")

        q_metric = SafeSQLBuilder.quote_identifier(metric_col)
        q_order = SafeSQLBuilder.quote_identifier(order_col)
        table_name = dataset.view_name

        where_sql, params = SafeSQLBuilder.build_filter_clause(filters, dataset.columns)
        where_clause = f"WHERE {where_sql}" if where_sql else ""

        partition_clause = f"PARTITION BY {SafeSQLBuilder.quote_identifier(group_col)}" if group_col else ""
        group_select = f"{SafeSQLBuilder.quote_identifier(group_col)}, " if group_col else ""

        sql = f"""
        WITH sequence_data AS (
            SELECT
                {group_select}
                {q_order},
                {q_metric} AS current_value,
                LAG({q_metric}) OVER ({partition_clause} ORDER BY {q_order} ASC) AS previous_value
            FROM {table_name}
            {where_clause}
        )
        SELECT
            *,
            (current_value - previous_value) AS delta,
            CASE
                WHEN previous_value IS NULL THEN NULL
                WHEN previous_value = 0 THEN NULL
                ELSE ROUND(((current_value - previous_value) / ABS(previous_value)) * 100.0, 2)
            END AS percent_change
        FROM sequence_data
        ORDER BY {q_order} ASC
        LIMIT {limit} OFFSET {offset}
        """

        cols, rows = self._execute_sql(dataset, sql, params)
        summary = {
            "metric_column": metric_col,
            "order_by_column": order_col,
            "group_by_column": group_col,
            "total_points": len(rows),
        }
        return cols, ResultSanitizer.sanitize_rows(rows), summary


class OutlierAnalysisTool(AnalysisTool):
    """
    Identifies statistical outliers in numeric fields using Tukey's Interquartile Range (IQR) rule.
    """

    @property
    def metadata(self) -> AnalysisToolMetadata:
        return AnalysisToolMetadata(
            name="outlier_analysis",
            display_name="Outlier Analysis",
            description="Detects statistical anomalies using IQR upper and lower threshold bounds.",
            category="statistical",
            required_params=["column"],
            optional_params=["multiplier", "limit"],
            input_schema={
                "type": "object",
                "properties": {
                    "column": {"type": "string", "description": "Numeric column to evaluate for outliers."},
                    "multiplier": {
                        "type": "number",
                        "default": 1.5,
                        "description": "IQR multiplier (typically 1.5 for mild outliers, 3.0 for extreme).",
                    },
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
            raise ValueError(f"Column '{col}' must be numeric for outlier analysis, found {col_type}")

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
        k = float(parameters.get("multiplier", 1.5))
        q_col = SafeSQLBuilder.quote_identifier(col)
        table_name = dataset.view_name

        where_sql, params = SafeSQLBuilder.build_filter_clause(filters, dataset.columns)
        where_clause = f"WHERE {where_sql}" if where_sql else ""

        # Step 1: Compute Q1, Q3, IQR
        q_sql = f"""
        SELECT
            COUNT(*) AS total_count,
            COUNT({q_col}) AS non_null_count,
            QUANTILE_CONT({q_col}, 0.25) AS q1,
            QUANTILE_CONT({q_col}, 0.75) AS q3
        FROM {table_name}
        {where_clause}
        """
        _, q_rows = self._execute_sql(dataset, q_sql, params)
        q_res = q_rows[0] if q_rows else {}
        q1 = q_res.get("q1") or 0.0
        q3 = q_res.get("q3") or 0.0
        iqr = q3 - q1
        lower_bound = q1 - (k * iqr)
        upper_bound = q3 + (k * iqr)
        total_records = q_res.get("non_null_count", 0)

        # Step 2: Extract Outlier Rows
        outlier_where = f"({q_col} < {lower_bound} OR {q_col} > {upper_bound})"
        combined_where = f"WHERE {where_sql} AND {outlier_where}" if where_sql else f"WHERE {outlier_where}"

        sql = f"""
        SELECT *,
            CASE
                WHEN {q_col} < {lower_bound} THEN 'LOWER_OUTLIER'
                ELSE 'UPPER_OUTLIER'
            END AS outlier_type
        FROM {table_name}
        {combined_where}
        LIMIT {limit} OFFSET {offset}
        """
        cols, rows = self._execute_sql(dataset, sql, params)

        count_sql = f"SELECT COUNT(*) AS cnt FROM {table_name} {combined_where}"
        _, c_rows = self._execute_sql(dataset, count_sql, params)
        outlier_count = c_rows[0].get("cnt", 0) if c_rows else 0
        outlier_pct = (outlier_count / total_records * 100.0) if total_records > 0 else 0.0

        summary = {
            "column": col,
            "q1": q1,
            "q3": q3,
            "iqr": iqr,
            "lower_bound": lower_bound,
            "upper_bound": upper_bound,
            "total_records": total_records,
            "outlier_count": outlier_count,
            "outlier_percentage": round(outlier_pct, 2),
        }
        return cols, ResultSanitizer.sanitize_rows(rows), summary
