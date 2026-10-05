# Phase 11: Human-Computer Interaction & Accessibility

## 1. HCI Design Principles
1. **Visibility of System Status**: Real-time progress indicators communicate data preparation, candidate model training, chronological backtesting, and visualization preparation.
2. **Recognition Over Recall**: Automatic target variable and time field detection with clean dropdown selectors.
3. **Error Prevention & Recovery**: Clear validation warnings when temporal series have insufficient rows, ambiguous frequencies, or invalid targets.
4. **Consistency**: Soft dark aesthetic matching the InsightFlow design system with accessible contrast and SVG charts.

## 2. Visual Semantics & Accessibility
- **Historical vs Forecast Distinction**:
  - Historical data: Solid blue curve with point markers.
  - Forecast trajectory: Emerald dashed stroke with highlighted point markers.
  - Prediction interval: Shaded emerald ribbon with translucent boundaries.
- **Table Fallback**: Accessible HTML `<table>` with ARIA labels and keyboard navigability for users relying on screen readers.
