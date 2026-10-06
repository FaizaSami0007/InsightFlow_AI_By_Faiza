# Phase 15: Evidence Contracts & Critic Validation

## 1. Structured Evidence Contracts
All communication between agents uses strictly typed Pydantic models:
- `EvidenceItem`: Concrete facts extracted from datasets, mathematical engines, or verified knowledge docs.
  - Types: `DATA_FACT`, `KNOWLEDGE_FACT`, `CALCULATION`, `INTERPRETATION`, `ASSUMPTION`
- `ClaimItem`: Explicit analytical statements asserted by agents, linked to supporting `evidence_ids`.
  - Types: `METRIC_VALUE`, `BUSINESS_RULE`, `TREND_ASSERTION`, `ANOMALY_ASSERTION`, `SCENARIO_PROJECTION`, `CORRELATION`

## 2. Critic Agent Auditing
The `CriticAgent` operates as an impartial auditor:
1. **Numerical Verification**: Verifies that numbers cited in narrative claims match DuckDB aggregation results.
2. **Citation Grounding**: Validates that policy rules cited reference real knowledge chunks.
3. **Contradiction Detection**: Flags claims that contradict proven evidence.
4. **Validation Report**: Produces a `ValidationReport` with statuses (`VERIFIED`, `CONTRADICTED`, `UNVERIFIED`, `INSUFFICIENT_EVIDENCE`).

## 3. Result Synthesis
The `ResultSynthesizer` formats the verified findings into structured outputs clearly distinguishing:
- **Data Facts**: Deterministic metrics calculated from data.
- **Knowledge Facts**: Documented enterprise policies and definitions.
- **Calculations & Projections**: Forecasts and scenario simulations.
- **Interpretation & Assumptions**: Contextual business insights.
- **Validation Audit**: Critic grounding status and confidence.
