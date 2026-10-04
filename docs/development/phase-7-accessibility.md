# Phase 7 — Visualization Accessibility & HCI Standards

## Accessibility Architecture

InsightFlow AI's visualization system follows WCAG 2.1 AA and HCI best practices:

### Core Principles
1. **Universal Data Table Fallback**:
   - Every visualization component provides an instant toggle to view the data as a paginated, sortable tabular view.
   - Screen readers and assistive devices can navigate data cells directly without relying on graphical SVG interpretations.

2. **Semantic SVG & ARIA**:
   - SVG charts include descriptive `title` and `desc` elements.
   - Interactive elements (bars, points, slices) have keyboard focus outlines and tooltips.

3. **Color & Contrast**:
   - High-contrast institutional color palette adhering to minimum 4.5:1 contrast ratios.
   - Color is never used as the single information carrier; values are labelled with direct text, numbers, and tooltips.

4. **Responsive Layout**:
   - Charts dynamically adapt between mobile (stacked cards, horizontal bars, simplified legends) and desktop layouts.
   - Horizontal scrolling is prevented by automatic label truncation and responsive viewBox scaling.

5. **Export & Portability**:
   - Built-in one-click CSV export and PNG image export for reports and external verification.
