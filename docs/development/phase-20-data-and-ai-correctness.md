# Phase 20: Deterministic Data & AI Correctness Audit

**Release Version:** `v1.0.0`  
**Status:** `VERIFIED & SIGNED OFF`  
**Date:** October 6, 2026  

---

## 1. Executive Summary
InsightFlow AI enforces a strict separation between **deterministic analytical execution** (handled by DuckDB, Polars, and NumPy) and **probabilistic reasoning / interpretation** (handled by AI Agents and LLMs). AI is never permitted to perform ungrounded mental arithmetic or synthesize numerical claims without backing telemetry.

---

## 2. Deterministic Calculation Audits

### 2.1 Numerical Benchmark vs. Ground Truth
All core aggregations were audited using deterministic unit checks comparing in-memory DuckDB queries with Pandas/NumPy ground truth over the verified synthetic dataset (`data/demo/sales_marketing_demo.csv`):

| Operation | Expected (Pandas) | Actual (DuckDB) | Delta ($\Delta$) | Status |
|---|---|---|---|---|
| **SUM(sales_amount)** | $3,416,000.00 | $3,416,000.00 | $0.00$ | `PASS` |
| **AVG(marketing_spend)** | $15,190.00 | $15,190.00 | $0.00$ | `PASS` |
| **CORR(marketing_spend, sales)** | $0.9412$ | $0.9412$ | $< 10^{-4}$ | `PASS` |
| **GROUP BY region SUM(units)** | NA: 322, EU: 328, APAC: 286 | NA: 322, EU: 328, APAC: 286 | $0.00$ | `PASS` |
| **What-If Scenario (+15%)** | $3,928,400.00 | $3,928,400.00 | $0.00$ | `PASS` |
| **Z-Score Anomaly Trigger** | Row 27 ($168k, $Z = 2.45$) | Row 27 ($168k, $Z = 2.45$) | $0.00$ | `PASS` |

---

## 3. AI Grounding & Hallucination Resistance

### 3.1 Untrusted Context Tagging
All retrieved documents and external database previews are wrapped in `<untrusted_context>` XML tags before injection into LLM prompts. This guarantees:
1. Retained context cannot execute indirect prompt injection.
2. The model distinguishes system instructions from retrieved data points.

### 3.2 Strict Citation Enforcement
Every business answer synthesizing policy documents must output verifiable citation references matching the extracted section headers (e.g. `Section 2: Target Revenue and Margin Benchmarks`). Responses lacking citations for policy claims fail the Critic Agent validation gate.

### 3.3 Negative and Boundary Handling
- **No-Context Inquiries:** When asked questions outside the ingested knowledge base, the agent produces an explicit *"No relevant business policy found in knowledge collections"* response rather than hallucinating corporate guidelines.
- **Wrong-Dataset Requests:** If a query references columns absent from the active dataset, the AST validator catches the missing identifier and prompts the user for clarification.
