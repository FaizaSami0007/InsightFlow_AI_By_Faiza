# Phase 8 — Known Issues & Limitations

## 1. Known Technical Limitations

1. **Analytical Parallelism**: Tool executions during dashboard generation currently run sequentially within an asynchronous loop. For datasets with 10+ complex group-by operations, generation can take 2-4 seconds.
2. **Dynamic Drag-and-Drop on Mobile**: On mobile viewports (< 768px), dragging widgets is disabled in favor of single-column vertical cards and accessible button-driven layout controls.
3. **Complex Multi-Column Composite Filters**: Filter propagation currently supports single-column equality and categorical containment. Compound multi-field cross-filtering expressions will be expanded in future enhancements.

## 2. Deferred Capabilities (Out of Scope for Phase 8)

As specified by the architecture guidelines, the following capabilities are explicitly deferred:
- Autonomous background multi-agent collaboration loops
- Vector database integration / RAG pipeline
- Predictive forecasting / statistical machine learning models
- External database connection brokers
- Arbitrary executable script or dynamic code generation
