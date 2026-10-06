# Phase 17 — Security Architecture: SSRF Defense & SQL Safety

## 1. SSRF Boundary Enforcement (`SSRFGuard`)
Located in `apps/api/app/connectors/security.py`.

InsightFlow AI strictly defends internal network boundaries against Server-Side Request Forgery:
- **Blocked Hostnames:** `localhost`, `127.0.0.1`, `0.0.0.0`, `::1`, `metadata.google.internal`, `instance-data`, `169.254.169.254`, `kubernetes.default`.
- **Blocked Subnets:**
  - `10.0.0.0/8` (Private RFC-1918)
  - `172.16.0.0/12` (Private RFC-1918)
  - `192.168.0.0/16` (Private RFC-1918)
  - `127.0.0.0/8` (Loopback)
  - `169.254.0.0/16` (Link-Local & Cloud Metadata)
  - `224.0.0.0/4` & `240.0.0.0/4` (Multicast & Reserved)
- **Protocol Whitelist:** Only `http` and `https` schemes are permitted. Schemes like `file://`, `ftp://`, `gopher://`, and `dict://` are strictly rejected.

## 2. Read-Only SQL Safety (`SQLSafetyValidator`)
External database connectors operate under strict read-only constraints:
- **Statement Whitelist:** Queries must start with `SELECT`, `WITH`, or `EXPLAIN`.
- **Mutation Blacklist:** Rejects all DDL/DML mutation keywords: `DROP`, `DELETE`, `UPDATE`, `ALTER`, `TRUNCATE`, `INSERT`, `EXEC`, `EXECUTE`, `CREATE`, `GRANT`, `REVOKE`, `ATTACH`, `DETACH`, `COPY`, `INTO OUTFILE`, `LOAD_FILE`, `SHUTDOWN`.
- **Comment Stripping & Semicolon Detection:** Automatically strips comments (`--`, `/* */`) before regex scanning and rejects multi-statement SQL injection attacks.

## 3. Cryptographic Secret Management (`SecretProvider`)
Located in `apps/api/app/connectors/secrets.py`.
- Symmetric field-level encryption using **Fernet** (AES-128 in CBC mode with HMAC-SHA256).
- Keys are derived deterministically from the application master secret.
- **Zero Credential Exposure:** Raw passwords, API keys, and client secrets are never returned in REST responses, UI states, or audit logs. `SecretProvider.mask_credentials()` returns masked values (`********`) for display.
