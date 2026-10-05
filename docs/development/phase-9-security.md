# Phase 9: Security, Multi-Tenancy & Threat Mitigation

## 1. Threat Modeling & Safeguards

| Threat Vector | Mitigation Strategy | Verification Mechanism |
| :--- | :--- | :--- |
| **Insecure Direct Object Reference (IDOR)** | Ownership verification on dashboard, export, and share CRUD operations | Integration test suite (`test_exports.py`, `test_sharing.py`) |
| **Path Traversal / Arbitrary File Generation** | Strict filename regex sanitization (`[a-zA-Z0-9_\-]+`) | Unit test `test_filename_sanitization` |
| **Denial of Service (DoS) via Huge Exports** | `MAX_EXPORT_ROWS`, `MAX_EXPORT_FILE_SIZE`, `MAX_EXPORT_EXECUTION_TIME` | Engine limit checks |
| **Token Guessing / Enumeration** | 256-bit URL-safe cryptographic randomness | Secrets engine |
| **Data Leakage in Shared Links** | View-only tokenized routes expose only widget result projections, not raw database tables | Live share API tests |
| **Viewer Session Mutation** | Viewer filter state is transient in memory or cached by session | Session isolation tests |

---

## 2. Authorization Rules

1. **Dashboard Exports (`/dashboards/{id}/exports`):**
   - Requester must be authenticated (`JWT Bearer`).
   - Requester must own the target dashboard (`dashboard.user_id == current_user.id`).
2. **Export Downloads (`/exports/{id}/download`):**
   - Requester must be the owner of the export record (`export.user_id == current_user.id`).
3. **Dashboard Shares (`/dashboards/{id}/shares`):**
   - Requester must own the target dashboard.
4. **Public Shared View (`/shared/dashboards/{token}`):**
   - Opaque token verification.
   - Token must be active (`is_active = True`) and not expired (`expires_at > now`).
