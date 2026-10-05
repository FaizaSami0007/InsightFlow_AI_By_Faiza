# Phase 13 — HCI Principles & Soft UI Aesthetics

## 1. Nielsen & Shneiderman Principles
- **Error Prevention (Heuristic 5)**: Interactive sliders and input bounds prevent negative prices, unrealistic conversion rates (>100%), and extreme combinatorial explosions.
- **Visibility of System Status (Heuristic 1)**: Pre-execution preview cards explicitly disclose the baseline, driver modifications, and formula before execution.
- **Clear Separation of Truth vs Simulation**: UI prominently badges `ACTUAL (BASELINE)` with solid slate vs `SIMULATION (SCENARIO)` with blue indicators to prevent cognitive misinterpretation.
- **Recognition Over Recall**: Suggested presets (`Optimistic (+10%)`, `Conservative (-10%)`, `Stress Test (-25%)`) assist rapid strategic exploration.

## 2. Accessible Design
- Full keyboard navigability across sliders and tab switchers.
- WCAG 2.1 AA compliant color contrast ratios on all metric badges and delta values.
- Accessible HTML table view for all sensitivity steps and comparison branches.
