# Phase 14 — Security & Prompt Injection Defense

## 1. Passive Untrusted Data Policy
- **Documents as Untrusted Data**: All ingested documents, OCR outputs, and user-supplied reference texts are treated strictly as passive factual data.
- **Delimited Context Injection**: Retrieved chunks are passed into the AI orchestrator with strict boundary tags (`<untrusted_business_knowledge> ... </untrusted_business_knowledge>`).
- **Instruction Disregard Enforcement**: The orchestrator instructs the LLM that text inside knowledge boundaries must never be interpreted as commands, instructions, role switches, or system policy overrides.

## 2. Multi-Tenant Authorization & Access Boundaries
- **Ownership Verification**: Every query strictly enforces `KnowledgeDocument.user_id == current_user.id` and workspace tenant boundaries.
- **Cross-Tenant Isolation**: Vector search results and BM25 candidate scoring filter candidate chunks at the database query level before semantic similarity scoring.
- **Path Traversal & Safe Ingestion**: Uploaded files are validated for MIME type, extension allowlist, and sanitized filenames. File data is stored with SHA-256 content addressing.
