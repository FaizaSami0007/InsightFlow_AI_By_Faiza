# Phase 12: Anomaly Detection Methodologies & Estimator Registry

InsightFlow AI implements an extensible registry of deterministic statistical detectors:

## 1. Supported Detectors

### 1. Robust Z-Score (`ROBUST_Z_SCORE`) - Recommended
- **Formula**: $M_i = \frac{0.6745 \cdot |x_i - \tilde{x}|}{\text{MAD}}$
- **Zero MAD Fallback**: Mean Absolute Deviation scaling $M_i = \frac{|x_i - \tilde{x}|}{1.2533 \cdot \text{mean\_ad}}$
- **Best For**: Data with heavy tails, extreme outliers, or skewed financial distributions.

### 2. Standard Z-Score (`Z_SCORE`)
- **Formula**: $Z_i = \frac{|x_i - \bar{x}|}{s}$
- **Best For**: Normally distributed, stable operational telemetry metrics.

### 3. Interquartile Range (`IQR`)
- **Formula**: $[Q_1 - k \cdot \text{IQR}, Q_3 + k \cdot \text{IQR}]$ with standard $k=1.5$ or $k=3.0$.
- **Best For**: Non-parametric distributions without distributional assumptions.

### 4. Rolling Dynamic Baseline (`ROLLING_BASELINE`)
- **Formula**: Local sliding window median $\tilde{x}_{t-w:t}$ and rolling dispersion $\sigma_{\text{roll}}$.
- **Best For**: Evolving time-series with non-stationary drift and trend shifts.

### 5. Seasonal Cycle Baseline (`SEASONAL_BASELINE`)
- **Formula**: Compares slot $i \pmod s$ against historical median and MAD for that specific seasonal period.
- **Best For**: Weekly or monthly seasonal patterns (e.g. Q4 holiday spikes are recognized as normal).

### 6. Forecast Interval Deviation (`FORECAST_DEVIATION`)
- **Formula**: Flags actual observations that violate Phase 11 backtested prediction intervals $[L_t, U_t]$.
- **Best For**: Forward-looking anomaly detection against validated forecasting models.
