"""Deterministic Visualization Recommendation Engine implementing context-aware chart suitability rules."""

from typing import Any, Dict, List, Optional

from app.visualization.engine.registry import chart_registry
from app.visualization.schemas import (
    AxisDataType,
    ChartType,
    VisualizationProvenance,
    VisualizationSpec,
)


class RecommendationEngine:
    """
    Evaluates analytical results against deterministic visualization rules to recommend
    the optimal, semantically appropriate chart representation.
    """

    @classmethod
    def analyze_columns(
        cls,
        columns: List[str],
        rows: List[Dict[str, Any]],
    ) -> Dict[str, AxisDataType]:
        """Infers data types for all columns in the analytical result."""
        types: Dict[str, AxisDataType] = {}

        for col in columns:
            col_lower = col.lower()
            # Temporal keywords
            if any(k in col_lower for k in ["date", "time", "year", "month", "day", "quarter", "week", "created_at"]):
                types[col] = AxisDataType.TEMPORAL
                continue

            # Inspect actual values in rows
            values = [r.get(col) for r in rows if r.get(col) is not None]
            if not values:
                types[col] = AxisDataType.CATEGORICAL
                continue

            if all(isinstance(v, bool) for v in values):
                types[col] = AxisDataType.BOOLEAN
            elif all(isinstance(v, (int, float)) for v in values):
                types[col] = AxisDataType.NUMERIC
            else:
                types[col] = AxisDataType.CATEGORICAL

        return types

    @classmethod
    def recommend(
        cls,
        operation: str,
        columns: List[str],
        rows: List[Dict[str, Any]],
        summary: Optional[Dict[str, Any]] = None,
        parameters: Optional[Dict[str, Any]] = None,
        filters: Optional[Dict[str, Any]] = None,
        dataset_id: str = "",
        dataset_version_id: str = "",
        analysis_id: str = "",
        preferred_chart_type: Optional[ChartType] = None,
    ) -> VisualizationSpec:
        """
        Recommends the best chart specification for the analytical result.
        If preferred_chart_type is provided and valid, it adapts the recommendation.
        """
        row_count = len(rows)
        col_types = cls.analyze_columns(columns, rows)
        summary = summary or {}
        parameters = parameters or {}

        # Categorize columns by inferred type
        numeric_cols = [c for c, t in col_types.items() if t == AxisDataType.NUMERIC]
        temporal_cols = [c for c, t in col_types.items() if t == AxisDataType.TEMPORAL]
        categorical_cols = [c for c, t in col_types.items() if t in (AxisDataType.CATEGORICAL, AxisDataType.BOOLEAN)]

        # Check for non-negative values in numeric columns (important for Pie/Donut)
        all_numeric_non_negative = True
        for col in numeric_cols:
            for r in rows:
                v = r.get(col)
                if isinstance(v, (int, float)) and v < 0:
                    all_numeric_non_negative = False
                    break

        provenance = VisualizationProvenance(
            analysis_id=analysis_id,
            dataset_id=dataset_id,
            dataset_version_id=dataset_version_id,
            operation=operation,
            row_count=row_count,
        )

        title = cls._generate_title(operation, columns, parameters)
        subtitle = f"Analysis #{analysis_id[:8]} • {operation.replace('_', ' ').title()}" if analysis_id else None

        # Rule 1: Five-number summary / Boxplot
        if operation == "distribution" and all(
            k in summary for k in ["q1", "median", "q3", "min", "max"]
        ):
            spec = VisualizationSpec(
                chart_type=ChartType.BOXPLOT,
                title=title,
                subtitle=subtitle,
                y_axis=parameters.get("column") or (numeric_cols[0] if numeric_cols else None),
                options={
                    "min": summary.get("min"),
                    "q1": summary.get("q1"),
                    "median": summary.get("median"),
                    "q3": summary.get("q3"),
                    "max": summary.get("max"),
                    "mean": summary.get("mean"),
                    "std_dev": summary.get("std_dev"),
                },
                provenance=provenance,
                explanation="Statistical distribution with quartiles is best visualized as a Box Plot.",
                available_chart_types=[ChartType.BOXPLOT, ChartType.HISTOGRAM, ChartType.TABLE],
            )
            return cls._apply_preference_if_compatible(spec, preferred_chart_type, col_types, columns, rows)

        # Rule 2: Single Scalar Metric -> KPI
        if (
            operation in ("aggregate", "scalar")
            or (row_count == 1 and len(numeric_cols) == 1 and len(categorical_cols) == 0 and operation != "distribution")
        ):
            metric_col = numeric_cols[0] if numeric_cols else columns[0]
            val = rows[0].get(metric_col) if rows else summary.get(metric_col)
            spec = VisualizationSpec(
                chart_type=ChartType.KPI,
                title=title,
                subtitle=subtitle,
                y_axis=metric_col,
                options={
                    "kpi_value": val,
                    "kpi_label": metric_col.replace("_", " ").title(),
                },
                provenance=provenance,
                explanation="Single scalar metric is best represented as a high-impact KPI card.",
                available_chart_types=[ChartType.KPI, ChartType.TABLE],
            )
            return cls._apply_preference_if_compatible(spec, preferred_chart_type, col_types, columns, rows)

        # Rule 3: Histogram / Binned Distribution
        if operation in ("histogram", "distribution_bins") or (
            operation == "distribution" and "bins" in summary
        ):
            x_col = "bin_range" if "bin_range" in columns else (categorical_cols[0] if categorical_cols else columns[0])
            y_col = "count" if "count" in columns else (numeric_cols[0] if numeric_cols else columns[-1])
            spec = VisualizationSpec(
                chart_type=ChartType.HISTOGRAM,
                title=title,
                subtitle=subtitle,
                x_axis=x_col,
                y_axis=y_col,
                cardinality=row_count,
                options={"bins": summary.get("bins", [])},
                provenance=provenance,
                explanation="Frequency distribution across intervals is best visualized as a Histogram.",
                available_chart_types=[ChartType.HISTOGRAM, ChartType.BAR, ChartType.TABLE],
            )
            return cls._apply_preference_if_compatible(spec, preferred_chart_type, col_types, columns, rows)

        # Rule 4: Temporal Trend -> Line Chart / Area Chart
        if temporal_cols and numeric_cols:
            x_col = temporal_cols[0]
            y_col = numeric_cols[0] if len(numeric_cols) == 1 else numeric_cols
            available = [ChartType.LINE, ChartType.AREA, ChartType.BAR, ChartType.TABLE]
            spec = VisualizationSpec(
                chart_type=ChartType.LINE,
                title=title,
                subtitle=subtitle,
                x_axis=x_col,
                y_axis=y_col,
                series=categorical_cols[0] if categorical_cols else None,
                cardinality=row_count,
                sort="asc",
                provenance=provenance,
                explanation="Time-series data is best visualized as a continuous Line Chart.",
                available_chart_types=available,
            )
            return cls._apply_preference_if_compatible(spec, preferred_chart_type, col_types, columns, rows)

        # Rule 5: 2 Numeric Variables without Categorical / Temporal -> Scatter Plot
        if len(numeric_cols) >= 2 and not categorical_cols and not temporal_cols:
            spec = VisualizationSpec(
                chart_type=ChartType.SCATTER,
                title=title,
                subtitle=subtitle,
                x_axis=numeric_cols[0],
                y_axis=numeric_cols[1],
                cardinality=row_count,
                provenance=provenance,
                explanation="Numerical correlation between two variables is best visualized as a Scatter Plot.",
                available_chart_types=[ChartType.SCATTER, ChartType.TABLE],
            )
            return cls._apply_preference_if_compatible(spec, preferred_chart_type, col_types, columns, rows)

        # Rule 6: Categorical + Numeric Measures -> Bar / Horizontal Bar / Pie / Donut
        if categorical_cols and numeric_cols:
            cat_col = categorical_cols[0]
            num_col = numeric_cols[0]

            # Check average length of category labels
            avg_label_len = sum(len(str(r.get(cat_col, ""))) for r in rows) / max(row_count, 1)

            # Long category labels -> Horizontal Bar
            if avg_label_len > 12:
                spec = VisualizationSpec(
                    chart_type=ChartType.HORIZONTAL_BAR,
                    title=title,
                    subtitle=subtitle,
                    x_axis=num_col,
                    y_axis=cat_col,
                    cardinality=row_count,
                    provenance=provenance,
                    explanation="Categorical comparison with long labels is best visualized as a Horizontal Bar Chart.",
                    available_chart_types=[ChartType.HORIZONTAL_BAR, ChartType.BAR, ChartType.TABLE],
                )
                return cls._apply_preference_if_compatible(spec, preferred_chart_type, col_types, columns, rows)

            # Small composition (3 to 6 non-negative categories with short labels)
            if 3 <= row_count <= chart_registry.MAX_PIE_CATEGORIES and all_numeric_non_negative:
                spec = VisualizationSpec(
                    chart_type=ChartType.DONUT,
                    title=title,
                    subtitle=subtitle,
                    x_axis=cat_col,
                    y_axis=num_col,
                    cardinality=row_count,
                    provenance=provenance,
                    explanation=f"Part-to-whole composition with {row_count} categories is best visualized as a Donut Chart.",
                    available_chart_types=[ChartType.DONUT, ChartType.PIE, ChartType.BAR, ChartType.HORIZONTAL_BAR, ChartType.TABLE],
                )
                return cls._apply_preference_if_compatible(spec, preferred_chart_type, col_types, columns, rows)

            # Moderate Cardinality (<= 20 categories) -> Bar or Horizontal Bar
            if row_count <= chart_registry.MAX_BAR_CATEGORIES:
                is_horizontal = row_count > 8
                chart_t = ChartType.HORIZONTAL_BAR if is_horizontal else ChartType.BAR
                spec = VisualizationSpec(
                    chart_type=chart_t,
                    title=title,
                    subtitle=subtitle,
                    x_axis=num_col if is_horizontal else cat_col,
                    y_axis=cat_col if is_horizontal else num_col,
                    cardinality=row_count,
                    provenance=provenance,
                    explanation=f"Categorical comparison with {row_count} items is best visualized as a {'Horizontal ' if is_horizontal else ''}Bar Chart.",
                    available_chart_types=[
                        ChartType.BAR,
                        ChartType.HORIZONTAL_BAR,
                        ChartType.TABLE,
                        *([ChartType.DONUT, ChartType.PIE] if row_count <= chart_registry.MAX_PIE_CATEGORIES and all_numeric_non_negative else []),
                    ],
                )
                return cls._apply_preference_if_compatible(spec, preferred_chart_type, col_types, columns, rows)

        # Rule 7: High Cardinality (> 20) or Generic Multi-Column Result -> Table Fallback
        spec = VisualizationSpec(
            chart_type=ChartType.TABLE,
            title=title,
            subtitle=subtitle,
            cardinality=row_count,
            provenance=provenance,
            explanation=f"Result with {row_count} rows or multi-column structure is safest as a Data Table.",
            available_chart_types=[ChartType.TABLE, *([ChartType.BAR] if categorical_cols and numeric_cols else [])],
        )
        return cls._apply_preference_if_compatible(spec, preferred_chart_type, col_types, columns, rows)

    @classmethod
    def _apply_preference_if_compatible(
        cls,
        base_spec: VisualizationSpec,
        preferred_chart_type: Optional[ChartType],
        col_types: Dict[str, AxisDataType],
        columns: List[str],
        rows: List[Dict[str, Any]],
    ) -> VisualizationSpec:
        """If user or AI expressed a valid chart preference from available alternatives, adapt the spec."""
        if not preferred_chart_type or preferred_chart_type == base_spec.chart_type:
            return base_spec

        if preferred_chart_type not in base_spec.available_chart_types:
            # Not compatible, return base with explanation
            base_spec.is_fallback = False
            return base_spec

        numeric_cols = [c for c, t in col_types.items() if t == AxisDataType.NUMERIC]
        categorical_cols = [c for c, t in col_types.items() if t in (AxisDataType.CATEGORICAL, AxisDataType.BOOLEAN)]
        temporal_cols = [c for c, t in col_types.items() if t == AxisDataType.TEMPORAL]

        # Adapt axes based on target chart
        if preferred_chart_type == ChartType.HORIZONTAL_BAR:
            x_col = numeric_cols[0] if numeric_cols else columns[0]
            y_col = categorical_cols[0] if categorical_cols else (temporal_cols[0] if temporal_cols else columns[-1])
            base_spec.chart_type = ChartType.HORIZONTAL_BAR
            base_spec.x_axis = x_col
            base_spec.y_axis = y_col
            base_spec.explanation = "Rendered as requested: Horizontal Bar Chart."
        elif preferred_chart_type == ChartType.BAR:
            x_col = categorical_cols[0] if categorical_cols else (temporal_cols[0] if temporal_cols else columns[0])
            y_col = numeric_cols[0] if numeric_cols else columns[-1]
            base_spec.chart_type = ChartType.BAR
            base_spec.x_axis = x_col
            base_spec.y_axis = y_col
            base_spec.explanation = "Rendered as requested: Bar Chart."
        elif preferred_chart_type in (ChartType.PIE, ChartType.DONUT):
            x_col = categorical_cols[0] if categorical_cols else columns[0]
            y_col = numeric_cols[0] if numeric_cols else columns[-1]
            base_spec.chart_type = preferred_chart_type
            base_spec.x_axis = x_col
            base_spec.y_axis = y_col
            base_spec.explanation = f"Rendered as requested: {preferred_chart_type.value.title()} Chart."
        elif preferred_chart_type in (ChartType.LINE, ChartType.AREA):
            x_col = temporal_cols[0] if temporal_cols else (categorical_cols[0] if categorical_cols else columns[0])
            y_col = numeric_cols[0] if numeric_cols else columns[-1]
            base_spec.chart_type = preferred_chart_type
            base_spec.x_axis = x_col
            base_spec.y_axis = y_col
            base_spec.explanation = f"Rendered as requested: {preferred_chart_type.value.title()} Chart."
        elif preferred_chart_type == ChartType.TABLE:
            base_spec.chart_type = ChartType.TABLE
            base_spec.explanation = "Rendered as requested: Data Table view."

        return base_spec

    @classmethod
    def _generate_title(cls, operation: str, columns: List[str], parameters: Dict[str, Any]) -> str:
        """Generates a human-readable title describing the analytical result."""
        metric = parameters.get("metric") or parameters.get("column") or (columns[-1] if len(columns) > 1 else columns[0] if columns else "Data")
        group = parameters.get("group_by") or parameters.get("by") or (columns[0] if len(columns) > 1 else None)
        metric_fmt = str(metric).replace("_", " ").title()

        if group:
            group_fmt = str(group).replace("_", " ").title()
            return f"{metric_fmt} by {group_fmt}"

        if operation == "aggregate":
            agg = parameters.get("aggregation", "Total").upper()
            return f"{agg} {metric_fmt}"

        if operation == "correlation":
            col1 = str(parameters.get("column1", "X")).replace("_", " ").title()
            col2 = str(parameters.get("column2", "Y")).replace("_", " ").title()
            return f"Correlation between {col1} and {col2}"

        return f"{operation.replace('_', ' ').title()} of {metric_fmt}"


recommendation_engine = RecommendationEngine()
