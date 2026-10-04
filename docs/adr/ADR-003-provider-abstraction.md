# ADR-003 — LLM Provider Abstraction

**Decision:** Business logic depends on an internal LLM provider interface rather than a vendor SDK directly.

**Reason:** Model/provider changes should not force an architecture rewrite.
