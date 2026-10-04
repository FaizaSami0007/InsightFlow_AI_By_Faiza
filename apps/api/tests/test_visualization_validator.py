"""Unit tests for the Chart Validator ensuring schema integrity and security."""

from app.visualization.engine.validator import chart_validator
from app.visualization.schemas import ChartType, VisualizationSpec


def test_validator_accepts_valid_bar_chart():
    spec = VisualizationSpec(
        chart_type=ChartType.BAR,
        title="Revenue by Region",
        x_axis="region",
        y_axis="revenue",
    )
    cols = ["region", "revenue"]
    rows = [{"region": "North", "revenue": 1000}, {"region": "South", "revenue": 2000}]

    result = chart_validator.validate(
        spec=spec,
        operation="group_by",
        columns=cols,
        rows=rows,
    )

    assert result.valid is True
    assert len(result.errors) == 0
    assert result.validated_spec is not None
    assert result.validated_spec.chart_type == ChartType.BAR


def test_validator_rejects_missing_column():
    spec = VisualizationSpec(
        chart_type=ChartType.BAR,
        title="Revenue by Region",
        x_axis="non_existent_column",
        y_axis="revenue",
    )
    cols = ["region", "revenue"]
    rows = [{"region": "North", "revenue": 1000}]

    result = chart_validator.validate(
        spec=spec,
        operation="group_by",
        columns=cols,
        rows=rows,
    )

    assert result.valid is False
    assert any("non_existent_column" in err for err in result.errors)
    assert result.fallback_spec is not None
    assert result.fallback_spec.is_fallback is True


def test_validator_rejects_non_numeric_y_axis():
    spec = VisualizationSpec(
        chart_type=ChartType.BAR,
        title="Invalid Chart",
        x_axis="region",
        y_axis="customer_name",  # String column cannot be Y axis of Bar
    )
    cols = ["region", "customer_name"]
    rows = [{"region": "North", "customer_name": "Alice"}, {"region": "South", "customer_name": "Bob"}]

    result = chart_validator.validate(
        spec=spec,
        operation="group_by",
        columns=cols,
        rows=rows,
    )

    assert result.valid is False
    assert any("does not support Y-axis data type" in err for err in result.errors)


def test_validator_rejects_pie_with_excessive_categories():
    spec = VisualizationSpec(
        chart_type=ChartType.PIE,
        title="Pie with 20 items",
        x_axis="category",
        y_axis="sales",
    )
    cols = ["category", "sales"]
    rows = [{"category": f"Item_{i}", "sales": 100} for i in range(20)]

    result = chart_validator.validate(
        spec=spec,
        operation="group_by",
        columns=cols,
        rows=rows,
    )

    assert result.valid is False
    assert any("unsuitable for 20 categories" in err for err in result.errors)


def test_validator_rejects_pie_with_negative_values():
    spec = VisualizationSpec(
        chart_type=ChartType.PIE,
        title="Profit Pie",
        x_axis="region",
        y_axis="profit",
    )
    cols = ["region", "profit"]
    rows = [{"region": "North", "profit": 500}, {"region": "South", "profit": -200}]

    result = chart_validator.validate(
        spec=spec,
        operation="group_by",
        columns=cols,
        rows=rows,
    )

    assert result.valid is False
    assert any("negative values found" in err for err in result.errors)


def test_validator_rejects_script_injection_in_title():
    spec = VisualizationSpec(
        chart_type=ChartType.BAR,
        title="<script>alert('XSS')</script> Revenue",
        x_axis="region",
        y_axis="revenue",
    )
    cols = ["region", "revenue"]
    rows = [{"region": "North", "revenue": 1000}]

    result = chart_validator.validate(
        spec=spec,
        operation="group_by",
        columns=cols,
        rows=rows,
    )

    assert result.valid is False
    assert any("Unsafe script or markup detected" in err for err in result.errors)
