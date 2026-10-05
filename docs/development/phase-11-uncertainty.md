# Phase 11: Prediction Intervals & Uncertainty Quantification

## 1. Principles of Uncertainty Quantification
1. **Never Fabricate Intervals**: Confidence intervals are grounded in model residual standard error $\sigma_{\text{res}}$ and statistical distributions.
2. **Configurable Confidence Levels**:
   - 80% ($z = 1.282$)
   - 90% ($z = 1.645$)
   - 95% ($z = 1.960$, default)
3. **Horizon Expansion**: Prediction interval width widens with step horizon $h$, reflecting escalating uncertainty over long forecast horizons ($\propto \sqrt{h}$).
4. **Physical Bounds**: For non-negative targets (e.g. sales, orders, users), negative bounds are clamped to zero unless `allow_negative=True` is explicitly toggled.

## 2. Statistical Communication
The user interface avoids misleading phrasing like "95% probability of this exact value" and instead displays "95% Prediction Interval: the range in which future observations are expected to fall under identical statistical distributions."
