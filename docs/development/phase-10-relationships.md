# Phase 10: Dataset Relationship Model & Discovery

## Relationship Lifecycle
Dataset relationships follow an explicit state machine:
- `PROPOSED`: Discovered automatically or submitted manually; awaits verification or has unverified referential coverage.
- `VALIDATED`: Verified against physical data in DuckDB; referential coverage > 0%, compatible data types, verified unique keys.
- `DISABLED`: Temporarily deactivated by user; excluded from automatic federated query pathfinding.
- `REJECTED`: Disapproved by user or failed referential compatibility.

## Cardinality Inference Rules
During referential validation against DuckDB:
1. `source_unique_ratio = count(distinct source_key) / count(*)`
2. `target_unique_ratio = count(distinct target_key) / count(*)`
3. **Cardinality Assignment**:
   - `source_unique_ratio >= 0.98` AND `target_unique_ratio >= 0.98` $\rightarrow$ `ONE_TO_ONE`
   - `source_unique_ratio >= 0.98` AND `target_unique_ratio < 0.98` $\rightarrow$ `ONE_TO_MANY`
   - `source_unique_ratio < 0.98` AND `target_unique_ratio >= 0.98` $\rightarrow$ `MANY_TO_ONE`
   - `source_unique_ratio < 0.98` AND `target_unique_ratio < 0.98` $\rightarrow$ `MANY_TO_MANY` (flagged with warnings; requires bridge entity).

## Automated Discovery Signals
The candidate discovery engine computes a deterministic confidence score $[0.0, 1.0]$ based on:
1. **Exact Field Name Match**: `+0.45`
2. **Identifier/ID Naming Pattern**: `+0.25`
3. **Common Suffix Match (e.g. `_id`, `_code`)**: `+0.20`
4. **Semantic Role Match (`IDENTIFIER` role in both profiles)**: `+0.15`
5. **Conceptual Type Compatibility**: Type mismatch incurs severe confidence penalties.
