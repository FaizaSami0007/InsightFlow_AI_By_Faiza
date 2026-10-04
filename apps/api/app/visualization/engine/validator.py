"""Chart Validator enforcing security, schema integrity, column existence, and cardinality constraints."""

import re
from typing import Any, Dict, List, Optional

from app.visualization.engine.registry import chart_registry
from app.visualization.engine.rules import recommendation_engine
from app.visualization.schemas import (
    ChartType,
    VisualizationSpec,
    VisualizationValidationResult,
)


class ChartValidator:
    """
    Validates candidate visualization specifications against source analytical results.
    Prevents unauthorized field references, type mismatches, XSS/script injection, and illegal charts.
    """

    # Unsafe code patterns (XSS, script injection)
    DANGEROUS_PATTERNS = [
        re.compile(r"<script.*?>", re.IGNORECASE),
        re.compile(r"javascript:", re.IGNORECASE),
        re.compile(r"onload=", re.IGNORECASE),
        re.compile(r"onerror=", re.IGNORECASE),
        re.compile(r"eval\(", re.IGNORECASE),
        re.compile(r"<iframe.*?>", re.IGNORECASE),
    ]

    @classmethod
    def validate(
        cls,
        spec: VisualizationSpec,
        operation: str,
        columns: List[str],
        rows: List[Dict[str, Any]],
        summary: Optional[Dict[str, Any]] = None,
        dataset_id: str = "",
        dataset_version_id: str = "",
        analysis_id: str = "",
    ) -> VisualizationValidationResult:
        errors: List[str] = []
        warnings: List[str] = []
        row_count = len(rows)
        summary = summary or {}

        # 1. Security & Script Sanitization Check
        for field_val in [spec.title, spec.subtitle, spec.explanation, spec.format]:
            if field_val and any(p.search(field_val) for p in cls.DANGEROUS_PATTERNS):
                errors.append("Unsafe script or markup detected in visualization specification.")

        # 2. Chart Type Support
        defn = chart_registry.get(spec.chart_type)
        if not defn:
            errors.append(f"Unsupported chart type: '{spec.chart_type}'.")

        # 3. Column Existence Validation
        col_set = set(columns)
        inferred_types = recommendation_engine.analyze_columns(columns, rows)

        if spec.x_axis and spec.x_axis not in col_set:
            errors.append(f"X-axis column '{spec.x_axis}' does not exist in analytical result.")

        if spec.y_axis:
            y_cols = [spec.y_axis] if isinstance(spec.y_axis, str) else spec.y_axis
            for y in y_cols:
                if y not in col_set:
                    errors.append(f"Y-axis column '{y}' does not exist in analytical result.")

        if spec.series and spec.series not in col_set:
            errors.append(f"Series column '{spec.series}' does not exist in analytical result.")

        # 4. Axis Data Type & Semantic Compatibility
        if defn and not errors:
            # Check X-Axis Data Type
            if spec.x_axis and spec.x_axis in inferred_types:
                x_type = inferred_types[spec.x_axis]
                if x_type not in defn.allowed_x_types:
                    errors.append(
                        f"Chart '{spec.chart_type.value}' does not support X-axis data type '{x_type.value}' on column '{spec.x_axis}'."
                    )

            # Check Y-Axis Data Type
            if spec.y_axis:
                y_cols = [spec.y_axis] if isinstance(spec.y_axis, str) else spec.y_axis
                for y in y_cols:
                    if y in inferred_types:
                        y_type = inferred_types[y]
                        if y_type not in defn.allowed_y_types:
                            errors.append(
                                f"Chart '{spec.chart_type.value}' does not support Y-axis data type '{y_type.value}' on column '{y}'."
                            )

            # Check Cardinality & Negative Values
            if defn.max_cardinality and row_count > defn.max_cardinality:
                if spec.chart_type in (ChartType.PIE, ChartType.DONUT):
                    errors.append(
                        f"{spec.chart_type.value.title()} chart is unsuitable for {row_count} categories (maximum allowed is {defn.max_cardinality})."
                    )
                else:
                    warnings.append(
                        f"Result cardinality ({row_count}) exceeds recommended limit ({defn.max_cardinality}) for {spec.chart_type.value} chart."
                    )

            if defn.disallow_negative and spec.y_axis:
                y_cols = [spec.y_axis] if isinstance(spec.y_axis, str) else spec.y_axis
                for y in y_cols:
                    for r in rows:
                        val = r.get(y)
                        if isinstance(val, (int, float)) and val < 0:
                            errors.append(
                                f"{spec.chart_type.value.title()} chart cannot be rendered with negative values found in '{y}'."
                            )
                            break

            if defn.min_values and row_count < defn.min_values:
                warnings.append(
                    f"Histogram has only {row_count} data points (recommended minimum is {defn.min_values})."
                )

        # 5. Result Synthesis
        if errors:
            fallback = recommendation_engine.recommend(
                operation=operation,
                columns=columns,
                rows=rows,
                summary=summary,
                dataset_id=dataset_id,
                dataset_version_id=dataset_version_id,
                analysis_id=analysis_id,
            )
            fallback.is_fallback = True
            return VisualizationValidationResult(
                valid=False,
                errors=errors,
                warnings=warnings,
                validated_spec=None,
                fallback_spec=fallback,
            )

        # Valid Spec - fill available alternatives
        spec.cardinality = row_count
        if not spec.available_chart_types:
            rec = recommendation_engine.recommend(
                operation=operation,
                columns=columns,
                rows=rows,
                summary=summary,
                dataset_id=dataset_id,
                dataset_version_id=dataset_version_id,
                analysis_id=analysis_id,
            )
            spec.available_chart_types = rec.available_chart_types

        return VisualizationValidationResult(
            valid=True,
            errors=[],
            warnings=warnings,
            validated_spec=spec,
            fallback_spec=None,
        )


chart_validator = ChartValidator()
