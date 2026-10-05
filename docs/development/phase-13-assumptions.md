# Phase 13 — Assumption Model & Domain Validation

## 1. Structured Assumption Schema
Assumptions in InsightFlow AI are strictly structured Pydantic models:
```json
{
  "variable": "price",
  "operation": "PERCENTAGE_CHANGE",
  "value": 5.0,
  "unit": "%",
  "min_bound": 0.0,
  "max_bound": 500.0,
  "is_non_negative": true
}
```

## 2. Validation & Boundary Enforcement
1. **Physical Non-Negativity**: Variables representing physical or monetary values (e.g. `price`, `revenue`, `quantity`, `orders`, `cost`) cannot become negative unless `allow_negative=True` is explicitly authorized.
2. **Domain Rate Bounds**: Variables indicating percentages or bounded ratios (e.g. `discount`, `tax_rate`, `churn_rate`, `conversion_rate`) are strictly bounded to $[0\%, 100\%]$.
3. **Existence & Modifiability**: Assumptions targeting non-numeric or non-existent columns are rejected prior to execution.
4. **Safety Limits**: Percentage modifiers exceeding sanity limits (e.g. $\pm 500\%$) trigger explicit validation errors rather than silently running absurd simulations.
