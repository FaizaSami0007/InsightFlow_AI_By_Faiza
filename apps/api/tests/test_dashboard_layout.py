"""Unit tests for 12-column Grid Layout Engine."""

from app.dashboards.engine.layout import DashboardLayoutEngine
from app.dashboards.schemas import LayoutPosition


def test_layout_engine_kpis_and_charts():
    widgets = [
        {"widget_type": "kpi", "title": "KPI 1"},
        {"widget_type": "kpi", "title": "KPI 2"},
        {"widget_type": "kpi", "title": "KPI 3"},
        {"widget_type": "kpi", "title": "KPI 4"},
        {"widget_type": "chart", "title": "Chart 1"},
        {"widget_type": "chart", "title": "Chart 2"},
        {"widget_type": "table", "title": "Table 1"},
    ]

    placed = DashboardLayoutEngine.compute_auto_layout(widgets)
    assert len(placed) == 7

    positions = [
        LayoutPosition(
            x=p["grid_x"],
            y=p["grid_y"],
            w=p["grid_w"],
            h=p["grid_h"],
        )
        for p in placed
    ]

    is_valid, errors = DashboardLayoutEngine.validate_layout(positions)
    assert is_valid is True, f"Layout validation failed: {errors}"

    # Check that KPIs are in row y=0
    kpis = [p for p in placed if p["widget_type"] == "kpi"]
    for k in kpis:
        assert k["grid_y"] == 0
        assert k["grid_w"] == 3


def test_layout_engine_collision_detection():
    # Intentionally overlapping positions
    positions = [
        LayoutPosition(x=0, y=0, w=6, h=4),
        LayoutPosition(x=4, y=2, w=6, h=4),  # Overlaps with (0,0,6,4)
    ]

    is_valid, errors = DashboardLayoutEngine.validate_layout(positions)
    assert is_valid is False
    assert any("overlap" in e for e in errors)


def test_layout_engine_out_of_bounds():
    positions = [
        LayoutPosition(x=8, y=0, w=6, h=4),  # x(8) + w(6) = 14 > 12
    ]

    is_valid, errors = DashboardLayoutEngine.validate_layout(positions)
    assert is_valid is False
    assert any("overflows grid width" in e for e in errors)


def test_layout_engine_reflow_compact():
    widgets = [
        {"id": "w1", "grid_x": 0, "grid_y": 0, "grid_w": 6, "grid_h": 4},
        {"id": "w2", "grid_x": 6, "grid_y": 0, "grid_w": 6, "grid_h": 4},
        {"id": "w3", "grid_x": 0, "grid_y": 8, "grid_w": 12, "grid_h": 4},  # Gap at y=4..7
    ]

    compacted = DashboardLayoutEngine.reflow_compact(widgets)
    w3_compact = next(w for w in compacted if w["id"] == "w3")
    assert w3_compact["grid_y"] == 4  # Pulled up from y=8 to y=4
