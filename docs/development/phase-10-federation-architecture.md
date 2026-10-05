# Phase 10: Dataset Federation Architecture

## Overview
InsightFlow AI Phase 10 enables multi-dataset intelligence and controlled federated analytics across multiple related tabular datasets without physically merging or duplicating underlying data files.

## Core Principles
1. **Zero Physical Merges**: Source datasets (CSV, Parquet) remain independent and immutable.
2. **Deterministic Virtual Views**: Virtual relations are dynamically registered into an in-process DuckDB analytical session using streaming readers (`read_csv_auto`, `read_parquet`).
3. **No Arbitrary SQL Generation**: The LLM proposes structured dataset selection, join intents, dimensions, and measures. The deterministic backend validates authorization, relationships, and types before generating safe parameterized SQL.
4. **Graph-Based Join Pathfinding**: Relationship topologies are evaluated as an undirected/directed graph with BFS shortest-path tree resolution, cycle prevention, and depth bounding (`MAX_JOIN_DEPTH = 3`).

```
                    USER
                     │
                     ▼
              NATURAL LANGUAGE
                     │
                     ▼
              AI ORCHESTRATOR
                     │
                     ▼
          MULTI-DATASET PLAN
                     │
                     ▼
         AUTHORIZATION CHECK
                     │
                     ▼
       RELATIONSHIP VALIDATION
                     │
                     ▼
          SEMANTIC VALIDATION
                     │
                     ▼
         SAFE QUERY BUILDER
                     │
                     ▼
                  DUCKDB
                     │
                     ▼
          VALIDATED ANALYTICAL
                 RESULT
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
   VISUALIZATION             TABLE
          │                     │
          └──────────┬──────────┘
                     ▼
              DASHBOARD /
              CONVERSATION
                     │
                     ▼
                PROVENANCE
```

## Component Breakdown
- `DatasetCollection`: Logical grouping of datasets belonging to a user workspace.
- `DatasetRelationship`: First-class relational edge linking `(source_dataset, source_field)` to `(target_dataset, target_field)` with explicit cardinality (`ONE_TO_ONE`, `ONE_TO_MANY`, `MANY_TO_ONE`), coverage ratio, and validation status (`PROPOSED`, `VALIDATED`, `REJECTED`, `DISABLED`).
- `FederationGraph`: Network graph structure providing shortest join-path determination, spanning-tree generation, and ambiguity resolution.
- `RelationshipEngine`: Statistical profile inspection (exact name matches, substring matches, semantic entity roles, type compatibility) and DuckDB referential integrity validation.
- `FederatedQueryPlanner`: Sanitized SQL generation, aggregation correctness enforcement, duplication prevention, bounded LIMIT application, and execution provenance assembly.
