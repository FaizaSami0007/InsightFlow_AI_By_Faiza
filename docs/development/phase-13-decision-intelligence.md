# Phase 13 — Decision Intelligence Architecture

## 1. Overview & Core Objective
Phase 13 establishes the Decision Intelligence, What-If Analysis, and Scenario Simulation layer for InsightFlow AI. It empowers analysts, business leaders, and data scientists to evaluate parameter changes, perform sensitivity sweeps, and compare strategic scenario branches deterministically.

## 2. Fundamental Architectural Principle
**A simulation is NOT historical truth and is NOT a guaranteed forecast.**
Every analytical output in InsightFlow AI rigorously enforces distinct analytical contexts:
- `ACTUAL`: Measured, immutable historical facts directly stored in datasets.
- `FORECAST`: Statistical projections generated with explicit prediction intervals (Phase 11).
- `ASSUMPTION`: Explicit user-defined or policy-driven hypothesis modifying specific drivers.
- `SIMULATION`: Deterministic evaluation of output metrics given assumptions.
- `SCENARIO`: Named branches (e.g., Optimistic, Conservative, Custom) binding assumptions to simulated outcomes.

## 3. End-to-End Simulation Pipeline
```
USER (Natural Language / Interactive Workspace UI)
  │
  ▼
AI Interpretation & Schema Extraction (Structured Tool Calling)
  │
  ▼
Request & Assumption Validation (Bound Checking & Security Guards)
  │
  ▼
Immutable Baseline Analysis (DuckDB Read-Only Snapshot)
  │
  ▼
Deterministic Scenario Engine (Mathematical Transformations & Compounding)
  │
  ▼
Impact & Delta Calculation (Absolute + Percentage Change with Zero-Baseline Guard)
  │
  ▼
Grounded Result Presentation (Workspace Cards, Sensitivity Curves, Side-by-Side Tables)
  │
  ▼
Export & Dashboard Integration (PDF/CSV/PNG with Full Provenance)
```

## 4. Key Capabilities Supported
1. **Single-Variable What-If**: Modify direct target metrics or underlying drivers (e.g. `Price +5%`).
2. **Multi-Variable What-If**: Simultaneous compound changes with driver relationship modeling (e.g. `Price +5%` and `Volume -10%`).
3. **Sensitivity Analysis Sweeps**: Automated incremental parameter variation (e.g. `-20%` to `+20%` at `5%` steps) with safety caps (`MAX_SCENARIOS_PER_RUN = 25`).
4. **Scenario Comparisons**: Side-by-side branch evaluations (`Optimistic`, `Conservative`, `Custom`).
5. **Regression & Model-Based Scenarios**: Simulation across features in validated regression models without parameter fabrication.
