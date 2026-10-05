# Phase 11: Predictive Analytics & Forecasting Architecture

## 1. Overview & System Mission
Phase 11 extends InsightFlow AI's analytical capabilities with a deterministic, backtested Time-Series Predictive Intelligence subsystem. Users can forecast business metrics (such as revenue, order volume, server workloads, inventory levels, and demand) with full provenance, statistical diagnostics, and rigorous prediction intervals.

```
USER QUERY: "Forecast monthly revenue for the next 6 months"
                     │
                     ▼
           AI TOOL CALL TRANSLATION
 (Target field, Time field, Horizon, Confidence)
                     │
                     ▼
          REQUEST & DATA VALIDATION
  (Ownership check, IDOR guard, Datatype validation)
                     │
                     ▼
        TIME-SERIES PREPROCESSING
  (Frequency detection, Timeline regularization, Imputation)
                     │
                     ▼
           MODEL REGISTRY POOL
  [Naive, Seasonal Naive, MA, Holt-Winters, ARIMA, SARIMA]
                     │
                     ▼
       CHRONOLOGICAL BACKTESTING
  (Zero Lookahead Leakage, Holdout & Rolling-Origin)
                     │
                     ▼
          OPTIMAL MODEL SELECTION
  (Evaluated vs Naive/Seasonal Baseline on Holdout MAE)
                     │
                     ▼
         PREDICTION INTERVALS (80/90/95%)
                     │
                     ▼
         PERSISTENCE & PROVENANCE
 (ForecastExecution record, version binding, diagnostics)
                     │
                     ▼
       INTERACTIVE FORECAST WORKSPACE & AI
```

## 2. Absolute Anti-Hallucination & Security Rules
1. **No LLM Code Generation or Execution**: The LLM translates user intent into structured forecasting requests (`ForecastRunRequest`). It never writes or runs arbitrary Python scripts, PyTorch/TensorFlow code, or model architectures.
2. **Deterministic ML Engine Execution**: All data filtering, preprocessing, training, backtesting, metric calculation, and interval computation occur in deterministic, isolated Python/C math libraries (`statsmodels`, `scipy`, `numpy`, `pandas`).
3. **No Lookahead Data Leakage**: Future points are strictly withheld during training. Splits are 100% chronological with no random shuffling.
4. **No Fabricated Uncertainty**: Prediction intervals are computed statistically from residual standard error and normal critical values ($z$-scores), rather than arbitrary guesses.

## 3. Database & Persistence Layer
- `ForecastExecution` stores historical runs with:
  - `target_field`, `time_field`, `frequency`, `forecast_horizon`, `confidence_level`
  - `requested_model_type` and `selected_model_name`
  - `metrics` (MAE, RMSE, MAPE, sMAPE, baseline MAE, % improvement)
  - `predictions` (point, lower, upper)
  - `historical_points`
  - `diagnostics` (seasonality period, stationarity ADF results, imputed period counts, outlier counts, hyperparameter summaries)
  - `provenance` (dataset ID, dataset version ID, execution timestamp, user ID).
