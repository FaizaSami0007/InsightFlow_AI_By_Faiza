# Phase 14 — Embedding Abstraction & Hybrid Retrieval

## 1. Embedding Provider Abstraction
The `EmbeddingProvider` base class provides a pluggable interface for dense vector representation:
- `DeterministicEmbeddingProvider`: High-efficiency, zero-cloud-dependency 384-dimensional subword and character n-gram hasher with stop-word suppression and L2 normalization. 100% offline reproducible across test environments.
- `CloudEmbeddingProvider`: Extensible adapter for OpenAI (`text-embedding-3-small`/`large`), Google Gemini, Cohere, or local HuggingFace sentence-transformers.

## 2. Hybrid Retrieval Engine (`HybridRetriever`)
Combines dense semantic vector similarity with sparse BM25 keyword matching:
- **Dense Cosine Similarity**: Evaluates semantic orientation between query and document vectors.
- **Sparse BM25 Keyword Frequency**: Evaluates exact business term matches (e.g., specific acronyms, metric names, product IDs).
- **Hybrid Score Formula**:
  $$\text{Score} = \alpha \cdot \text{Sim}_{\text{dense}} + (1 - \alpha) \cdot \text{Score}_{\text{sparse}}$$
- **Relevance Thresholding**: Filters out candidate chunks below minimum confidence (`min_similarity = 0.15` - `0.20`).
- **Sufficient Evidence Flag**: Sets `has_sufficient_evidence = True` only when top candidate surpasses threshold, preventing hallucinatory generation.
