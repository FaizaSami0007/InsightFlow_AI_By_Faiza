# InsightFlow AI

## AI-Driven Automated Data Analysis & Context-Aware Dashboard Generation

**Version:** 1.0.0 implementation baseline  
**Status:** Implementation-ready scaffold  
**Architecture:** Modular monolith  
**Frontend:** Next.js + TypeScript  
**Backend:** FastAPI + Python  
**Analytics:** DuckDB + Polars  
**Application DB:** PostgreSQL  
**UI:** Tailwind CSS + shadcn/ui patterns  

---

## 1. What InsightFlow AI is

InsightFlow AI is an AI-assisted analytics workspace that turns structured data into validated analysis, grounded explanations, visualizations, and context-aware dashboards.

The core rule is:

> **The model reasons; deterministic tools calculate.**

The LLM never becomes the source of truth for numerical results. It produces a structured analysis plan, selects allowlisted analytical tools, and explains validated results returned by the analytical engine.

### Core flow

```text
Upload data
  ↓
Validate + version
  ↓
Profile + quality analysis
  ↓
Build dataset context
  ↓
Natural-language question
  ↓
Intent + analysis plan
  ↓
Tool validation
  ↓
DuckDB / Polars execution
  ↓
Result validation + provenance
  ↓
Grounded explanation
  ↓
Visualization recommendation
  ↓
Dashboard generation
  ↓
Natural-language dashboard editing
```

---

## 2. What was added beyond the original documentation

This package preserves the original 16 specifications under `docs/original-specifications/` and adds the missing implementation-level capabilities identified during review:

- Product discovery, personas, jobs-to-be-done, and non-goals
- Explicit MVP / V1 / V2 boundaries and feature gates
- Architecture Decision Records (ADRs)
- Semantic metric/dimension layer
- Dataset lineage and analytical provenance
- Data governance, retention, deletion, and export policy
- PII detection/redaction policy
- AI provider abstraction and model routing contract
- Prompt/version registry and prompt injection defense model
- AI tool contracts, tool budgets, timeout and retry policy
- Human-in-the-loop approval policy for risky actions
- Explainability and evidence presentation model
- Conversation memory policy and context budget management
- Dashboard schema versioning and migration policy
- Accessibility / WCAG-oriented UX requirements
- Strict HCI principles and usability heuristics
- Design tokens and soft UI design system
- Empty/loading/error/success states
- Responsive and keyboard-first interaction rules
- Internationalization and localization readiness
- Observability, tracing, metrics, structured logs, and alerting
- Cost/latency budgets
- Backup/restore and disaster-recovery plan
- Threat model and abuse cases
- Feature flags and safe rollout strategy
- Seed/demo datasets and reproducible evaluation fixtures
- API contract conventions and error model
- Developer environment and local-first setup
- CI quality gates
- Definition of Done and release checklist

---

## 3. Repository structure

```text
InsightFlow-AI/
├── apps/
│   ├── web/                    # Next.js frontend
│   └── api/                    # FastAPI backend
├── packages/
│   ├── contracts/              # Shared API/AI/dashboard contracts
│   └── config/                 # Shared conventions
├── docs/
│   ├── architecture/
│   ├── product/
│   ├── ai/
│   ├── data/
│   ├── ux/
│   ├── security/
│   ├── testing/
│   ├── operations/
│   ├── adr/
│   └── original-specifications/
├── infra/
│   ├── docker/
│   ├── nginx/
│   └── postgres/
├── data/
│   └── sample/
├── scripts/
├── tests/
│   ├── e2e/
│   ├── ai-evaluation/
│   └── fixtures/
├── .env.example
├── docker-compose.yml
├── Makefile
└── LICENSE
```

---

## 4. MVP scope

### Must work

1. Account creation/login
2. CSV upload
3. Dataset versioning
4. Dataset preview
5. Schema inference
6. Profiling
7. Data quality report
8. DuckDB analytical execution
9. Natural-language analytical questions
10. Structured AI analysis plans
11. Tool allowlisting and validation
12. Result validation and provenance
13. Grounded AI responses
14. KPI / table / bar / line / scatter visualizations
15. Basic dashboard generation
16. Dashboard save/load
17. Audit trail for AI tool calls

### Explicitly deferred from MVP

- Multi-agent orchestration
- RAG/vector database
- Real-time streaming data
- External business data connectors
- Kubernetes
- Enterprise SSO
- Advanced forecasting
- Autonomous scheduled agents
- Complex semantic federation

These remain documented extension points.

---

## 5. Technology decisions

| Layer | Decision |
|---|---|
| Web | Next.js App Router + TypeScript |
| UI | Tailwind CSS + shadcn/ui patterns |
| State | TanStack Query + minimal Zustand |
| API | FastAPI |
| ORM | SQLAlchemy 2.x |
| Validation | Pydantic v2 |
| App DB | PostgreSQL |
| Analytics | DuckDB |
| Dataframes | Polars; Pandas only for compatibility |
| Numerical | NumPy / SciPy where justified |
| Background work | Redis + worker abstraction, introduced when needed |
| File storage | Local filesystem in dev; S3-compatible in production |
| AI | Provider abstraction; provider selected by environment |
| Testing | Pytest + Vitest/Playwright |
| Packaging | Docker Compose for local development |

---

## 6. Visual system

### Design direction

**Institutional analytics + soft UI + human-centered interaction.**

Avoid neon gradients, excessive glassmorphism, decorative AI imagery, and chat-first layouts.

### Primary palette

- **Ink:** `#172033` — primary text / navigation
- **Slate:** `#536176` — secondary text
- **Cloud:** `#F7F9FC` — application background
- **Surface:** `#FFFFFF` — cards / panels
- **Teal:** `#0F766E` — primary action / positive analytical emphasis
- **Teal Soft:** `#E6F4F1` — soft active state
- **Blue:** `#2563EB` — informational interaction
- **Amber:** `#B45309` — warning
- **Red:** `#B42318` — destructive/error
- **Border:** `#E3E8EF`

The palette is intentionally restrained and supports WCAG-oriented contrast checks.

### Soft UI rules

- 8px base spacing grid
- 10–14px corner radii
- 1px subtle borders preferred over heavy shadows
- Very soft elevation only for floating surfaces
- No gradients for primary UI controls
- Clear focus rings
- Consistent hover/active/disabled states
- Dense data tables with readable row height
- Typography prioritizes hierarchy and scanability

---

## 7. Strict HCI principles

Every screen must be reviewed against:

1. Visibility of system status
2. Match between system and real-world concepts
3. User control and freedom
4. Consistency and standards
5. Error prevention
6. Recognition over recall
7. Flexibility and efficiency
8. Minimalist design
9. Error recovery
10. Help/documentation

Also enforce Shneiderman's rules, WCAG-oriented accessibility, progressive disclosure, clear affordances, reversible actions, and meaningful feedback.

A UI feature is not considered complete until its loading, empty, success, error, permission-denied, and offline/degraded states are defined.

---

## 8. Getting started

### Prerequisites

- Node.js 22+
- Python 3.12+
- Docker Desktop
- Git

### Local infrastructure

```bash
docker compose up -d postgres redis
```

### API

```bash
cd apps/api
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Web

```bash
cd apps/web
npm install
npm run dev
```

The scaffold is intentionally minimal; implementation work should follow `docs/implementation-plan.md`.

---

## 9. Environment variables

Copy `.env.example` to `.env` and configure only the provider/storage values needed for the current phase.

Never commit secrets.

---

## 10. Development order

Follow this order strictly:

```text
Foundation
→ Database
→ Auth
→ Dataset ingestion
→ Profiling
→ Data quality
→ Analytics engine
→ AI tool contracts
→ LLM provider
→ Tool orchestration
→ Result validation
→ Visualization
→ Dashboard
→ AI dashboard editing
→ Security hardening
→ Evaluation
→ Observability
→ Deployment
```

Do not skip the deterministic analytics engine to build the AI layer first.

---

## 11. Definition of Done

A feature is complete only when:

- Acceptance criteria pass
- Unit/integration tests exist
- Loading/empty/error/success states exist
- Accessibility checks pass
- Authorization is enforced server-side
- Logs/metrics exist for important failures
- AI outputs have validation where applicable
- Documentation is updated
- No secret or PII leakage exists
- The feature can be reproduced locally

---

## 12. Documentation map

Start with:

1. `docs/implementation-plan.md`
2. `docs/product/product-spec.md`
3. `docs/architecture/target-architecture.md`
4. `docs/ai/ai-operating-model.md`
5. `docs/data/data-governance.md`
6. `docs/ux/hci-design-system.md`
7. `docs/operations/observability-and-sre.md`
8. `docs/security/threat-model.md`
9. `docs/testing/test-strategy.md`
10. `docs/adr/README.md`

Original specifications remain available under `docs/original-specifications/`.
