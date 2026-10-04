# Phase 3 Semantic Layer Specification

## 1. Purpose
The Semantic Layer translates technical tabular columns into analytical business roles (`MEASURE`, `DIMENSION`, `IDENTIFIER`, `DATE`, `DATETIME`, `BOOLEAN`, `TEXT`, `UNKNOWN`).

## 2. Inferred Roles & Heuristics
- **`MEASURE`**: Continuous numeric features, currency keywords (`revenue`, `sales`, `price`, `amount`, `profit`), high cardinality numeric columns.
- **`DIMENSION`**: Categorical features, geographic or organizational attributes (`region`, `country`, `category`, `status`), low-cardinality integers.
- **`IDENTIFIER`**: High-uniqueness columns with key patterns (`id`, `uuid`, `code`, `_id`).
- **`DATE` / `DATETIME`**: Native date/datetime types or temporal name patterns.
- **`BOOLEAN`**: Native booleans or binary categorical patterns (`yes/no`, `true/false`, `0/1`).

## 3. Human Override Foundation
The database model separates `inferred_role` (system inference) from `user_role` (human override). The frontend UI and `PATCH /api/v1/datasets/{id}/versions/{ver}/semantics/{col}` endpoint allow immediate user adjustment.
