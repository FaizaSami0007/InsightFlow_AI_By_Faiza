# Phase 17 — Schema Discovery & Resource Introspection

## Overview
Schema discovery allows InsightFlow AI users to explore remote database tables, API collections, and object storage files without executing expensive data transfers.

## Discovery Workflow
1. **Handshake Test:** `POST /api/v1/connectors/connections/{id}/test` validates connectivity, measures latency, and returns resource counts.
2. **Live Introspection:** `GET /api/v1/connectors/connections/{id}/discover` extracts:
   - Resource name and type (`TABLE`, `VIEW`, `ENDPOINT`, `FILE`, `SHEET`).
   - Column names, data types, nullability, and primary key constraints.
   - Estimated row count for workload planning.
3. **Interactive Preview:** `POST /api/v1/connectors/connections/{id}/preview` samples between 1 and 500 records with type inference.
4. **Historical Snapshotting:** Each discovery run is stored in `data_connection_schema_snapshots` to power automatic schema drift detection.
