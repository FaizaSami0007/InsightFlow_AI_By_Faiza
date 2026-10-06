# Phase 18 — Enterprise Threat Model

## 1. Threat Landscape Overview
The InsightFlow AI threat model encompasses 13 distinct attacker profiles, mapping entry points, trust boundaries, deterministic mitigations, and residual risks across the platform.

## 2. Attacker Profiles & Mitigations Matrix
1. **Unauthenticated Attacker:** Entry via public endpoints (`/auth/login`, `/health`). Mitigated by sliding-window rate limiter, Bcrypt, and strict CORS.
2. **Authenticated Normal User:** Attempting horizontal IDOR across datasets. Mitigated by explicit owner/workspace query scoping.
3. **Malicious Workspace Member:** Attempting unauthorized deletions. Mitigated by role-permission matrix and audit logging.
4. **Workspace Administrator:** Attempting cross-tenant access. Mitigated by database-level workspace isolation.
5. **Compromised Account:** Using stolen bearer tokens. Mitigated by short JWT expiry (30m) and JTI tracking.
6. **Malicious Document Author:** Uploading malicious PDFs or zip bombs. Mitigated by FileGuard magic byte checks and decompression bounds.
7. **Malicious Dataset Provider:** Uploading CSVs with formula injection (`=cmd|'/C calc'!A0`). Mitigated by ExportGuard single-quote prepending.
8. **Malicious API Source:** Returning unbounded payloads. Mitigated by JSON schema normalization and preview limits.
9. **Prompt Injection Attacker:** Submitting direct instruction overrides ("ignore previous instructions"). Mitigated by PromptGuard regex/heuristic filters.
10. **Malicious Agent / Tool Interaction:** Sub-agent attempting tool escalation. Mitigated by AIGuard role checks and recursion depth bounding.
11. **External Connector Attacker:** SSRF targeting AWS/GCP metadata (`169.254.169.254`). Mitigated by SSRFGuard IP/DNS validation.
12. **Insider Threat:** Attempting credential inspection. Mitigated by Fernet symmetric encryption and automatic secret masking in logs.
13. **Data Exfiltration Attacker:** Bulk unauthorized export. Mitigated by export role gating and rate limits.
