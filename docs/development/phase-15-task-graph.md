# Phase 15: Task Graph Engine & DAG Execution

## 1. Directed Acyclic Graph (DAG) Execution Model
The `TaskGraph` engine manages the stateful execution of complex multi-agent workflows.

## 2. Topological Batching (Kahn's Algorithm)
Tasks are sorted into independent execution batches:
1. **In-degree 0 Nodes**: Tasks with no pending upstream dependencies are grouped into Batch 0 and launched concurrently using `asyncio.gather()`.
2. **Upstream Output Propagation**: When Batch 0 tasks finish, their generated `EvidenceItem` and `ClaimItem` payloads are made available to downstream nodes.
3. **Subsequent Batches**: Nodes whose dependencies are satisfied are dispatched in subsequent batches until the entire DAG completes.

## 3. Resilience & Safety Controls
- **Cycle Detection**: Kahn's algorithm validates that `visited == total_nodes`. Any dependency cycle immediately triggers a `TaskGraphCycleError`.
- **Recursion Limits**: The DAG planner enforces a maximum task depth bound (default: 8) to prevent runaway execution loops.
- **Node-Level Isolation**: If a non-critical analytical task fails (e.g. chart recommendation), the error is isolated, logged as `FAILED`, and the rest of the synthesis continues gracefully.
- **Budget Tracking**: Accumulated token usage and execution duration are audited per node.
