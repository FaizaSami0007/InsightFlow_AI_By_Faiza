# Phase 15: Human-Computer Interaction & Multi-Agent UX

## 1. Transparency & Inspectability
Rather than presenting the multi-agent system as an opaque black box, InsightFlow AI provides full visibility into the agent execution lifecycle:
- **Live Pipeline Status**: While processing queries, the UI displays real-time stage transitions (*"Supervisor Planning → Data Analyst / Engine → Critic Validation"*).
- **Interactive Execution Graph Modal**: Users can click the **Agent Graph** button in the header to view the complete DAG of tasks executed for their conversation.
- **Node-Level Audit Trace**: Each task card in the graph drawer displays:
  - Agent name and execution order index
  - Execution duration in milliseconds and token usage
  - Task objective and dependency links
  - Critic validation status and findings summary

## 2. Structured Factual Grounding
Responses clearly separate deterministic facts from knowledge policies and interpretations, allowing business stakeholders to audit calculations and citations directly.
