"""Deterministic 12-column Grid Layout Engine for InsightFlow Dashboards.

Computes collision-free positioning, bounds checking, automatic flow packing,
and responsive column transformations (Desktop 12-col, Tablet 8-col, Mobile stacked).
"""

from typing import Any, Dict, List, Tuple

from app.dashboards.schemas import LayoutPosition, WidgetType


class DashboardLayoutEngine:
    GRID_COLUMNS_DESKTOP = 12
    GRID_COLUMNS_TABLET = 8
    GRID_COLUMNS_MOBILE = 1

    # Standard default dimensions based on widget type
    DEFAULT_SIZES = {
        WidgetType.KPI: {"w": 3, "h": 2},
        WidgetType.CHART: {"w": 6, "h": 4},
        WidgetType.TABLE: {"w": 12, "h": 5},
    }

    @classmethod
    def get_default_size(cls, widget_type: WidgetType) -> Dict[str, int]:
        return cls.DEFAULT_SIZES.get(widget_type, {"w": 6, "h": 4})

    @classmethod
    def compute_auto_layout(
        cls,
        widgets: List[Dict[str, Any]],
        columns: int = GRID_COLUMNS_DESKTOP,
    ) -> List[Dict[str, Any]]:
        """
        Arranges widgets sequentially in a row-packing grid without overlaps.
        Widgets with explicit (w, h) are respected; otherwise defaults are assigned.
        Widgets are grouped by visual hierarchy (KPIs top, charts middle, tables bottom)
        unless positions are already partially defined.
        """

        # Sort widgets to place KPIs first, then charts, then tables
        def sort_priority(w: Dict[str, Any]) -> int:
            wtype = w.get("widget_type")
            if wtype == WidgetType.KPI or wtype == "kpi":
                return 0
            if wtype == WidgetType.TABLE or wtype == "table":
                return 2
            return 1

        ordered_widgets = sorted(widgets, key=sort_priority)

        # 2D occupied grid tracker: occupied[(x, y)] = True
        occupied: Dict[Tuple[int, int], bool] = {}
        layout_results: List[Dict[str, Any]] = []

        for widget in ordered_widgets:
            wtype_val = widget.get("widget_type", "chart")
            try:
                wtype = WidgetType(wtype_val)
            except ValueError:
                wtype = WidgetType.CHART

            default_dim = cls.get_default_size(wtype)
            w = int(widget.get("grid_w") or default_dim["w"])
            h = int(widget.get("grid_h") or default_dim["h"])

            # Clamp width to available columns
            w = max(1, min(columns, w))
            h = max(1, h)

            # Find first available (x, y) slot that can fit (w, h)
            placed_x = 0
            placed_y = 0
            found = False

            test_y = 0
            while not found:
                for test_x in range(0, columns - w + 1):
                    # Check if region [test_x, test_x + w) x [test_y, test_y + h) is free
                    collides = False
                    for dx in range(w):
                        for dy in range(h):
                            if occupied.get((test_x + dx, test_y + dy)):
                                collides = True
                                break
                        if collides:
                            break

                    if not collides:
                        placed_x = test_x
                        placed_y = test_y
                        found = True
                        break
                if not found:
                    test_y += 1

            # Mark region as occupied
            for dx in range(w):
                for dy in range(h):
                    occupied[(placed_x + dx, placed_y + dy)] = True

            placed_widget = dict(widget)
            placed_widget["grid_x"] = placed_x
            placed_widget["grid_y"] = placed_y
            placed_widget["grid_w"] = w
            placed_widget["grid_h"] = h
            layout_results.append(placed_widget)

        return layout_results

    @classmethod
    def validate_layout(
        cls,
        positions: List[LayoutPosition],
        columns: int = GRID_COLUMNS_DESKTOP,
    ) -> Tuple[bool, List[str]]:
        """
        Validates layout positions for bounds errors and collisions.
        """
        errors: List[str] = []

        for i, pos in enumerate(positions):
            if pos.x < 0 or pos.x >= columns:
                errors.append(f"Widget {i} x position {pos.x} is out of bounds (0-{columns - 1})")
            if pos.y < 0:
                errors.append(f"Widget {i} y position {pos.y} is negative")
            if pos.w < 1 or pos.w > columns:
                errors.append(f"Widget {i} width {pos.w} is out of range (1-{columns})")
            if pos.x + pos.w > columns:
                errors.append(f"Widget {i} overflows grid width: x({pos.x}) + w({pos.w}) > {columns}")
            if pos.h < 1 or pos.h > 24:
                errors.append(f"Widget {i} height {pos.h} is invalid (1-24)")

        # Check for overlaps
        for i in range(len(positions)):
            p1 = positions[i]
            for j in range(i + 1, len(positions)):
                p2 = positions[j]
                if p1.x < p2.x + p2.w and p1.x + p1.w > p2.x and p1.y < p2.y + p2.h and p1.y + p1.h > p2.y:
                    errors.append(f"Widgets {i} and {j} overlap in grid space")

        return len(errors) == 0, errors

    @classmethod
    def reflow_compact(
        cls,
        widgets: List[Dict[str, Any]],
        columns: int = GRID_COLUMNS_DESKTOP,
    ) -> List[Dict[str, Any]]:
        """
        Gravity pull towards y=0: shifts widgets upward into free gaps while preserving x order.
        """
        # Sort by y first, then x
        sorted_widgets = sorted(
            widgets,
            key=lambda w: (w.get("grid_y", 0), w.get("grid_x", 0)),
        )

        occupied: Dict[Tuple[int, int], bool] = {}
        compacted: List[Dict[str, Any]] = []

        for w in sorted_widgets:
            x = int(w.get("grid_x", 0))
            w_val = int(w.get("grid_w", 6))
            h_val = int(w.get("grid_h", 4))

            # Clamp width to columns
            w_val = max(1, min(columns, w_val))
            x = max(0, min(columns - w_val, x))

            # Pull y upward as much as possible
            target_y = 0
            while True:
                collides = False
                for dx in range(w_val):
                    for dy in range(h_val):
                        if occupied.get((x + dx, target_y + dy)):
                            collides = True
                            break
                    if collides:
                        break
                if not collides:
                    break
                target_y += 1

            # Mark occupied
            for dx in range(w_val):
                for dy in range(h_val):
                    occupied[(x + dx, target_y + dy)] = True

            new_w = dict(w)
            new_w["grid_x"] = x
            new_w["grid_y"] = target_y
            new_w["grid_w"] = w_val
            new_w["grid_h"] = h_val
            compacted.append(new_w)

        return compacted
