# Release Notes — InsightFlow AI v1.0.0

**Release Date:** October 6, 2026  
**Build Version:** `20261006.1`  
**Release Gate Status:** `RELEASE READY`  

---

## Welcome to InsightFlow AI v1.0.0
InsightFlow AI is an evidence-driven intelligence platform that transforms connected data and corporate knowledge into grounded analysis, visual insights, predictions, scenarios, and decision support.

---

## Key Features & Highlights

### 1. Grounded Conversational BI & Analytics
- Ask questions in natural language and receive mathematically accurate, deterministic SQL calculations powered by an in-memory DuckDB engine.
- Instant statistical profiling via Polars across tabular columns (nulls, distributions, correlations, entity types).

### 2. Evidence-Driven RAG & Knowledge Fusion
- Ingest enterprise PDFs, markdown guidelines, and Word documents.
- Semantic vector search with token-bounded chunking and mandatory citation tracking.
- Joint evidence fusion: answering questions by reconciling raw tabular numbers against business policy rules.

### 3. Multi-Agent Intelligence Layer
- 9 specialized autonomous agents (Data Analyst, Knowledge Agent, Forecasting Agent, Anomaly Agent, Scenario Agent, Chart Planner, Critic, etc.) coordinated by a DAG Supervisor with strict tool allowlists.

### 4. Forecasting, Anomalies & What-If Simulations
- Time-series predictive modeling (ARIMA, Exponential Smoothing, Moving Average) with backtesting and confidence intervals.
- Statistical anomaly detection with Z-Scores and root-cause explanations.
- What-if decision simulation modeling baseline deltas against strategic modifier assumptions.

### 5. Enterprise Connectors & Security
- Native connectors for PostgreSQL, MySQL, Snowflake, BigQuery, AWS S3, and Salesforce.
- Zero-trust multi-tenancy, PromptGuard adversarial injection defenses, ExportGuard CSV formula escape, RBAC permissions, and Prometheus telemetry.

---

## System Requirements & Deployment
- **Backend:** Python 3.12+, FastAPI, SQLAlchemy 2.0, DuckDB 1.1+
- **Frontend:** Node.js 20+, Next.js 15.5+ (App Router), Turbopack
- **Database:** PostgreSQL 15+ (Production) / SQLite (Local Dev)
- **AI Engine:** Google Gemini API Key (`GEMINI_API_KEY`)
