# Phase 8 — HCI, Usability & Accessibility

## 1. Design System Alignment

InsightFlow AI Phase 8 follows the curated enterprise palette:
- `#172033` (Ink / Primary Text)
- `#536176` (Slate / Secondary Text)
- `#F7F9FC` (Cloud / Canvas Background)
- `#FFFFFF` (Surface / Card Background)
- `#0F766E` (Teal / Primary Brand Accent)
- `#E6F4F1` (Teal Soft / Subtle Badges)
- `#E3E8EF` (Border Line)

## 2. Nielsen & Shneiderman Principles

1. **Visibility of System Status**: Explicit badges for `GENERATING`, `READY`, `PARTIAL`, `FAILED` with non-blocking feedback.
2. **Recognition over Recall**: Visual plan preview displays chart types and column associations before generation commitment.
3. **User Control and Freedom**: Reversible edits, individual widget removal, atomic chart changes, and manual refresh controls.
4. **Consistency and Standards**: Universal 12-column grid layout across desktop, tablet, and mobile.
5. **Error Recovery**: In case of a single widget computation failure, the remainder of the dashboard renders in `PARTIAL` mode with inline retry prompts rather than crashing the whole view.

## 3. Accessibility (a11y)

- All widgets sorted by `grid_y` then `grid_x` for natural DOM keyboard traversal.
- High contrast text conforming to WCAG 2.1 AA.
- ARIA live regions for toast feedback and generation spinners.
- Screen-reader friendly table fallback and modal dialogues with keyboard escape handling.
