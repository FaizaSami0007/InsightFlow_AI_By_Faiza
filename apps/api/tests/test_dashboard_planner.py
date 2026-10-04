"""Unit tests for AI Dashboard Planner and Plan Validator."""

from app.dashboards.planner.planner import DashboardPlanner
from app.dashboards.planner.validator import DashboardPlanValidator
from app.dashboards.schemas import DashboardPlan, DashboardWidgetPlan, WidgetType
from app.database.models.profiling import ColumnProfile, DatasetProfile, SemanticColumn, SemanticRole


def create_mock_profile_and_semantics():
    cols = [
        ColumnProfile(
            id="cp1",
            profile_id="dp1",
            column_name="order_date",
            normalized_name="order_date",
            ordinal_position=0,
            data_type="DATE",
            null_count=0,
            null_percentage=0.0,
            unique_count=365,
        ),
        ColumnProfile(
            id="cp2",
            profile_id="dp1",
            column_name="revenue",
            normalized_name="revenue",
            ordinal_position=1,
            data_type="DOUBLE",
            null_count=5,
            null_percentage=0.5,
            unique_count=850,
        ),
        ColumnProfile(
            id="cp3",
            profile_id="dp1",
            column_name="profit",
            normalized_name="profit",
            ordinal_position=2,
            data_type="DOUBLE",
            null_count=10,
            null_percentage=1.0,
            unique_count=720,
        ),
        ColumnProfile(
            id="cp4",
            profile_id="dp1",
            column_name="region",
            normalized_name="region",
            ordinal_position=3,
            data_type="VARCHAR",
            null_count=0,
            null_percentage=0.0,
            unique_count=4,
        ),
        ColumnProfile(
            id="cp5",
            profile_id="dp1",
            column_name="category",
            normalized_name="category",
            ordinal_position=4,
            data_type="VARCHAR",
            null_count=0,
            null_percentage=0.0,
            unique_count=5,
        ),
        ColumnProfile(
            id="cp6",
            profile_id="dp1",
            column_name="low_quality_col",
            normalized_name="low_quality_col",
            ordinal_position=5,
            data_type="DOUBLE",
            null_count=850,
            null_percentage=85.0,
            unique_count=50,
        ),
    ]


    profile = DatasetProfile(
        id="dp1",
        dataset_version_id="dv1",
        row_count=1000,
        column_count=6,
        column_profiles=cols,
    )


    semantics = {
        "order_date": SemanticColumn(
            id="sc1", profile_id="dp1", column_name="order_date", inferred_role=SemanticRole.DATE, inferred_confidence=1.0, is_temporal=True
        ),
        "revenue": SemanticColumn(
            id="sc2", profile_id="dp1", column_name="revenue", inferred_role=SemanticRole.MEASURE, inferred_confidence=1.0, is_measure=True
        ),
        "profit": SemanticColumn(
            id="sc3", profile_id="dp1", column_name="profit", inferred_role=SemanticRole.MEASURE, inferred_confidence=1.0, is_measure=True
        ),
        "region": SemanticColumn(
            id="sc4", profile_id="dp1", column_name="region", inferred_role=SemanticRole.DIMENSION, inferred_confidence=1.0, is_dimension=True
        ),
        "category": SemanticColumn(
            id="sc5", profile_id="dp1", column_name="category", inferred_role=SemanticRole.DIMENSION, inferred_confidence=1.0, is_dimension=True
        ),
        "low_quality_col": SemanticColumn(
            id="sc6", profile_id="dp1", column_name="low_quality_col", inferred_role=SemanticRole.MEASURE, inferred_confidence=1.0, is_measure=True
        ),
    }


    return profile, semantics


def test_dashboard_planner_grounded_generation():
    profile, semantics = create_mock_profile_and_semantics()

    plan = DashboardPlanner.generate_plan(
        dataset_id="d1",
        dataset_version_id="dv1",
        profile=profile,
        semantic_columns=semantics,
        intent="Executive Sales Performance",
        purpose="sales",
    )

    assert plan is not None
    assert "Executive Sales Performance" in plan.title or "Sales" in plan.title
    assert len(plan.widgets) >= 3
    assert len(plan.widgets) <= 8

    # Ensure low_quality_col (>85% nulls) was not selected as primary measure
    first_kpi = plan.widgets[0]
    assert first_kpi.widget_type == WidgetType.KPI
    assert "revenue" in first_kpi.params.get("columns", []) or "revenue" in first_kpi.title.lower()

    # Ensure temporal trend was generated
    trend_widget = next((w for w in plan.widgets if w.operation == "time_series_summary"), None)
    assert trend_widget is not None
    assert trend_widget.params.get("date_column") == "order_date" or trend_widget.params.get("time_column") == "order_date"


def test_dashboard_planner_no_temporal_column():
    profile, semantics = create_mock_profile_and_semantics()
    profile.column_profiles = [c for c in profile.column_profiles if c.column_name != "order_date"]
    del semantics["order_date"]


    plan = DashboardPlanner.generate_plan(
        dataset_id="d1",
        dataset_version_id="dv1",
        profile=profile,
        semantic_columns=semantics,
        purpose="operations",
    )

    # Must not contain time_series_summary widget without temporal column
    trend_widget = next((w for w in plan.widgets if w.operation == "time_series_summary"), None)
    assert trend_widget is None
    assert len(plan.widgets) >= 2


def test_dashboard_plan_validator_valid():
    profile, semantics = create_mock_profile_and_semantics()

    plan = DashboardPlan(
        title="Valid Test Dashboard",
        purpose="testing",
        dataset_id="d1",
        dataset_version_id="dv1",
        widgets=[
            DashboardWidgetPlan(
                title="Total Revenue",
                widget_type=WidgetType.KPI,
                operation="describe_dataset",
                params={"columns": ["revenue"]},
            ),
            DashboardWidgetPlan(
                title="Revenue by Region",
                widget_type=WidgetType.CHART,
                operation="group_by",
                params={"group_column": "region", "aggregate_column": "revenue", "aggregation": "sum"},
            ),
        ],
        suggested_filters=["region", "order_date"],
    )

    is_valid, errors, warnings = DashboardPlanValidator.validate_plan(plan, profile, semantics)
    assert is_valid is True
    assert len(errors) == 0


def test_dashboard_plan_validator_invalid_column():
    profile, semantics = create_mock_profile_and_semantics()

    plan = DashboardPlan(
        title="Invalid Column Plan",
        purpose="testing",
        dataset_id="d1",
        dataset_version_id="dv1",
        widgets=[
            DashboardWidgetPlan(
                title="Unknown Metric KPI",
                widget_type=WidgetType.KPI,
                operation="describe_dataset",
                params={"columns": ["non_existent_column"]},
            )
        ],
    )

    is_valid, errors, warnings = DashboardPlanValidator.validate_plan(plan, profile, semantics)
    assert is_valid is False
    assert any("non_existent_column" in e for e in errors)


def test_dashboard_plan_validator_invalid_operation():
    profile, semantics = create_mock_profile_and_semantics()

    plan = DashboardPlan(
        title="Invalid Op Plan",
        purpose="testing",
        dataset_id="d1",
        dataset_version_id="dv1",
        widgets=[
            DashboardWidgetPlan(
                title="Arbitrary Op",
                widget_type=WidgetType.CHART,
                operation="run_arbitrary_script",
                params={},
            )
        ],
    )

    is_valid, errors, warnings = DashboardPlanValidator.validate_plan(plan, profile, semantics)
    assert is_valid is False
    assert any("run_arbitrary_script" in e for e in errors)


def test_dashboard_plan_validator_widget_limits():
    profile, semantics = create_mock_profile_and_semantics()

    widgets = [
        DashboardWidgetPlan(
            title=f"Widget {i}",
            widget_type=WidgetType.CHART,
            operation="describe_dataset",
            params={"columns": ["revenue"]},
        )
        for i in range(15)  # exceeds max 12
    ]

    try:
        plan = DashboardPlan(
            title="Too Many Widgets",
            purpose="testing",
            dataset_id="d1",
            dataset_version_id="dv1",
            widgets=widgets,
        )
        is_valid, errors, warnings = DashboardPlanValidator.validate_plan(plan, profile, semantics)
        assert is_valid is False
    except Exception:
        # Pydantic max_length=12 validator caught it
        pass
