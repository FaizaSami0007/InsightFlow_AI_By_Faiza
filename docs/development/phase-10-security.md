# Phase 10: Security Model, IDOR Protection & Tenant Isolation

## Security Hierarchy
```
USER (Authenticated via JWT)
  ↓
DATASET ACCESS (Dataset.owner_id == user.id)
  ↓
COLLECTION ACCESS (DatasetCollection.user_id == user.id)
  ↓
RELATIONSHIP ACCESS (All endpoints enforce source & target ownership)
  ↓
FEDERATED EXECUTION (Verified dataset version ownership)
```

## Security Controls Implemented
1. **IDOR Prevention**:
   - `FederationService.create_collection` ignores or rejects dataset IDs not owned by the requesting user.
   - `FederationService.propose_relationship` verifies both `source_dataset` and `target_dataset` belong to `user.id`.
   - `FederationService.execute_federated_analysis` ensures all `dataset_version_ids` belong to datasets owned by `user.id`.
2. **SQL Injection Protection**:
   - Zero raw user/LLM SQL execution.
   - Strict identifier whitelisting and double-quoting.
   - `DuckDBManager.validate_query_safety` blocks all DDL, DML, file system operations (`COPY`, `ATTACH`, `LOAD`, `INSTALL`, `SYSTEM`), and multi-statement queries.
3. **Prompt Injection Hardening**:
   - Table and column contents are never treated as prompt instructions.
   - Grounded schema adapter only transmits column names, types, and validated relationships to the LLM.
