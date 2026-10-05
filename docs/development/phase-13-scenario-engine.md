# Phase 13 — Scenario Engine & Mathematical Formulation

## 1. Engine Responsibilities
`ScenarioEngine` (`apps/api/app/scenarios/engine.py`) is a pure deterministic engine that takes an immutable baseline metric and one or more structured assumptions, applies transformations according to explicit mathematical semantics, and returns a verified `ScenarioResultResponse`.

## 2. Mathematical Transformations
For baseline value $B$ and scenario simulated value $S$:

### A. Direct Percentage Change
$$S = B \times \left(1 + \frac{\Delta\%}{100}\right)$$

### B. Absolute Change
$$S = B + \Delta_{\text{abs}}$$

### C. Direct Set
$$S = V_{\text{target}}$$

### D. Multiplicative Compounding
When multiple direct multiplicative drivers ($D_1, D_2, \dots$) affect an outcome ($Y = D_1 \times D_2$):
$$S = B \times \prod_{i} \left(1 + \frac{\Delta\%_i}{100}\right)$$

### E. Linear Regression Model Scenarios
For a validated regression model $Y = \beta_0 + \sum_j \beta_j X_j$:
$$\Delta Y = \sum_j \beta_j \Delta X_j \implies S = B + \Delta Y$$

## 3. Safe Delta and Impact Calculation
- **Absolute Delta**: $\Delta_{\text{abs}} = S - B$
- **Percentage Change**:
  $$\Delta\% = \begin{cases} \left(\frac{S - B}{B}\right) \times 100 & \text{if } B \neq 0 \\ \text{null} & \text{if } B = 0 \end{cases}$$
- When $B = 0$, the system records `percentage_change = None` and provides an explicit narrative: *"Percentage change unavailable because baseline is zero."*

## 4. Engine Versioning & Reproducibility
Every simulation record stamps `engine_version: "scenario_engine_v1"` alongside the dataset version ID and SHA256 checksum to guarantee 100% mathematical reproducibility.
