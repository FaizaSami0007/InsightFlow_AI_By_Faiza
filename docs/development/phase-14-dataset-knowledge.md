# Phase 14 — Dataset ↔ Knowledge Linking & Semantic Layer

## 1. Domain Contextualization
InsightFlow AI connects qualitative unstructured documents with structured quantitative tables:
- **`DatasetKnowledgeLink`**: Binds datasets or dataset versions to knowledge documents or entire collections.
- **Context Prioritization**: When an analytical query targets a dataset (e.g. `sales_2026.csv`), the retriever prioritizes associated documents (e.g. `Sales_Policy_2026.pdf`).
- **Semantic Layer Integration**: Column definitions in the semantic layer (e.g. `customer_churn`) link directly to formal policy definitions (e.g. `Customers inactive for 90 days are classified as churned`).

## 2. Dynamic Evidence Fusion
When answering hybrid questions:
- The system queries DuckDB to calculate exact aggregates (`churn_rate = 6.8%`).
- The system retrieves the domain document chunk (`churn_inactivity_days = 90`).
- The AI synthesizes the grounded explanation: *"Under the organization's 90-day churn policy [1], the Q3 churn rate increased to 6.8%."*
