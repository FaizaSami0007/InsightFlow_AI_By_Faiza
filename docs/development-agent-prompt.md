# Development Agent Operating Prompt

Use this document when delegating implementation to an AI coding agent.

## Mission

Build InsightFlow AI as a reliable, human-centered analytics product. Do not optimize for flashy demos at the expense of correctness.

## Non-negotiable rules

1. Deterministic analytics is the source of numerical truth.
2. Treat all LLM output as untrusted input.
3. Never execute arbitrary model-generated Python.
4. Validate all tool arguments against schemas.
5. Enforce authorization server-side.
6. Preserve dataset version and analysis provenance.
7. Use the HCI checklist before marking a UI feature complete.
8. Every feature needs empty/loading/success/error states.
9. Do not introduce a new dependency without a clear reason.
10. Do not expand scope without updating the roadmap/ADR.
11. Prefer a modular monolith over premature microservices.
12. Do not implement multi-agent orchestration until evaluation proves the need.

## Required workflow for each implementation step

1. Read the relevant specification.
2. Identify dependencies and affected modules.
3. Define acceptance criteria.
4. Implement the smallest complete slice.
5. Add tests.
6. Run lint/type/test checks.
7. Verify accessibility for UI work.
8. Update documentation.
9. Summarize changed files and remaining risks.

## UI rules

Use the InsightFlow palette and soft UI tokens. Prefer calm institutional analytics styling. Never use decorative gradients, glowing AI effects, or low-contrast text merely for aesthetics.

## AI rules

The model may propose an analysis plan but cannot bypass tool policy, authorization, resource budgets, or result validation.

## Completion standard

A feature is not done because the happy path works. It is done when failure, permission, loading, accessibility, observability, and regression behavior are covered.
