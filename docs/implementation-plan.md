# Implementation Plan

## Goal

Convert the documentation into a working vertical slice before expanding the platform.

## Phase 1 — Foundation

- Repository setup
- Environment configuration
- Docker infrastructure
- FastAPI health endpoint
- Next.js shell
- CI quality gates

## Phase 2 — Identity and datasets

- User registration/login
- Session/token management
- Dataset upload
- MIME/extension validation
- File size limits
- Dataset and version records
- Dataset preview

## Phase 3 — Understanding

- Schema inference
- Type normalization
- Profiling
- Missing values
- Duplicate detection
- Outlier detection
- Quality score
- PII detection

## Phase 4 — Deterministic analytics

Implement and test:

- filter
- group-by
- aggregation
- descriptive statistics
- correlation
- distributions
- safe read-only SQL

Every result must carry provenance.

## Phase 5 — AI analyst

1. User question
2. Context builder
3. Intent classification
4. Structured analysis plan
5. Schema validation
6. Tool authorization
7. Tool execution
8. Result validation
9. Grounded response

## Phase 6 — Visualization

Start with KPI, table, bar, line, and scatter. Visualization selection must be driven by data semantics, not arbitrary LLM preference.

## Phase 7 — Dashboard

- Dashboard schema
- Renderer
- Save/load
- Version history
- Filters
- AI modification

## Phase 8 — Hardening

- Security
- Accessibility
- Observability
- AI evaluation
- Cost/latency budgets
- Backup/restore
- Deployment

## Vertical-slice milestone

The first end-to-end success criterion is:

> Upload CSV → ask a question → deterministic calculation → validated result → evidence-backed answer.
