# Phase 10: Semantic Federation & Measure/Dimension Ownership

## Semantic Entity Ownership
- **Measures**: Inherently tied to the originating fact table (e.g. `Orders.revenue`, `Shipments.freight_cost`). Measures cannot be arbitrarily synthesized on dimension tables.
- **Dimensions**: Tied to entity tables (e.g. `Customers.segment`, `Products.category`, `Regions.country`).
- **Identifier Keys**: Serve as relational join bridges across datasets.

## Aggregation Correctness & Duplication Prevention
When joining a fact table to a dimension table with cardinality `MANY_TO_ONE` (e.g. `Orders` $\rightarrow$ `Customers`), `SUM(Orders.revenue)` is mathematically invariant because each order links to at most one customer.
When joining across multiple dimensions or one-to-many child entities:
1. `COUNT_DISTINCT` is leveraged for entity counts across join expansions.
2. Safe join tree traversal roots at the primary analytical subject to prevent Cartesian multiplication.
3. Uncontrolled `CROSS JOIN` or cyclic joins are strictly rejected by the planner.
