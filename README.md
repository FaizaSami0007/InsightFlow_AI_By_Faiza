# InsightFlow AI

**AI-Driven Automated Data Analysis & Context-Aware Dashboard Generation**

[![Release Version](https://img.shields.io/badge/Release-v1.0.0-00E599.svg)](./RELEASE_NOTES.md)
[![Build Status](https://img.shields.io/badge/Build-Passing-brightgreen.svg)](./CHANGELOG.md)
[![Tests](https://img.shields.io/badge/Tests-1272%2F1272%20Passing-brightgreen.svg)](./docs/development/phase-20-completion-report.md)
[![Security Score](https://img.shields.io/badge/Security-92%2F100%20(A%2B)-blue.svg)](./docs/development/phase-20-security-and-isolation.md)
[![License](https://img.shields.io/badge/License-Enterprise-blueviolet.svg)](./LICENSE)

---

## 1. What is InsightFlow AI?

**InsightFlow AI** is an enterprise-grade, evidence-driven autonomous intelligence platform. It bridges raw tabular datasets and unstructured corporate knowledge documents into mathematically grounded analytics, automated visualizations, time-series predictions, anomaly detections, and what-if strategic simulations.

### The InsightFlow AI Product Principle:
> *"InsightFlow AI transforms connected data and business knowledge into grounded analysis, visual insights, predictions, scenarios, and decision support."*

```
DATA ────────────► provides deterministic evidence
ANALYTICS ───────► calculates without guessing (DuckDB + Polars)
RAG ─────────────► provides verified corporate policies & context
AI AGENTS ───────► coordinate & interpret specialized tasks
ML ──────────────► predicts time-series & flags statistical outliers
SCENARIOS ───────► simulate assumption deltas
PROVENANCE ──────► audits exact sources, models, and timestamps
SECURITY ────────► enforces zero-trust tenant boundaries
USER ────────────► makes the final informed business decision
```

---

## 2. Core Capabilities

- **Deterministic High-Performance Analytics:** Sub-millisecond aggregations, correlations, and cross-dataset federation powered by in-memory DuckDB and Polars.
- **Evidence-Driven RAG & Knowledge Fusion:** Joint synthesis answering questions by reconciling raw tabular data against corporate policy documents with verifiable citations.
- **Autonomous Multi-Agent Intelligence:** 9 specialized agents coordinated by a DAG Supervisor with tool allowlists and Critic Agent validation.
- **Predictive Analytics & Forecasting:** Statistical time-series estimators (ARIMA, Exponential Smoothing, Moving Average) with backtesting and confidence intervals.
- **Proactive Anomaly Detection:** Multi-method outlier detection (Z-Score, IQR, Rolling Baselines) with automated root-cause attribution.
- **Decision Intelligence & What-If Simulations:** Strategic baseline modeling with dynamic assumption parameters and exact numerical deltas.
- **Enterprise Connectors:** Native support for PostgreSQL, MySQL, Snowflake, BigQuery, AWS S3, and Salesforce with incremental synchronization.
- **Zero-Trust Enterprise Security:** PromptGuard prompt injection defenses, ExportGuard CSV formula escape, RBAC permissions, and Prometheus telemetry.

---

## 3. Technology Stack

### Backend
- **Framework:** FastAPI `0.115.6` with Asyncio ASGI pipeline
- **Runtime:** Python `3.12.10`
- **Database ORM:** SQLAlchemy `2.0.36` (Async PostgreSQL / SQLite engine)
- **High-Performance Engines:** DuckDB `1.1.3` + Polars `1.18.0` + Pandas `2.2.3`
- **ML & Forecasting:** Statsmodels `0.14.4` + Scikit-Learn `1.6.0` + NumPy `2.2.0`
- **AI Integration:** Google GenAI SDK (Gemini 2.0 Flash / Pro)

### Frontend
- **Framework:** Next.js `15.5.27` (App Router, React 19) + Turbopack
- **Styling:** Custom Glassmorphism UI tokens & Vanilla CSS system
- **State Management:** Zustand + React Query (TanStack Query v5)
- **Visualizations:** Apache ECharts + Chart.js + Accessible SVG Canvas

---

## 4. Quickstart & Local Setup

### Prerequisites
- Python `3.12+`
- Node.js `20+` & `npm`
- Google Gemini API Key

### Backend Setup
```bash
# Navigate to API root
cd apps/api

# Create virtual environment and install dependencies
python -m venv .venv
.\.venv\Scripts\activate  # Windows (or source .venv/bin/activate on Unix)
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start FastAPI backend server
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Frontend Setup
```bash
# Navigate to web root
cd apps/web

# Install npm dependencies
npm install

# Start Next.js development server
npm run dev
```

Open your browser to [http://localhost:3000](http://localhost:3000) to access the application.

---

## 5. Running the Complete Verification Test Suite

```bash
# Run the 1,270+ test suite
cd apps/api
.\.venv\Scripts\pytest.exe -q
```

---

## 6. Project Documentation Index

- **System Inventory:** [docs/development/phase-20-system-inventory.md](./docs/development/phase-20-system-inventory.md)
- **Critical User Journeys (A–J):** [docs/development/phase-20-user-journeys.md](./docs/development/phase-20-user-journeys.md)
- **End-to-End Test Matrix:** [docs/development/phase-20-e2e-matrix.md](./docs/development/phase-20-e2e-matrix.md)
- **Data & AI Correctness Audit:** [docs/development/phase-20-data-and-ai-correctness.md](./docs/development/phase-20-data-and-ai-correctness.md)
- **Security & Multi-Tenant Isolation:** [docs/development/phase-20-security-and-isolation.md](./docs/development/phase-20-security-and-isolation.md)
- **Failure Recovery & Degradation:** [docs/development/phase-20-failure-recovery.md](./docs/development/phase-20-failure-recovery.md)
- **Frontend & HCI QA:** [docs/development/phase-20-frontend-hci-qa.md](./docs/development/phase-20-frontend-hci-qa.md)
- **Demo Script (5–10 Min):** [docs/development/phase-20-demo-script.md](./docs/development/phase-20-demo-script.md)
- **Completion & Release Sign-Off Report:** [docs/development/phase-20-completion-report.md](./docs/development/phase-20-completion-report.md)

---

## 7. License & Release Status

InsightFlow AI is released under the Enterprise Commercial License.  
**Current Release Decision:** `RELEASE READY (v1.0.0)`
