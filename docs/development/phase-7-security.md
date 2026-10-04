# Phase 7 — Visualization Security & Sandboxing

## Security Architecture & Principles

Phase 7 maintains the strict security and authorization boundaries established in Phases 1–6:

1. **Authorization & Tenant Isolation**:
   - Every visualization recommendation and validation request resolves through the authenticated user's `AnalysisJob`.
   - A tenant cannot request, validate, or render charts against analysis jobs or datasets owned by another user (`404 Not Found` returned on cross-tenant access).

2. **Zero Code Execution**:
   - The LLM and recommendation engine never generate JavaScript code, script tags, HTML snippets, or Python execution blocks.
   - All chart specifications are strictly structured JSON adhering to `VisualizationSpec`.

3. **Input Sanitization & XSS Protection**:
   - The `ChartValidator` scans all text fields (`title`, `subtitle`, `explanation`, `format`) for script tags (`<script>`), `javascript:` protocols, event handlers (`onload=`, `onerror=`), and `eval(`.
   - Any malicious string results in immediate validation failure and safe fallback.

4. **Schema & Column Existence Verification**:
   - The validator verifies that every referenced column (`x_axis`, `y_axis`, `series`) exists in the actual output schema of the analytical result.
   - Unreferenced or injected columns cannot be rendered.

5. **Prompt Injection Hardening**:
   - Prompts embedded in dataset values or user inputs cannot alter visualization generation rules or bypass security checks.
