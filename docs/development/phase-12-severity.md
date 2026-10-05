# Phase 12: Severity & Materiality Scoring Methodology

## 1. Severity Levels

InsightFlow AI assigns explainable severity levels derived from deterministic rules:

| Severity | Criteria |
|---|---|
| **CRITICAL** | Anomaly Score $\ge 4.5$ OR ($|\Delta\%| \ge 50\%$ with $|\Delta| \ge 500.0$) |
| **HIGH** | Anomaly Score $\ge 3.5$ OR ($|\Delta\%| \ge 30\%$ with $|\Delta| \ge 100.0$) |
| **MEDIUM** | Anomaly Score $\ge 2.5$ OR $|\Delta\%| \ge 15\%$ |
| **LOW** | Anomaly Score $\ge 1.5$ OR $|\Delta\%| \ge 5\%$ |
| **INFO** | Statistical score $< 1.5$ (informational tracking) |

## 2. Materiality Priority Score & Anti-Fatigue

To prevent micro-volume noise from dominating alerts (e.g. a $1.00 item jumping 500% to $6.00):
$$\text{Priority Score} = \text{Score} \cdot \log_{10}(\max(10, |\Delta|)) \cdot \left(1 + 0.5 \cdot \frac{\text{recency\_idx}}{\text{total\_points}}\right)$$

This guarantees that a material drop in total revenue ($100,000 drop) correctly outranks high-percentage changes in negligible line items.
