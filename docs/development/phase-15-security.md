# Phase 15: Security & Adversarial Defense Architecture

## 1. Adversarial Attack Vectors Mitigated
1. **Prompt Injection & Privilege Escalation**:
   - Attacks attempting to instruct subagents to execute arbitrary code or unauthorized system tools are blocked by immutable tool allowlists in `AgentRegistry`.
2. **Context Poisoning from Untrusted Documents**:
   - Document chunks retrieved by RAG are treated as passive untrusted data and wrapped in structured `EvidenceItem` models rather than executed as instructions.
3. **Denial-of-Service (DoS) via Cyclic or Infinite Task Spawn**:
   - The `TaskGraph` engine detects cycles with Kahn's algorithm and enforces a strict maximum node count and recursion depth bound.
4. **Tenant Isolation & IDOR Protection**:
   - Subagents inherit tenant and user context from the active session. All underlying service calls enforce row-level tenant boundaries.
5. **Hallucination & Fabrication Mitigation**:
   - The `CriticAgent` inspects all claims before final synthesis, preventing agents from fabricating numbers or policies.
