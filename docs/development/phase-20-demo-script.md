# Phase 20: Official Product Demonstration Script (5–10 Minutes)

**Product:** InsightFlow AI  
**Release Version:** `v1.0.0`  
**Audience:** Enterprise Data Leaders, VP of Analytics, Technical Decision Makers  
**Theme:** "From Raw Data and Fragmented Documents to Grounded Autonomous Intelligence"  

---

## Act 1: The Enterprise Reality & Value Proposition (1.5 min)
- **Speaker:** "Modern enterprises struggle with two disconnected worlds: massive structured databases and thousands of unstructured business policy documents. Analysts spend 80% of their time writing boilerplate SQL and reconciling metrics against static PDFs. InsightFlow AI unifies these worlds into an evidence-driven intelligence platform where every insight, chart, forecast, and simulation is mathematically grounded and cryptographically traceable."
- **Action:** Open browser to `http://localhost:3000`. Showcase the sleek, modern dashboard and workspace switcher.

---

## Act 2: Ingestion & Autonomous Semantic Profiling (2 min)
- **Speaker:** "Let's upload our quarterly sales and operations CSV. In seconds, InsightFlow AI's Polars profiling engine detects types, calculates statistics, and classifies entities without moving data to an external black box."
- **Action:**
  1. Click **"Datasets"** → **"Upload CSV"**.
  2. Select `data/demo/sales_marketing_demo.csv`.
  3. Show the instant statistical profile: 30 rows, distributions, null counts, and inferred categorical fields.

---

## Act 3: Conversational BI & Grounded Evidence Fusion (2.5 min)
- **Speaker:** "Now let's ask a complex question that requires both structured calculations and unstructured policy context: *'What is our Enterprise AI Customer Satisfaction score, and does it satisfy our 2026 KPI policy guidelines?'*"
- **Action:**
  1. Upload `data/demo/enterprise_kpi_policy.md` to the **Knowledge Collections**.
  2. In the AI Chat, type the prompt.
  3. Watch the Multi-Agent Orchestrator dispatch tasks:
     - Data Analyst queries DuckDB for average CSAT (`4.80`).
     - Knowledge Agent retrieves Section 2 of the KPI Policy (`Target: 4.75`).
     - Critic Agent validates evidence fusion.
  4. Showcase the generated answer with interactive citation pill and verifiable SQL provenance.

---

## Act 4: Forecasting & What-If Scenario Decision Support (2 min)
- **Speaker:** "InsightFlow AI doesn't just look backward. Let's forecast revenue for the next 7 days and model a strategic scenario."
- **Action:**
  1. Navigate to **"Forecasting"** → Select `sales_amount` with a 7-day horizon. Point out the statistical confidence intervals and backtesting score.
  2. Navigate to **"Scenarios"** → Run a **What-If Simulation**: `+15% Marketing Spend`.
  3. Point out the deterministic delta breakdown ($+512,400 projected revenue increase).

---

## Act 5: Executive Dashboard & Secure Release Wrap-Up (1 min)
- **Speaker:** "With one click, we pin our findings to the Executive Dashboard, generate a sanitized PDF export, and share a secured read-only link with stakeholders. That is InsightFlow AI: deterministic, auditable, autonomous decision intelligence."
- **Action:** Open pinned Executive Dashboard, click **"Export Report"**, conclude demo.
