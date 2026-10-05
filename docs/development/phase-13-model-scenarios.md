# Phase 13 — Model-Based Scenarios & Boundary Rules

## 1. Grounded Model Integration
When predictive models (Phase 11) or regression relationships exist:
1. Scenario assumptions may only modify features that exist in the trained model schema.
2. The AI must never invent elasticity parameters or causal coefficients without an underlying trained model or explicit user assertion.
3. If no relationship exists between a requested driver and outcome, the system states: *"InsightFlow cannot estimate this impact from the available data/model."*

## 2. Distinction from Predictive Forecasting
- **Forecasting (Phase 11)**: Extrapolates temporal historical trends under uncertainty.
- **Scenario Simulation (Phase 13)**: Evaluates user-specified assumptions on top of baseline metrics.
- Forecast uncertainty intervals (e.g. 95% CI) are preserved when scenarios are simulated against predictive models.
