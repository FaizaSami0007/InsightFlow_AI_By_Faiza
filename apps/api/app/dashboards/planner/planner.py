"""AI Dashboard Planner for InsightFlow AI.

Analyzes dataset semantics, statistical profiles, and user intent to construct
grounded, structured dashboard plans without generating any arbitrary code.
"""

import logging
from typing import Dict, List, Optional

from app.dashboards.planner.validator import DashboardPlanValidator
from app.dashboards.schemas import DashboardPlan, DashboardWidgetPlan, WidgetType
from app.database.models.profiling import DatasetProfile, SemanticColumn, SemanticRole
from app.visualization.schemas import ChartType

logger = logging.getLogger("insightflow.dashboards.planner")


class DashboardPlanner:
    """
    Constructs structured dashboard plans based on semantic intelligence,
    statistical profiles, data quality indicators, and natural language intent.
    """

    @classmethod
    def generate_plan(
        cls,
        dataset_id: str,
        dataset_version_id: str,
        profile: DatasetProfile,
        semantic_columns: Dict[str, SemanticColumn],
        intent: Optional[str] = None,
        purpose: Optional[str] = None,
        min_widgets: int = 3,
        max_widgets: int = 8,
    ) -> DashboardPlan:
        """
        Creates a validated, structured dashboard plan.
        Uses grounded heuristic planning backed by AI semantic analysis.
        """
        # 1. Categorize columns by semantic role and data quality
        measures: List[str] = []
        dimensions: List[str] = []
        temporals: List[str] = []
        identifiers: List[str] = []

        raw_cols = getattr(profile, "column_profiles", None) or getattr(profile, "columns", [])
        col_profiles = {cp.column_name: cp for cp in raw_cols}

        for col_name, sem in semantic_columns.items():
            cp = col_profiles.get(col_name)
            null_pct = cp.null_percentage if cp and cp.null_percentage is not None else 0.0

            # Exclude low quality columns (> 60% nulls) from primary positions
            if null_pct > 60.0:
                continue

            role = getattr(sem, "user_role", None) or getattr(sem, "inferred_role", None) or getattr(sem, "role", None)
            is_meas = (
                getattr(sem, "is_measure", False)
                or role == SemanticRole.MEASURE
                or getattr(sem, "conceptual_type", "") in ["numeric", "currency", "integer", "float"]
            )
            is_temp = (
                getattr(sem, "is_temporal", False)
                or role in [SemanticRole.DATE, SemanticRole.DATETIME]
                or getattr(sem, "conceptual_type", "") in ["datetime", "date", "timestamp"]
            )
            is_ident = getattr(sem, "is_identifier", False) or role == SemanticRole.IDENTIFIER

            if is_meas:
                measures.append(col_name)
            elif is_temp:
                temporals.append(col_name)
            elif is_ident:
                identifiers.append(col_name)
            else:
                dimensions.append(col_name)

        # 2. Select primary metrics and dimensions
        primary_measure = measures[0] if measures else None
        secondary_measure = measures[1] if len(measures) > 1 else None
        primary_temporal = temporals[0] if temporals else None
        primary_dimension = dimensions[0] if dimensions else None
        secondary_dimension = dimensions[1] if len(dimensions) > 1 else None

        # 3. Determine dashboard title and purpose
        resolved_purpose = purpose or "General Analytical Overview"
        resolved_title = f"{resolved_purpose.title()} Dashboard"
        if intent:
            clean_intent = intent.strip().rstrip(".")
            if len(clean_intent) > 3 and not any(
                k in clean_intent.lower() for k in ["ignore", "drop", "hack", "script"]
            ):
                resolved_title = clean_intent.title()
                resolved_purpose = clean_intent

        # 4. Assemble widgets
        widgets: List[DashboardWidgetPlan] = []

        # Widget 1: Primary KPI
        if primary_measure:
            widgets.append(
                DashboardWidgetPlan(
                    title=f"Total {primary_measure.replace('_', ' ').title()}",
                    description=f"Aggregate sum of {primary_measure}",
                    widget_type=WidgetType.KPI,
                    operation="describe_dataset",
                    params={"columns": [primary_measure]},
                    preferred_chart_type=ChartType.KPI,
                    grid_w=4,
                    grid_h=2,
                )
            )

        # Widget 2: Secondary KPI or Count
        if secondary_measure:
            widgets.append(
                DashboardWidgetPlan(
                    title=f"Total {secondary_measure.replace('_', ' ').title()}",
                    description=f"Aggregate sum of {secondary_measure}",
                    widget_type=WidgetType.KPI,
                    operation="describe_dataset",
                    params={"columns": [secondary_measure]},
                    preferred_chart_type=ChartType.KPI,
                    grid_w=4,
                    grid_h=2,
                )
            )
        else:
            widgets.append(
                DashboardWidgetPlan(
                    title="Total Records",
                    description="Total row volume",
                    widget_type=WidgetType.KPI,
                    operation="describe_dataset",
                    params={},
                    preferred_chart_type=ChartType.KPI,
                    grid_w=4,
                    grid_h=2,
                )
            )

        # Widget 3: Time Series Trend (if temporal column exists)
        if primary_temporal and primary_measure:
            widgets.append(
                DashboardWidgetPlan(
                    title=f"{primary_measure.replace('_', ' ').title()} Over Time",
                    description=f"Chronological trend of {primary_measure} by {primary_temporal}",
                    widget_type=WidgetType.CHART,
                    operation="time_series_summary",
                    params={
                        "date_column": primary_temporal,
                        "metric_column": primary_measure,
                        "aggregation": "SUM",
                        "period": "month",
                    },
                    preferred_chart_type=ChartType.LINE,
                    grid_w=12,
                    grid_h=4,
                )
            )

        # Widget 4: Primary Dimension Breakdown
        if primary_dimension and primary_measure:
            widgets.append(
                DashboardWidgetPlan(
                    title=f"{primary_measure.replace('_', ' ').title()} by {primary_dimension.replace('_', ' ').title()}",
                    description=f"Categorical comparison across {primary_dimension}",
                    widget_type=WidgetType.CHART,
                    operation="group_by",
                    params={
                        "dimensions": [primary_dimension],
                        "aggregations": [{"column": primary_measure, "agg_type": "SUM"}],
                        "limit": 10,
                    },
                    preferred_chart_type=ChartType.BAR,
                    grid_w=6,
                    grid_h=4,
                )
            )
        elif primary_dimension:
            widgets.append(
                DashboardWidgetPlan(
                    title=f"Distribution by {primary_dimension.replace('_', ' ').title()}",
                    description=f"Frequency count of {primary_dimension}",
                    widget_type=WidgetType.CHART,
                    operation="frequency",
                    params={
                        "column": primary_dimension,
                        "top_n": 10,
                    },
                    preferred_chart_type=ChartType.BAR,
                    grid_w=6,
                    grid_h=4,
                )
            )

        # Widget 5: Secondary Dimension Breakdown or Distribution
        if secondary_dimension and primary_measure:
            widgets.append(
                DashboardWidgetPlan(
                    title=f"{primary_measure.replace('_', ' ').title()} by {secondary_dimension.replace('_', ' ').title()}",
                    description=f"Secondary breakdown across {secondary_dimension}",
                    widget_type=WidgetType.CHART,
                    operation="group_by",
                    params={
                        "dimensions": [secondary_dimension],
                        "aggregations": [{"column": primary_measure, "agg_type": "SUM"}],
                        "limit": 8,
                    },
                    preferred_chart_type=ChartType.DONUT,
                    grid_w=6,
                    grid_h=4,
                )
            )
        elif primary_measure:
            widgets.append(
                DashboardWidgetPlan(
                    title=f"{primary_measure.replace('_', ' ').title()} Distribution",
                    description=f"Statistical spread of {primary_measure}",
                    widget_type=WidgetType.CHART,
                    operation="distribution",
                    params={
                        "column": primary_measure,
                    },
                    preferred_chart_type=ChartType.HISTOGRAM,
                    grid_w=6,
                    grid_h=4,
                )
            )

        # Widget 6: Correlation or Comparison
        if primary_measure and secondary_measure:
            widgets.append(
                DashboardWidgetPlan(
                    title=f"{primary_measure.replace('_', ' ').title()} vs {secondary_measure.replace('_', ' ').title()}",
                    description=f"Bivariate relationship between {primary_measure} and {secondary_measure}",
                    widget_type=WidgetType.CHART,
                    operation="correlation",
                    params={
                        "columns": [primary_measure, secondary_measure],
                    },
                    preferred_chart_type=ChartType.SCATTER,
                    grid_w=6,
                    grid_h=4,
                )
            )

        # Widget 7: Detailed Summary Table
        if primary_dimension and primary_measure:
            widgets.append(
                DashboardWidgetPlan(
                    title=f"{primary_dimension.replace('_', ' ').title()} Performance Summary",
                    description=f"Tabular breakdown with complete metrics for {primary_dimension}",
                    widget_type=WidgetType.TABLE,
                    operation="group_by",
                    params={
                        "dimensions": [primary_dimension],
                        "aggregations": [{"column": primary_measure, "agg_type": "SUM"}],
                        "limit": 20,
                    },
                    preferred_chart_type=ChartType.TABLE,
                    grid_w=12,
                    grid_h=5,
                )
            )

        # Enforce widget bounds
        if len(widgets) > max_widgets:
            widgets = widgets[:max_widgets]

        # Suggested filters: primary categorical and temporal dimensions
        suggested_filters: List[str] = []
        if primary_temporal:
            suggested_filters.append(primary_temporal)
        if primary_dimension:
            suggested_filters.append(primary_dimension)
        if secondary_dimension and len(suggested_filters) < 3:
            suggested_filters.append(secondary_dimension)

        candidate_plan = DashboardPlan(
            title=resolved_title,
            purpose=resolved_purpose,
            dataset_id=dataset_id,
            dataset_version_id=dataset_version_id,
            widgets=widgets,
            suggested_filters=suggested_filters,
            reasoning_summary=(
                f"Generated {len(widgets)} analytical widgets prioritizing key metrics "
                f"({primary_measure or 'records'}) and dimensions ({primary_dimension or 'overall'})."
            ),
        )

        # Validate candidate plan
        is_valid, errors, warnings = DashboardPlanValidator.validate_plan(candidate_plan, profile, semantic_columns)

        if not is_valid:
            logger.warning(f"Initial plan had validation errors: {errors}. Attempting fallback clean plan.")
            # Fallback to minimal describe widget
            fallback_widget = DashboardWidgetPlan(
                title="Dataset Summary",
                description="General summary metrics",
                widget_type=WidgetType.KPI,
                operation="describe_dataset",
                params={},
                preferred_chart_type=ChartType.KPI,
                grid_w=12,
                grid_h=3,
            )
            return DashboardPlan(
                title=resolved_title,
                purpose=resolved_purpose,
                dataset_id=dataset_id,
                dataset_version_id=dataset_version_id,
                widgets=[fallback_widget],
                suggested_filters=[],
                reasoning_summary="Constructed safe fallback overview dashboard.",
            )

        return candidate_plan
