# Phase 14 — Knowledge Intelligence Architecture

## 1. Overview
Phase 14 introduces enterprise-grade Knowledge Intelligence and Retrieval-Augmented Generation (RAG) into InsightFlow AI. The system ingests, extracts, chunks, embeds, retrieves, cites, and reasons over domain business documents while grounding all analytical reasoning in verifiable source material.

## 2. Core Architecture & Evidence Fusion
The system strictly maintains the core principle:
- **DATA ENGINE**: Calculates quantitative analytics, forecasts, anomalies, and what-if scenarios deterministically.
- **KNOWLEDGE ENGINE**: Ingests, parses, and retrieves domain policies, metrics, KPI glossaries, and SOP rules.
- **RAG PIPELINE**: Supplies contextual evidence to AI agents with strict bounding delimiters.
- **AI ORCHESTRATION**: Interprets quantitative results through domain definitions.
- **EVIDENCE FUSION**: Explicitly segregates `DATA FACT`, `KNOWLEDGE FACT`, `CALCULATION`, `INTERPRETATION`, and `ASSUMPTION`.
- **PROVENANCE & CITATION**: Records exact document, version, section, page, and chunk offsets for full auditability.

```
USER QUERY
    ↓
QUERY UNDERSTANDING & INTENT ROUTING
    ↓
┌──────────────────────────────────────────────────────────┐
│  DATA ENGINE              │  KNOWLEDGE ENGINE            │
│  - Profiling & DuckDB     │  - Document Extractor        │
│  - Analytics Engine       │  - Structural Chunker        │
│  - Predictive Forecast    │  - Deterministic Embeddings  │
│  - Anomaly Detector       │  - Hybrid Vector Retriever   │
│  - Scenario Simulation    │  - Citation Generator        │
└──────────────────────────────────────────────────────────┘
                            ↓
                    EVIDENCE FUSION LAYER
                            ↓
                    GROUNDED AI REASONING
                            ↓
                FORMAL CITATIONS & AUDIT PROVENANCE
```

## 3. Data Models
- `KnowledgeCollection`: Organizes documents by domain or department.
- `KnowledgeDocument`: Primary document entity with metadata and lifecycle state.
- `KnowledgeDocumentVersion`: Immutable document version preserving historical chunk citations.
- `KnowledgeChunk`: Structural slice containing page numbers, section headers, token counts, and embeddings.
- `DatasetKnowledgeLink`: Binds quantitative datasets with qualitative reference documents.
