# Phase 8 — Deterministic 12-Column Layout Engine

## 1. Grid Specifications

The layout engine positions widgets within a 12-column grid coordinate system:
- `grid_x`: Horizontal column index (0 to 11)
- `grid_y`: Vertical row offset (0 to N)
- `grid_w`: Column width span (3, 4, 6, 8, or 12)
- `grid_h`: Row height units (typically 2 to 6)

## 2. Collision Detection & Auto-Placement

The engine utilizes a deterministic row-packing algorithm:
```python
def place_widget_auto(occupied_slots: Set[Tuple[int, int]], width: int, height: int) -> Tuple[int, int]:
    # Iterates y from 0..N and x from 0..(12 - width)
    # Finds the earliest (x, y) where no slot (x+dx, y+dy) is occupied
```

## 3. Reflow and Compacting

When widgets are removed or resized:
1. Widgets are sorted by `(grid_y, grid_x)`.
2. Each widget is shifted upward to the lowest available `grid_y` that does not cause collisions.
3. Negative coordinates, out-of-bound widths (`width > 12`), and zero heights are rejected with deterministic error codes.

## 4. Responsive Adaptation

On the frontend, the 12-column grid reflows cleanly:
- **Desktop (>= 1024px)**: Full 12-column span (`col-span-12`, `col-span-8`, `col-span-6`, `col-span-4`, `col-span-3`).
- **Tablet (768px - 1023px)**: 2-column or 6-column reduced grid.
- **Mobile (< 768px)**: 1-column vertically stacked cards with touch-friendly controls.
