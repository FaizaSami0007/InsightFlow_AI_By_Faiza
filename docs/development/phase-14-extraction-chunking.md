# Phase 14 — Extraction & Semantic Chunking Engine

## 1. Document Extraction Pipeline
The `DocumentExtractor` module provides safe, isolated text and structure extraction across business file formats:
- **PDF**: Extracts page-by-page text, detected headings (`#`, `##`, all-caps lines), and page boundaries. For scanned documents, tags OCR metadata and confidence.
- **DOCX**: Parses Word document XML structures, extracts heading styles (`Heading 1`, `Heading 2`, `Title`) and paragraph blocks.
- **TXT / Markdown**: Parses semantic markdown tokens, code blocks, lists, and hierarchical section titles.
- **CSV Reference**: Parses column headers and structured record rows into structured textual knowledge blocks.

## 2. Chunking Engine (`DocumentChunker`)
- **Heading-Aware Bounding**: Retains hierarchical document section titles (e.g. `Policy Section 4.2 > Reimbursement Limits`) with each chunk.
- **Token Limits**: Configurable target token sizes (default: 400 tokens; max: 800 tokens).
- **Contextual Overlap**: 50-token rolling window overlap ensures sentence transitions across chunk boundaries are not lost.
- **Source Offsets**: Persists document version ID, section title, page number, and chunk index with every chunk record.
