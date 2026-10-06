# Phase 14 — Known Issues & Mitigations

## 1. Known Limitations & Mitigations
- **Large PDF OCR Latency**: High-resolution scanned documents with hundreds of pages may require multi-second extraction times. *Mitigation*: Extracted chunks are cached and stored with SHA-256 content checksums to eliminate redundant re-parsing.
- **Complex Embedded Charts in Word/PDF**: Visual diagrams within documents are extracted via structural text captions rather than visual tensor reconstruction. *Mitigation*: Structural heading association tags keep caption context bound to adjacent paragraph chunks.
- **Local Embedding Provider vs Cloud Large-Models**: The offline deterministic embedding provider uses 384-dimensional n-gram hashing for zero-dependency execution. *Mitigation*: Pluggable provider architecture enables one-line drop-in configuration of OpenAI/Gemini/Cohere vector models via environment variables.
