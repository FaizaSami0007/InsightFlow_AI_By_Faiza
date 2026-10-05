# Phase 10: Federated Query Planning & Execution

## Join Path Resolution (BFS Spanning Tree)
1. **Input**: Requested dataset version IDs, validated relationship graph.
2. **Root Selection**: The dataset containing the primary measure or first dimension is selected as the query root.
3. **Graph Traversal**: A Breadth-First Search (BFS) explores active, validated relational edges.
4. **Depth Bounding**: Join depth cannot exceed `MAX_JOIN_DEPTH = 3`. Requests requiring $>3$ hops are rejected with an actionable error.
5. **Ambiguity Resolution**: If multiple distinct shortest paths connect two datasets (e.g. `Orders.customer_id` vs `Orders.billing_customer_id`), the engine raises an ambiguity warning/clarification request rather than making a non-deterministic choice.

## Safe SQL Construction
1. Identifiers are double-quoted and sanitized with regex `[^a-zA-Z0-9_"]` stripping.
2. Filter values are strictly parameterized or escaped.
3. Bounded limits (`LIMIT min(requested, 10000)`) are systematically injected.
4. Output rows are structured as strongly-typed column-keyed dictionaries with complete execution metadata.
