"""Deterministic validator for Dashboard Plans and Dashboard Patches.

Ensures plans and patches strictly adhere to dataset schema, semantic roles,
registered analytical tools, visualization constraints, and layout boundaries.
"""

from typing import Dict, List, Set, Tuple

from app.analytics.engine.registry import analysis_registry
from app.dashboards.engine.layout import DashboardLayoutEngine
from app.dashboards.schemas import DashboardPatch, DashboardPlan, PatchOp, WidgetType
from app.database.models.dashboards import Dashboard
from app.database.models.profiling import DatasetProfile, SemanticColumn, SemanticRole
from app.visualization.schemas import ChartType


class DashboardPlanValidator:
    MIN_WIDGETS = 1
    MAX_WIDGETS = 12

    @classmethod
    def validate_plan(
        cls,
        plan: DashboardPlan,
        profile: DatasetProfile,
        semantic_columns: Dict[str, SemanticColumn],
    ) -> Tuple[bool, List[str], List[str]]:
        """
        Validates a candidate DashboardPlan against dataset profile and semantic definitions.
        Returns (is_valid, errors, warnings).
        """
        errors: List[str] = []
        warnings: List[str] = []

        # 1. Widget count bounds
        widget_count = len(plan.widgets)
        if widget_count < cls.MIN_WIDGETS:
            errors.append(f"Dashboard plan must contain at least {cls.MIN_WIDGETS} widget (found {widget_count})")
        if widget_count > cls.MAX_WIDGETS:
            errors.append(f"Dashboard plan exceeds maximum allowed widgets of {cls.MAX_WIDGETS} (found {widget_count})")

        # 2. Extract column catalog
        raw_cols = getattr(profile, "column_profiles", None) or getattr(profile, "columns", [])
        col_names: Set[str] = {col.column_name for col in raw_cols}

        measures: Set[str] = {
            col_name
            for col_name, sem in semantic_columns.items()
            if getattr(sem, "is_measure", False)
            or (getattr(sem, "inferred_role", None) == SemanticRole.MEASURE)
            or (getattr(sem, "role", None) == SemanticRole.MEASURE)
            or getattr(sem, "conceptual_type", "") in ["numeric", "currency", "integer", "float"]
        }
        dimensions: Set[str] = {
            col_name
            for col_name, sem in semantic_columns.items()
            if getattr(sem, "is_dimension", False)
            or (
                getattr(sem, "inferred_role", None)
                in [SemanticRole.DIMENSION, SemanticRole.CATEGORY, SemanticRole.IDENTIFIER]
            )
            or (getattr(sem, "role", None) in [SemanticRole.DIMENSION, SemanticRole.IDENTIFIER])
            or getattr(sem, "conceptual_type", "") in ["categorical", "boolean", "text"]
        }
        temporals: Set[str] = {
            col_name
            for col_name, sem in semantic_columns.items()
            if getattr(sem, "is_temporal", False)
            or (getattr(sem, "inferred_role", None) in [SemanticRole.DATE, SemanticRole.DATETIME])
            or (getattr(sem, "role", None) in [SemanticRole.DATE, SemanticRole.DATETIME])
            or getattr(sem, "conceptual_type", "") in ["datetime", "date", "timestamp"]
        }

        # 3. Tool registry validation
        available_ops = set(analysis_registry._tools.keys())

        # 4. Validate each widget
        signatures_seen: Set[str] = set()
        for idx, widget in enumerate(plan.widgets):
            w_prefix = f"Widget #{idx + 1} ('{widget.title}')"

            # Check operation
            if widget.operation not in available_ops:
                errors.append(f"{w_prefix}: operation '{widget.operation}' is not supported by analytics engine")
                continue

            params = widget.params or {}

            # Check referenced columns in params
            for param_key in [
                "group_column",
                "aggregate_column",
                "time_column",
                "date_column",
                "metric_column",
                "column",
            ]:
                if param_key in params and params[param_key]:
                    val = params[param_key]
                    if isinstance(val, str) and val not in col_names and val != "*":
                        errors.append(f"{w_prefix}: parameter '{param_key}' references non-existent column '{val}'")

            if "dimensions" in params and isinstance(params["dimensions"], list):
                for dim in params["dimensions"]:
                    if dim not in col_names:
                        errors.append(f"{w_prefix}: dimension '{dim}' does not exist in dataset")

            if "aggregations" in params and isinstance(params["aggregations"], list):
                for agg in params["aggregations"]:
                    col = agg.get("column") if isinstance(agg, dict) else getattr(agg, "column", None)
                    if col and col != "*" and col not in col_names:
                        errors.append(f"{w_prefix}: aggregation column '{col}' does not exist in dataset")

            if "columns" in params and isinstance(params["columns"], list):
                for col in params["columns"]:
                    if col not in col_names:
                        errors.append(f"{w_prefix}: references non-existent column in list '{col}'")

            # Validate widget type & operation semantics
            if widget.widget_type == WidgetType.KPI:
                agg_col = (
                    params.get("aggregate_column")
                    or params.get("column")
                    or (params.get("columns")[0] if params.get("columns") else None)
                )
                if agg_col and agg_col not in measures and agg_col not in col_names:
                    warnings.append(f"{w_prefix}: KPI metric '{agg_col}' is not classified as a numeric measure")

            elif widget.operation == "time_series_summary":
                time_col = params.get("time_column") or params.get("date_column")
                if not time_col:
                    errors.append(f"{w_prefix}: time_series_summary requires 'date_column'")
                elif time_col not in temporals and time_col not in col_names:
                    errors.append(f"{w_prefix}: date_column '{time_col}' is not a temporal column")

            elif widget.operation == "group_by":
                group_col = params.get("group_column") or (
                    params.get("dimensions")[0] if params.get("dimensions") else None
                )
                if not group_col:
                    errors.append(f"{w_prefix}: group_by requires 'dimensions'")
                elif group_col not in col_names:
                    errors.append(f"{w_prefix}: dimension '{group_col}' does not exist")
                elif group_col not in dimensions:
                    warnings.append(f"{w_prefix}: column '{group_col}' is not classified as a dimension")

            # Check for redundancy (duplicate analytical signature)
            sig = f"{widget.operation}:{widget.title}:{widget.preferred_chart_type}"
            if sig in signatures_seen:
                warnings.append(
                    f"{w_prefix}: Duplicate analytical computation detected; consider combining or differentiating"
                )
            signatures_seen.add(sig)

        # 5. Validate suggested filters
        for f_col in plan.suggested_filters:
            if f_col not in col_names:
                warnings.append(f"Suggested filter column '{f_col}' does not exist in dataset")

        return len(errors) == 0, errors, warnings


class DashboardPatchValidator:
    @classmethod
    def validate_patch(
        cls,
        patch: DashboardPatch,
        dashboard: Dashboard,
        profile: DatasetProfile,
        semantic_columns: Dict[str, SemanticColumn],
    ) -> Tuple[bool, List[str]]:
        """
        Validates a single patch mutation against the target dashboard and dataset.
        """
        errors: List[str] = []
        raw_cols = getattr(profile, "column_profiles", None) or getattr(profile, "columns", [])
        col_names = {col.column_name for col in raw_cols}
        existing_widget_ids = {w.id for w in dashboard.widgets}

        if patch.op == PatchOp.ADD_WIDGET:
            w_dict = patch.params.get("widget", {})
            title = w_dict.get("title")
            op_name = w_dict.get("operation")
            if not title:
                errors.append("ADD_WIDGET requires widget 'title'")
            if not op_name:
                errors.append("ADD_WIDGET requires widget 'operation'")
            elif op_name not in analysis_registry._tools:
                errors.append(f"ADD_WIDGET operation '{op_name}' is not supported")

            if len(dashboard.widgets) >= DashboardPlanValidator.MAX_WIDGETS:
                errors.append(
                    f"Cannot add widget: Dashboard already has maximum of {DashboardPlanValidator.MAX_WIDGETS} widgets"
                )

        elif patch.op == PatchOp.REMOVE_WIDGET:
            if not patch.widget_id or patch.widget_id not in existing_widget_ids:
                errors.append(f"REMOVE_WIDGET: Widget '{patch.widget_id}' not found in dashboard")

        elif patch.op in [PatchOp.MOVE_WIDGET, PatchOp.RESIZE_WIDGET]:
            if not patch.widget_id or patch.widget_id not in existing_widget_ids:
                errors.append(f"{patch.op}: Widget '{patch.widget_id}' not found in dashboard")
            else:
                x = patch.params.get("grid_x")
                y = patch.params.get("grid_y")
                w = patch.params.get("grid_w")
                h = patch.params.get("grid_h")
                if x is not None and (x < 0 or x >= DashboardLayoutEngine.GRID_COLUMNS_DESKTOP):
                    errors.append(f"grid_x {x} out of range (0-11)")
                if y is not None and y < 0:
                    errors.append(f"grid_y {y} cannot be negative")
                if w is not None and (w < 1 or w > DashboardLayoutEngine.GRID_COLUMNS_DESKTOP):
                    errors.append(f"grid_w {w} out of range (1-12)")
                if h is not None and (h < 1 or h > 24):
                    errors.append(f"grid_h {h} out of range (1-24)")

        elif patch.op == PatchOp.CHANGE_CHART:
            if not patch.widget_id or patch.widget_id not in existing_widget_ids:
                errors.append(f"CHANGE_CHART: Widget '{patch.widget_id}' not found")
            chart_type_str = patch.params.get("chart_type")
            try:
                ChartType(chart_type_str)
            except (ValueError, TypeError):
                errors.append(f"Invalid chart_type '{chart_type_str}'")

        elif patch.op == PatchOp.CHANGE_FILTER:
            f_col = patch.params.get("column_name")
            if f_col and f_col not in col_names:
                errors.append(f"CHANGE_FILTER: column '{f_col}' not found in dataset")

        elif patch.op == PatchOp.RENAME_DASHBOARD:
            new_name = patch.params.get("name")
            if not new_name or len(new_name.strip()) == 0:
                errors.append("RENAME_DASHBOARD: 'name' cannot be empty")

        return len(errors) == 0, errors
