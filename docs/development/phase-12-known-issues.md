# Phase 12: Known Issues & Deferred Capabilities

## 1. Known Limitations & Safe Boundaries

1. **High Cardinality Dimensions**: Root-cause analysis limits group decomposition to top 5 contributors to prevent memory exhaustion and analytical cognitive overload.
2. **Minimum Observations**: Detectors require at least 3 to 4 observations (or 2 full cycles for seasonal detectors); smaller sample sizes return graceful status without fabricating statistical scores.
3. **No Autonomous Alerting Loops**: Background recurring crons and external SMS/email alerts are intentionally omitted in alignment with Phase 12 scope boundaries.
