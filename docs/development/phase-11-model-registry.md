# Phase 11: Forecasting Model Registry & Estimators

## 1. Estimator Contract (`BaseForecastModel`)
Every algorithm in InsightFlow AI implements the deterministic `BaseForecastModel` interface:
- `fit(y: Any, dates: Optional[List[pd.Timestamp]] = None, **kwargs)`
- `predict(horizon: int, confidence_level: float = 0.95, allow_negative: bool = False) -> Tuple[np.ndarray, np.ndarray, np.ndarray]`
- `get_parameters() -> Dict[str, Any]`

## 2. Supported Algorithms

### 1. Naive Baseline (`NAIVE`)
- **Mechanism**: Points to the most recent historical observation ($y_t = y_{T}$).
- **Interval**: $\pm z \cdot \sigma_{\text{res}} \cdot \sqrt{h}$.
- **Role**: Mandatory lower-bound performance baseline.

### 2. Seasonal Naive (`SEASONAL_NAIVE`)
- **Mechanism**: Repeats observations from the previous full seasonal cycle ($y_{T+h} = y_{T+h-s \cdot k}$).
- **Interval**: $\pm z \cdot \sigma_{\text{res}} \cdot \sqrt{\lfloor h/s \rfloor + 1}$.
- **Role**: Seasonal baseline when periodic patterns (e.g. 12 months, 7 days) are detected.

### 3. Moving Average (`MOVING_AVERAGE`)
- **Mechanism**: Rolling window mean projection ($\bar{y}_w$).
- **Interval**: $\pm z \cdot \sigma_{\text{res}} \cdot \sqrt{1 + h/w}$.

### 4. Exponential Smoothing / Holt-Winters (`EXPONENTIAL_SMOOTHING`)
- **Mechanism**: Exponentially weighted level, additive/multiplicative trend, and additive seasonal components.
- **Optimization**: Automated parameter estimation ($\alpha, \beta, \gamma$) via `statsmodels.tsa.holtwinters`.

### 5. ARIMA (`ARIMA`)
- **Mechanism**: Autoregressive Integrated Moving Average $(p, d, q)$ with bounded order grid search optimizing Akaike Information Criterion (AIC).

### 6. SARIMA (`SARIMA`)
- **Mechanism**: Seasonal ARIMA $(p, d, q) \times (P, D, Q)_s$ modeling both seasonal and non-seasonal autoregressive lag structures.

## 3. Auto Model Selection Factory
When `model_type="AUTO"` is requested:
1. Candidate models are generated based on series length and seasonality diagnostics.
2. Models are trained on historical holdout partitions.
3. Out-of-sample predictions are backtested against actuals.
4. The model achieving the lowest Holdout MAE is selected (with a 2% complexity penalty preference for simpler baselines if scores tie).
