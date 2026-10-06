# Phase 14 — HCI & Knowledge Center UX Design

## 1. HCI Heuristics Compliance
The Phase 14 Knowledge Center adheres to Nielsen-Norman heuristics and Shneiderman's direct manipulation principles:
- **Visibility of System Status**: Upload progress indicators, explicit document processing badges (`UPLOADED`, `EXTRACTING`, `CHUNKED`, `EMBEDDED`, `INDEXED`, `READY`, `FAILED`, `STALE`), and clear search confidence states.
- **Recognition Over Recall**: Interactive collection filter dropdowns, document type badges, and preview cards showing exact chunk content and page numbers.
- **Inspectable Citations**: One-click citation badges showing formal document references (`[Sales Policy 2026, p. 14]`) that link directly to source excerpts.
- **Error Prevention & Feedback**: Confirmation modals for document deletions, clear upload status messages with detailed error explanations when unsupported formats are encountered.

## 2. Knowledge Center Navigation
- Accessible via the main sidebar (`/knowledge`, `BookOpen` icon, `Phase 14` badge).
- 4 primary tabs: **Documents & Ingestion**, **Collections Manager**, **Dataset ↔ Knowledge Linking**, and **Hybrid Search & Citations Explorer**.
