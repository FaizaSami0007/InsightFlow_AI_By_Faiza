# Phase 17 — Ingestion & Synchronization Engine

## Synchronization Architecture (`SyncEngine`)
Located in `apps/api/app/connectors/sync_engine.py`.

The `SyncEngine` bridges external data connections with InsightFlow AI's core analytical storage:
1. **Extraction:** Chunks records from the remote source according to the selected mode (`FULL_SYNC` or `INCREMENTAL_SYNC`).
2. **Buffer Materialization:** Converts records into optimized Parquet/CSV file buffers in temporary storage.
3. **Dataset Versioning:** Calls `create_dataset_with_file` or `create_dataset_version` to create an immutable `DatasetVersion` linked to the user account.
4. **DuckDB Profiling:** Automatically triggers `ProfilingService.profile_version()` to compute statistical summaries, missingness metrics, column correlations, and semantic concepts.
5. **Audit Logging:** Emits structured records into `data_connection_audit_logs` tracking bytes transferred, elapsed time, and row counts.

```mermaid
sequenceDiagram
    participant User as Analyst / Client
    participant Router as /connectors/sync
    participant Sync as SyncEngine
    participant Conn as DataConnector
    participant Storage as Dataset Storage
    participant Profile as DuckDB Profiler

    User->>Router: Trigger Sync (resource="sales")
    Router->>Sync: execute_sync_job()
    Sync->>Conn: extract_records()
    Conn-->>Sync: Return Ingested Rows
    Sync->>Storage: Materialize Parquet Buffer & Create DatasetVersion
    Storage-->>Sync: DatasetVersion ID
    Sync->>Profile: Profile Dataset Version
    Sync-->>User: SyncJob Completed
```
