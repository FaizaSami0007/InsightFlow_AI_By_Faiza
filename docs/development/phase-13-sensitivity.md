# Phase 13 — Parameter Sensitivity Sweeps

## 1. Sensitivity Sweep Pipeline
Sensitivity analysis evaluates how an outcome metric responds across a systematic spectrum of driver variations.
- **Parameters**: `variable`, `min_pct` (e.g. -20%), `max_pct` (e.g. +20%), and `step_pct` (e.g. 5%).
- **Execution**: Computes deterministic increments producing a structured `List[SensitivityStep]`.

## 2. Resource & Combinatorial Controls
1. **Safety Cap (`MAX_SCENARIOS_PER_RUN = 25`)**: Prevents unbounded step loops or excessive computation.
2. **Combinatorial Sweep Control**: For multi-variable sensitivity, parameter combinations are validated before execution to prevent combinatorial explosion.
3. **Reproducibility**: Identical sweep ranges on the same dataset version yield identical response curves.
