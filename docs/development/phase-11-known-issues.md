# Phase 11: Known Issues & Deferred Scope

## 1. Known Issues & Limitations
1. **Short Time-Series Fitting**: Series with fewer than 6 observations cannot be modeled reliably and are rejected with a data sufficiency warning.
2. **High Autoregressive Order Optimization**: For small sample sizes ($N < 15$), SARIMA models with high seasonal order may trigger singular design matrix warnings from numerical optimization. In these instances, fallback models (Holt-Winters or Naive) are automatically selected based on backtesting.
3. **External Exogenous Variables**: Future exogenous features (e.g. planned marketing budget) require future values to be provided by the user.

## 2. Deferred Capabilities (Out of Scope for Phase 11)
- Deep Learning architectures (LSTM, GRU, Temporal Fusion Transformers).
- Autonomous retraining daemon loops.
- Full MLOps lifecycle model registry with external production artifact storage.
- Vector database / RAG integrations.
- Causal inference / counterfactual simulations.
