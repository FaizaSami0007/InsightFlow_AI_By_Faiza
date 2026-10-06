# Phase 14 — RAG Pipeline & Hybrid Retrieval

## 1. Pipeline Stages
The retrieval-augmented generation pipeline follows 7 deterministic stages:
1. **Query Intent Classification**: Classifies query into `DATA_ONLY`, `KNOWLEDGE_ONLY`, `HYBRID_ANALYTICS_KNOWLEDGE`, `FORECAST_KNOWLEDGE`, `SCENARIO_KNOWLEDGE`, or `OUT_OF_SCOPE`.
2. **Metadata Filtering**: Scopes candidates to authorized user, tenant workspace, collection, and linked dataset versions.
3. **Dense Vector Retrieval**: Computes cosine similarity between query embeddings and stored chunk embeddings.
4. **Keyword BM25 Scoring**: Evaluates term frequency and sub-stem weighting across chunk contents.
5. **Score Fusion & Ranking**: Calculates hybrid score: `Score = 0.65 * CosineSimilarity + 0.35 * KeywordScore`.
6. **Sufficiency & Threshold Validation**: Ensures top candidate surpasses minimum similarity threshold (`min_similarity >= 0.15` / `0.20`). If insufficient evidence exists, triggers explicit refusal.
7. **Citation Formatting & Provenance Injection**: Builds structured citations (`[Document Title, p. X]`) and records full retrieval provenance.

## 2. Evidence Fusion Protocol
The LLM prompt format enforces strict role separation:
- `DATA FACT`: Numbers derived directly from dataset queries or aggregation operations.
- `KNOWLEDGE FACT`: Factual rules and definitions extracted directly from verified chunks.
- `CALCULATION`: Deterministic formulas evaluated by the analytics engine.
- `INTERPRETATION`: Domain-grounded qualitative explanations combining facts and metrics.
- `ASSUMPTION`: Explicit hypotheses flagged during what-if simulations.
