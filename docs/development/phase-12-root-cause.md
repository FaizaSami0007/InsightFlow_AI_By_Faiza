# Phase 12: Dimensional Root-Cause & Contribution Analysis

## 1. Dimensional Decomposition

When an anomaly is detected on a primary metric in period $T$, the root-cause analyzer deterministically breaks down the metric across candidate semantic dimensions (e.g. `region`, `product_category`, `channel`).

$$\text{Contribution } \% = \frac{|\Delta_k|}{\sum_j |\Delta_j|} \times 100\%$$
Where:
- $\Delta_k = \text{Observed}_{k, T} - \text{Baseline}_{k}$
- $k$ represents each categorical subgroup.

## 2. Anti-Causality & Non-Causal Explanation Guidelines

InsightFlow AI strictly forbids unsupported causal claims without formal randomized control or econometric causal inference:
- **Disallowed**: `"Electronics caused the revenue drop."`
- **Mandated**: `"Category 'Electronics' accounted for 71.4% of the variation (decline of $50,000 relative to baseline $60,000)."`
