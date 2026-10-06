# Phase 14 — Citations & Provenance Architecture

## 1. Traceable Citations
Every business rule, metric definition, or domain constraint referenced by the AI model during reasoning includes an immutable citation:
- **Citation Structure**:
  - `citation_index`: Integer pointer `[1]`, `[2]`, ...
  - `document_id`: Unique identifier of the source document.
  - `document_title`: Human-readable title of the document.
  - `document_version_id` & `version_number`: Exact version at retrieval time.
  - `page_number`: Document page number (for PDF / multi-page docs).
  - `section_heading`: Heading hierarchy context.
  - `chunk_id`: Stored chunk primary key.
  - `source_snippet`: Contextual excerpt verified against the chunk text.
  - `similarity_score`: Retrieval confidence score.

## 2. Provenance Storage
When conversational AI or report generators use business knowledge, the response provenance payload stores:
- `query`: Original user prompt.
- `datasets_used`: List of quantitative dataset IDs & version IDs.
- `analytical_operations`: Exact SQL/DuckDB operations executed.
- `documents_retrieved`: List of document IDs, versions, and chunk IDs.
- `embedding_provider`: Model and dimension used for vector search.
- `retrieval_configuration`: `top_k`, `min_similarity`, and filter parameters.
- `timestamp`: UTC execution timestamp.
