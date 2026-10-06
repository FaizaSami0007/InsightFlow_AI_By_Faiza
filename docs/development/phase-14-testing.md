# Phase 14 — Testing & Quality Assurance

## 1. Test Coverage Overview
Phase 14 includes comprehensive unit, integration, security, and benchmark evaluation test suites:
- `apps/api/tests/test_knowledge.py`: Unit and integration tests covering collection creation, multi-format text extraction (PDF, DOCX, TXT, MD, CSV), semantic heading-aware chunking, deterministic vector embeddings, hybrid dense/sparse search, citation formatting, versioning, dataset linking, and multi-tenant security isolation.
- `apps/api/tests/test_phase14_evaluation.py`: 120+ benchmark test cases verifying query intent classification, grounded retrieval, refusal on insufficient evidence, conflicting document handling, versioned/stale citation preservation, prompt injection defense, and cross-tenant access isolation.

## 2. Test Execution
```bash
# Backend pytest suite
cd apps/api
pytest tests/test_knowledge.py tests/test_phase14_evaluation.py -v

# Frontend TypeScript & build validation
cd apps/web
npm run typecheck
npm run lint
npm run build
```
