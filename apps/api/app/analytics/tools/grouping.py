from typing import Any, List, Optional, Tuple

from app.analytics.duckdb.dataset import AnalyticalDataset
from app.analytics.engine.contracts import (
    AggregationSpec,
    AggregationType,
    AnalysisToolMetadata,
    SortSpecification,
)
from app.analytics.engine.sanitizer import ResultSanitizer
from app.analytics.engine.sql_builder import SafeSQLBuilder
from app.analytics.tools.base import AnalysisTool


class GroupByTool(AnalysisTool):
    """
    Groups data by one or more dimension columns and computes aggregations.
    """

    @property
    def metadata(self) -> AnalysisToolMetadata:
        return AnalysisToolMetadata(
            name="group_by",
            display_name="Group By & Aggregate",
            description="Groups records by dimensions and computes aggregate metrics (SUM, AVG, MIN, MAX, COUNT, MEDIAN, STDDEV).",
            category="aggregation",
            required_params=["dimensions", "aggregations"],
            optional_params=["having", "limit", "offset"],
            input_schema={
                "type": "object",
                "properties": {
                    "dimensions": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "One or more categorical/dimension column names to group by.",
                    },
                    "aggregations": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "column": {"type": "string"},
                                "agg_type": {
                                    "type": "string",
                                    "enum": [
                                        "COUNT",
                                        "COUNT DISTINCT",
                                        "SUM",
                                        "AVG",
                                        "MIN",
                                        "MAX",
                                        "MEDIAN",
                                        "STDDEV",
                                        "VARIANCE",
                                    ],
                                },
                                "alias": {"type": "string"},
                            },
                            "required": ["column", "agg_type"],
                        },
                    },
                },
                "required": ["dimensions", "aggregations"],
            },
            output_schema={
                "type": "object",
                "properties": {
                    "columns": {"type": "array", "items": {"type": "string"}},
                    "rows": {"type": "array", "items": {"type": "object"}},
                    "summary": {"type": "object"},
                },
            },
            semantic_prerequisites={
                "dimensions": ["DIMENSION", "CATEGORY", "DATE", "IDENTIFIER", "TEXT"],
                "numeric_aggregations": ["MEASURE", "INTEGER", "FLOAT"],
            },
        )

    def validate(
        self,
        dataset: AnalyticalDataset,
        parameters: dict[str, Any],
        filters: Optional[Any] = None,
    ) -> None:
        # Normalize dimensions
        raw_dims = (
            parameters.get("dimensions")
            or parameters.get("dimension")
            or parameters.get("group_column")
        )
        if not raw_dims:
            raise ValueError("Parameter 'dimensions' is required")
        dims = [raw_dims] if isinstance(raw_dims, str) else raw_dims
        if not isinstance(dims, list) or len(dims) == 0:
            raise ValueError("'dimensions' must be a non-empty list of column names")
        for d in dims:
            SafeSQLBuilder.validate_identifier(d, dataset.columns)

        # Normalize aggregations
        raw_aggs = parameters.get("aggregations")
        if not raw_aggs:
            # Fallback for shorthand parameter format: metric/aggregate_column + aggregation
            metric = (
                parameters.get("metric")
                or parameters.get("aggregate_column")
                or parameters.get("column")
            )
            agg = parameters.get("aggregation") or "sum"
            if metric:
                raw_aggs = [{"column": metric, "agg_type": agg.upper()}]
            else:
                raw_aggs = [{"column": "*", "agg_type": "COUNT"}]

        if not isinstance(raw_aggs, list) or len(raw_aggs) == 0:
            raise ValueError("'aggregations' must be a non-empty list")

        for agg in raw_aggs:
            col = agg.get("column") if isinstance(agg, dict) else getattr(agg, "column", None)
            agg_type = agg.get("agg_type") if isinstance(agg, dict) else getattr(agg, "agg_type", None)
            if not col or not agg_type:
                raise ValueError("Each aggregation must specify 'column' and 'agg_type'")

            agg_type_str = str(agg_type).upper()
            if col != "*":
                SafeSQLBuilder.validate_identifier(col, dataset.columns)
                # If numeric aggregation, check type
                if agg_type_str in ("SUM", "AVG", "MEDIAN", "STDDEV", "VARIANCE"):
                    col_type = dataset.schema.get(col, "VARCHAR").upper()
                    if not any(
                        t in col_type for t in ["INT", "DOUBLE", "FLOAT", "DECIMAL", "NUMERIC", "REAL", "BIGINT"]
                    ):
                        raise ValueError(
                            f"Aggregation {agg_type_str} requires a numeric column, but '{col}' has type {col_type}"
                        )

    def execute(
        self,
        dataset: AnalyticalDataset,
        parameters: dict[str, Any],
        filters: Optional[Any] = None,
        sort_by: Optional[List[SortSpecification]] = None,
        limit: int = 1000,
        offset: int = 0,
    ) -> Tuple[List[str], List[dict[str, Any]], Optional[dict[str, Any]]]:
        # Normalize dimensions
        raw_dims = (
            parameters.get("dimensions")
            or parameters.get("dimension")
            or parameters.get("group_column")
        )
        dims = [raw_dims] if isinstance(raw_dims, str) else raw_dims

        # Normalize aggregations
        raw_aggs = parameters.get("aggregations")
        if not raw_aggs:
            metric = (
                parameters.get("metric")
                or parameters.get("aggregate_column")
                or parameters.get("column")
            )
            agg = parameters.get("aggregation") or "sum"
            if metric:
                raw_aggs = [{"column": metric, "agg_type": agg.upper()}]
            else:
                raw_aggs = [{"column": "*", "agg_type": "COUNT"}]

        agg_specs = [
            AggregationSpec(
                column=a["column"],
                agg_type=AggregationType(a["agg_type"].upper()),
                alias=a.get("alias"),
            )
            if isinstance(a, dict)
            else a
            for a in raw_aggs
        ]

        table_name = dataset.view_name
        group_cols_quoted = [SafeSQLBuilder.quote_identifier(d) for d in dims]
        group_cols_str = ", ".join(group_cols_quoted)

        agg_exprs = [SafeSQLBuilder.build_aggregation_expression(spec, dataset.columns) for spec in agg_specs]
        agg_exprs_str = ", ".join(agg_exprs)

        where_sql, params = SafeSQLBuilder.build_filter_clause(filters, dataset.columns)
        where_clause = f"WHERE {where_sql}" if where_sql else ""
        agg_aliases = [spec.alias for spec in agg_specs if spec.alias]
        default_agg_names = [f"{spec.column}_{spec.agg_type.value.lower()}" for spec in agg_specs if spec.column != "*"]
        valid_order_columns = list(dims) + agg_aliases + default_agg_names + ["count"]
        order_clause = SafeSQLBuilder.build_order_by(sort_by, valid_order_columns)

        sql = f"""
        SELECT
            {group_cols_str},
            {agg_exprs_str}
        FROM {table_name}
        {where_clause}
        GROUP BY {group_cols_str}
        {order_clause}
        LIMIT {limit} OFFSET {offset}
        """

        cols, rows = self._execute_sql(dataset, sql, params)
        summary = {
            "group_count": len(rows),
            "dimensions": dims,
            "aggregation_count": len(agg_specs),
        }
        return cols, ResultSanitizer.sanitize_rows(rows), summary


class CompareGroupsTool(AnalysisTool):
    """
    Compares metrics across discrete segments or categories with absolute and relative differences.
    """

    @property
    def metadata(self) -> AnalysisToolMetadata:
        return AnalysisToolMetadata(
            name="compare_groups",
            display_name="Compare Groups",
            description="Compares target metrics across specific category groups with delta and percent differences.",
            category="aggregation",
            required_params=["dimension", "metric"],
            optional_params=["groups", "aggregation"],
            input_schema={
                "type": "object",
                "properties": {
                    "dimension": {"type": "string", "description": "Dimension column defining the groups."},
                    "metric": {"type": "string", "description": "Numeric measure to compare."},
                    "groups": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional list of specific group values to compare.",
                    },
                    "aggregation": {
                        "type": "string",
                        "enum": ["SUM", "AVG", "COUNT", "MEDIAN", "MIN", "MAX"],
                        "default": "SUM",
                    },
                },
                "required": ["dimension", "metric"],
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
        dim = parameters.get("dimension")
        metric = parameters.get("metric")
        if not dim or not metric:
            raise ValueError("Parameters 'dimension' and 'metric' are required")
        SafeSQLBuilder.validate_identifier(dim, dataset.columns)
        SafeSQLBuilder.validate_identifier(metric, dataset.columns)

        col_type = dataset.schema.get(metric, "VARCHAR").upper()
        if not any(t in col_type for t in ["INT", "DOUBLE", "FLOAT", "DECIMAL", "NUMERIC", "REAL", "BIGINT"]):
            raise ValueError(f"Metric '{metric}' must be a numeric column, found {col_type}")

    def execute(
        self,
        dataset: AnalyticalDataset,
        parameters: dict[str, Any],
        filters: Optional[Any] = None,
        sort_by: Optional[List[SortSpecification]] = None,
        limit: int = 1000,
        offset: int = 0,
    ) -> Tuple[List[str], List[dict[str, Any]], Optional[dict[str, Any]]]:
        dim = parameters["dimension"]
        metric = parameters["metric"]
        agg = (parameters.get("aggregation") or "SUM").upper()
        target_groups = parameters.get("groups")

        quoted_dim = SafeSQLBuilder.quote_identifier(dim)
        quoted_metric = SafeSQLBuilder.quote_identifier(metric)
        table_name = dataset.view_name

        where_parts = []
        all_params = []

        if filters:
            w_sql, w_params = SafeSQLBuilder.build_filter_clause(filters, dataset.columns)
            if w_sql:
                where_parts.append(w_sql)
                all_params.extend(w_params)

        if target_groups and isinstance(target_groups, list) and len(target_groups) > 0:
            placeholders = ", ".join(["?"] * len(target_groups))
            where_parts.append(f"{quoted_dim} IN ({placeholders})")
            all_params.extend(target_groups)

        where_clause = f"WHERE {' AND '.join(where_parts)}" if where_parts else ""

        sql = f"""
        SELECT
            {quoted_dim} AS group_name,
            COUNT(*) AS record_count,
            {agg}({quoted_metric}) AS metric_value
        FROM {table_name}
        {where_clause}
        GROUP BY {quoted_dim}
        ORDER BY metric_value DESC
        LIMIT {limit}
        """

        cols, raw_rows = self._execute_sql(dataset, sql, all_params)

        # Compute comparison benchmarks (overall mean, benchmark group comparison)
        benchmark_val = raw_rows[0]["metric_value"] if raw_rows and raw_rows[0]["metric_value"] is not None else 0.0

        comparison_rows = []
        for r in raw_rows:
            val = r.get("metric_value")
            delta = (val - benchmark_val) if val is not None else None
            pct_diff = (
                ((val - benchmark_val) / abs(benchmark_val) * 100.0)
                if (val is not None and benchmark_val != 0)
                else 0.0
            )

            comparison_rows.append(
                {
                    "group_name": r.get("group_name"),
                    "record_count": r.get("record_count"),
                    "metric_value": val,
                    "delta_from_top": delta,
                    "percent_difference_from_top": round(pct_diff, 2) if pct_diff is not None else None,
                }
            )

        output_cols = ["group_name", "record_count", "metric_value", "delta_from_top", "percent_difference_from_top"]
        summary = {
            "dimension": dim,
            "metric": metric,
            "aggregation": agg,
            "compared_groups_count": len(comparison_rows),
            "top_group": comparison_rows[0]["group_name"] if comparison_rows else None,
        }
        return output_cols, ResultSanitizer.sanitize_rows(comparison_rows), summary
