# Phase 13 — Known Issues & Limitations

## 1. Known Architectural Boundaries
1. **Direct Non-Linear Optimization**: Non-linear mathematical goal seeking (e.g. "Find the optimal price to maximize profit") is deferred to future dedicated optimization phases.
2. **Dynamic Causal Discovery**: Causal relationship graphs are strictly grounded in validated regression models or user-defined explicit assumptions; the system does not infer spontaneous causal graphs without empirical models.
3. **Multi-Variable Sensitivity Limit**: Multi-variable sweeps are currently capped at 2 interacting dimensions with a max step product of 25 scenarios to ensure sub-second response latency.
