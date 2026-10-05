# Phase 10: Performance & Resource Limits

## Performance Benchmarks
- **Discovery Engine**: Sub-second candidate generation across pairs of dataset profiles ($< 15\text{ ms}$).
- **Referential Integrity Validation**: Fast single-pass aggregation query in DuckDB calculating cardinality, null rates, and key coverage ($< 45\text{ ms}$).
- **Federated Analytical Queries**:
  - 2 Datasets: $10 - 25\text{ ms}$
  - 3 Datasets (Multi-hop): $20 - 55\text{ ms}$
  - Max Allowed Datasets (5 Datasets): $< 120\text{ ms}$

## Configured Hard Boundaries
- `MAX_DATASETS_PER_ANALYSIS = 5`
- `MAX_JOIN_DEPTH = 3`
- `MAX_RESULT_ROWS = 10000`
- `DEFAULT_TIMEOUT_SECONDS = 30.0`
- `MAX_UPLOAD_SIZE = 50MB`
