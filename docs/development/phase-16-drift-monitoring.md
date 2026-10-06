# Phase 16 — Statistical Drift & Multi-Factor Health Monitoring

## 1. Statistical Drift Engines

### A. Population Stability Index (PSI)
Computed with Laplace smoothing across quantile bins:
$$PSI = \sum_{i=1}^{K} (P_i - Q_i) \times \ln\left(\frac{P_i}{Q_i}\right)$$
- **Interpretation**:
  - $PSI < 0.1$: No significant distribution shift (Healthy).
  - $0.1 \le PSI \le 0.2$: Moderate shift (Warning alert triggered).
  - $PSI > 0.2$: Severe distribution shift (Critical alert; Retraining recommended).

### B. Two-Sample Kolmogorov-Smirnov (KS) Test
Non-parametric test for continuous features comparing empirical cumulative distribution functions (ECDF) between training and inference:
- $p\text{-value} < 0.05$ flags statistical divergence.

### C. Total Variation Distance (TVD) for Categorical Features
Measures L1-distance between category probability vectors:
$$TVD(P, Q) = \frac{1}{2} \sum_{c} |P(c) - Q(c)|$$
- Detects novel categories missing from training and shifts exceeding 15%.

---

## 2. 5-Factor Explainable Health Scoring
Rather than an opaque single score, health is decomposed across:
1. **Data Quality**: Missingness %, schema match, null spikes.
2. **Feature Drift**: Max PSI, drifted feature count.
3. **Accuracy / Baseline Superiority**: MAE / F1 improvement % vs naive benchmarks.
4. **Inference Latency**: Execution time vs 250ms SLA boundaries.
5. **Freshness**: Days elapsed since last validation benchmark.
