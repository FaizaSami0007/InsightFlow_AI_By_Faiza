# Phase 16 — MLOps Security, Governance & Isolation

## 1. Multi-Tenant Isolation
- All model registrations, versions, experiments, evaluations, deployments, and alerts are isolated by `user_id` and optional `workspace_id`.
- IDOR protections ensure users cannot read, promote, or rollback models belonging to other tenants.

## 2. Artifact Integrity Verification
- Model weights are hashed with SHA-256 upon creation.
- Checksums are verified prior to loading artifacts into memory to defend against tampering and injection.

## 3. Human-in-the-Loop Governance
- Autonomous production promotions and autonomous retraining deployments are strictly disallowed.
- State transitions require authenticated user session and explicit audit reasons.
