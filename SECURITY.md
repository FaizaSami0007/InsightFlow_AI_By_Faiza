# InsightFlow AI — Security & Compliance Architecture

## Overview
InsightFlow AI employs an enterprise zero-trust security architecture ensuring deterministic policy enforcement independently of AI model reasoning. Security controls are enforced across every trust boundary: API Edge, Authentication, RBAC, Multi-Tenant Isolation, Query AST Parsing, File Inspection, AI Prompt Defense, Tool Policy Boundaries, and Immutable Audit Logging.

---

## 1. Zero-Trust Security Boundaries

```
                 INTERNET / UNTRUSTED CLIENT
                              │
                    SECURITY HEADERS & CSP
                              │
                   SLIDING RATE LIMITER (DDoS)
                              │
                    JWT & BCRYPT IDENTITY
                              │
                    DETERMINISTIC RBAC (5-Tier)
                              │
                    TENANT ISOLATION / IDOR
                              │
     ┌────────────────────────┼────────────────────────┐
     ▼                        ▼                        ▼
DATA ENGINES             AI REASONING             FILE PARSING
DuckDB Parameterized     PromptGuard Defense      Magic Byte Check
SQLSafety AST Parser     Untrusted Delimiters     Zip Bomb Throttling
Read-Only Isolation      AIGuard Tool Boundary    Path Sanitization
     │                        │                        │
     └────────────────────────┼────────────────────────┘
                              ▼
                   IMMUTABLE AUDIT TRAIL
                              ▼
                  SECURITY POSTURE SCORECARD
```

---

## 2. 15-Dimension Technical Scorecard
| Dimension | Status | Enforced Controls |
| :--- | :---: | :--- |
| **Identity & Authentication** | PASS | Bcrypt password hashing, enterprise complexity policy (8-128 chars, mixed case, numbers, special symbols), JWT exp/jti claims. |
| **Authorization & RBAC** | PASS | 5-tier role hierarchy (`OWNER`, `ADMIN`, `ANALYST`, `MEMBER`, `VIEWER`), explicit permission matrix, FastAPI dependency validation. |
| **Multi-Tenant Isolation & IDOR** | PASS | Explicit `workspace_id` and `user_id` query scoping, ownership check on all mutations, 404 on cross-tenant access. |
| **Database Security & Injection** | PASS | SQLAlchemy parameterized queries, `SQLSafetyValidator` AST parser blocking DDL/DML mutations on external databases. |
| **API Security & Rate Limiting** | PASS | Sliding-window in-memory rate limiting, strongly typed Pydantic V2 schemas, `X-Request-ID` correlation tracing. |
| **File Upload & Document Security** | PASS | `FileGuard` magic byte verification, executable binary blocking (`MZ`, `ELF`, `#!`), path traversal sanitization, zip bomb limits. |
| **Enterprise Connectors & SSRF** | PASS | `SSRFGuard` blocking RFC-1918, 127.0.0.0/8, link-local, and cloud metadata (`169.254.169.254`), read-only driver isolation. |
| **AI Prompt Injection Defense** | PASS | `PromptGuard` regex & heuristic filters for direct instruction override, jailbreak markers (`DAN`, developer mode), system probes. |
| **Untrusted Context Encapsulation** | PASS | RAG document chunks, OCR text, and external API responses wrapped in strict `<untrusted_context>` tags with control token escaping. |
| **Tool Policy & Escalation Defense** | PASS | `AIGuard` tool permission mapping; low-privilege roles cannot trigger mutating tools; execution bounds (8 tools/turn, recursion depth 3). |
| **Multi-Agent Orchestration Limits** | PASS | Recursion depth limits, loop detection circuit breakers, immutable actor context propagation. |
| **MLOps & Model Security** | PASS | Version immutability, cryptographic provenance tracking, gated promotion workflows. |
| **Secret Management & Encryption** | PASS | Fernet symmetric credential encryption, automatic credential redaction from logs/APIs, environment variable isolation. |
| **Audit Logging & Immutability** | PASS | Structured `SecurityAuditLog` table capturing actor, action, resource, IP, and status with sensitive key redaction. |
| **Export Security & CSV Injection** | PASS | `ExportGuard` prefix neutralization (`'`, `=`, `+`, `-`, `@`, `\t`, `\r`, `\|`) protecting Excel and spreadsheet users from DDE attacks. |

---

## 3. Vulnerability Reporting & Responsible Disclosure
If you discover a potential security vulnerability in InsightFlow AI, please report it privately:
- **Email:** `security@insightflow.ai`
- **Response SLA:** Initial acknowledgment within 24 hours; triage within 48 hours.
- Please do NOT disclose security vulnerabilities publicly until a patch is released.
