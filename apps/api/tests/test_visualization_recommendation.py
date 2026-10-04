"""Unit tests for the Deterministic Visualization Recommendation Engine."""

from app.visualization.engine.rules import recommendation_engine
from app.visualization.schemas import ChartType


def test_recommend_kpi_for_single_scalar():
    """Single numeric scalar metric should recommend KPI card."""
    spec = recommendation_engine.recommend(
        operation="aggregate",
        columns=["total_revenue"],
        rows=[{"total_revenue": 1820000.0}],
        summary={"total_revenue": 1820000.0},
        parameters={"metric": "revenue", "aggregation": "sum"},
        dataset_id="ds-1",
        dataset_version_id="ver-1",
        analysis_id="an-101",
    )

    assert spec.chart_type == ChartType.KPI
    assert spec.options.get("kpi_value") == 1820000.0
    assert "KPI" in spec.explanation
    assert ChartType.KPI in spec.available_chart_types
    assert ChartType.TABLE in spec.available_chart_types


def test_recommend_line_chart_for_temporal_series():
    """Temporal column + numeric column should recommend Line chart."""
    rows = [
        {"order_date": "2025-01-01", "revenue": 12000},
        {"order_date": "2025-02-01", "revenue": 18500},
        {"order_date": "2025-03-01", "revenue": 24100},
    ]
    spec = recommendation_engine.recommend(
        operation="group_by",
        columns=["order_date", "revenue"],
        rows=rows,
        parameters={"dimensions": ["order_date"], "metric": "revenue"},
        dataset_id="ds-1",
        dataset_version_id="ver-1",
        analysis_id="an-102",
    )

    assert spec.chart_type == ChartType.LINE
    assert spec.x_axis == "order_date"
    assert spec.y_axis == "revenue"
    assert ChartType.AREA in spec.available_chart_types
    assert ChartType.BAR in spec.available_chart_types


def test_recommend_donut_for_small_composition():
    """Categorical + numeric measure with 3-6 non-negative categories should recommend Donut chart."""
    rows = [
        {"region": "North", "revenue": 50000},
        {"region": "South", "revenue": 45000},
        {"region": "East", "revenue": 30000},
        {"region": "West", "revenue": 25000},
    ]
    spec = recommendation_engine.recommend(
        operation="group_by",
        columns=["region", "revenue"],
        rows=rows,
        parameters={"dimensions": ["region"], "metric": "revenue"},
        dataset_id="ds-1",
        dataset_version_id="ver-1",
        analysis_id="an-103",
    )

    assert spec.chart_type == ChartType.DONUT
    assert spec.x_axis == "region"
    assert spec.y_axis == "revenue"
    assert ChartType.PIE in spec.available_chart_types
    assert ChartType.BAR in spec.available_chart_types


def test_recommend_bar_chart_for_moderate_categories():
    """Categorical + numeric measure with > 6 categories (<= 20) should recommend Bar chart."""
    rows = [{"category": f"Cat_{i}", "sales": 1000 * i} for i in range(1, 9)]
    spec = recommendation_engine.recommend(
        operation="group_by",
        columns=["category", "sales"],
        rows=rows,
        parameters={"dimensions": ["category"], "metric": "sales"},
        dataset_id="ds-1",
        dataset_version_id="ver-1",
        analysis_id="an-104",
    )

    assert spec.chart_type in (ChartType.BAR, ChartType.HORIZONTAL_BAR)
    assert spec.cardinality == 8


def test_recommend_horizontal_bar_for_long_labels():
    """Categories with long string labels should recommend Horizontal Bar chart."""
    rows = [
        {"department": "Enterprise Infrastructure & Cloud Services", "budget": 950000},
        {"department": "Customer Experience & Relationship Operations", "budget": 620000},
        {"department": "Strategic Research & Product Innovation", "budget": 840000},
    ]
    spec = recommendation_engine.recommend(
        operation="group_by",
        columns=["department", "budget"],
        rows=rows,
        parameters={"dimensions": ["department"], "metric": "budget"},
        dataset_id="ds-1",
        dataset_version_id="ver-1",
        analysis_id="an-105",
    )

    assert spec.chart_type == ChartType.HORIZONTAL_BAR
    assert spec.x_axis == "budget"
    assert spec.y_axis == "department"


def test_recommend_scatter_for_two_numerics():
    """Two numeric variables with no temporal or categorical dimension should recommend Scatter Plot."""
    rows = [
        {"advertising_spend": 5000, "revenue": 45000},
        {"advertising_spend": 8000, "revenue": 72000},
        {"advertising_spend": 12000, "revenue": 105000},
    ]
    spec = recommendation_engine.recommend(
        operation="correlation",
        columns=["advertising_spend", "revenue"],
        rows=rows,
        parameters={"column1": "advertising_spend", "column2": "revenue"},
        dataset_id="ds-1",
        dataset_version_id="ver-1",
        analysis_id="an-106",
    )

    assert spec.chart_type == ChartType.SCATTER
    assert spec.x_axis == "advertising_spend"
    assert spec.y_axis == "revenue"


def test_recommend_boxplot_for_five_number_summary():
    """Statistical distribution summary containing quartiles should recommend Box Plot."""
    summary = {
        "min": 100.0,
        "q1": 250.0,
        "median": 450.0,
        "q3": 680.0,
        "max": 1200.0,
        "mean": 480.0,
        "std_dev": 210.0,
    }
    spec = recommendation_engine.recommend(
        operation="distribution",
        columns=["price"],
        rows=[{"price": 450.0}],
        summary=summary,
        parameters={"column": "price"},
        dataset_id="ds-1",
        dataset_version_id="ver-1",
        analysis_id="an-107",
    )

    assert spec.chart_type == ChartType.BOXPLOT
    assert spec.options.get("median") == 450.0
    assert spec.options.get("q1") == 250.0


def test_recommend_table_fallback_for_high_cardinality():
    """High cardinality (> 20 categories) should fall back to Table."""
    rows = [{"item_id": f"ITEM_{i:04d}", "units_sold": 50 + i} for i in range(25)]
    spec = recommendation_engine.recommend(
        operation="group_by",
        columns=["item_id", "units_sold"],
        rows=rows,
        parameters={"dimensions": ["item_id"], "metric": "units_sold"},
        dataset_id="ds-1",
        dataset_version_id="ver-1",
        analysis_id="an-108",
    )

    assert spec.chart_type == ChartType.TABLE
    assert spec.cardinality == 25


def test_user_preference_override():
    """User preferred chart type within compatible alternatives should adapt specification."""
    rows = [
        {"region": "North", "revenue": 50000},
        {"region": "South", "revenue": 45000},
        {"region": "East", "revenue": 30000},
    ]
    # Default is DONUT for 3 items, user requests BAR
    spec = recommendation_engine.recommend(
        operation="group_by",
        columns=["region", "revenue"],
        rows=rows,
        preferred_chart_type=ChartType.BAR,
        dataset_id="ds-1",
        dataset_version_id="ver-1",
        analysis_id="an-109",
    )

    assert spec.chart_type == ChartType.BAR
    assert spec.x_axis == "region"
    assert spec.y_axis == "revenue"
