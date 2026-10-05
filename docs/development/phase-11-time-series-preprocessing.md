# Phase 11: Time-Series Preprocessing & Diagnostics

## 1. Timeline Regularization Pipeline
Time series require a regular frequency grid. InsightFlow AI uses `TimeSeriesPreprocessor`:
1. **Query & Type Casting**: DuckDB executes sanitization, `TRY_CAST(time_col AS TIMESTAMP)` and `TRY_CAST(target_col AS DOUBLE)`.
2. **Frequency Detection**: Analyzes the median step delta across timestamps:
   - $\le 1.5$ days $\rightarrow$ Daily (`D`)
   - $\le 10$ days $\rightarrow$ Weekly (`W-MON`)
   - $\le 45$ days $\rightarrow$ Monthly (`MS`)
   - $\le 120$ days $\rightarrow$ Quarterly (`QS`)
   - $> 120$ days $\rightarrow$ Yearly (`YS`)
3. **Resampling & Deduplication**: Aggregates same-period entries via `sum()` (or specified agg).
4. **Missing Period Imputation**: Missing dates in the sequence are identified as `NaN` and interpolated linearly with boundary backfill/forward-fill. The count of imputed points is recorded in diagnostics.

## 2. Statistical Diagnostics
- **Seasonality Detection**: Computes sample autocorrelation at candidate seasonal lags ($s \in \{12, 6, 4, 7, 52\}$). If autocorrelation $> 0.25$ with at least 2 cycles, seasonality is flagged with its detected period.
- **Stationarity Testing**: Evaluates Augmented Dickey-Fuller (ADF) test statistics. If $p < 0.05$, series is stationary; otherwise differencing is applied in ARIMA models.
- **Outlier Detection**: Measures counts of observations exceeding $1.5 \times \text{IQR}$ beyond Q1/Q3 boundaries. Outliers are flagged in metadata rather than silently erased.
- **Sufficiency Guard**: Enforces `MIN_OBSERVATIONS = 6`. Series shorter than the threshold are safely rejected with explainable error diagnostics.
