# Phase 16 — Known Issues & Operational Considerations

## 1. Known Considerations
1. **In-Memory Drift Sample Sizes**: For datasets with fewer than 30 observations, continuous KS tests may exhibit reduced statistical power. In such cases, Population Stability Index (PSI) with Laplace smoothing provides more stable drift estimation.
2. **PostgreSQL JSONB Compatibility**: When deployed to PostgreSQL production environments, model metadata, feature schemas, and parameter dictionaries automatically leverage native JSONB indexing.
3. **Rollback Notifications**: When an active production model version is rolled back, a critical `MODEL_ROLLBACK` alert is generated. Ensure monitoring teams acknowledge this alert in the UI after root cause inspection.
