# Phase 15: Agent Registry & Tool Allowlists

## 1. Static Agent Registry
InsightFlow AI implements a centralized, immutable `AgentRegistry` that defines the exact capabilities, token budgets, timeout constraints, and static tool allowlists for every agent in the multi-agent ecosystem.

## 2. Tool Allowlists per Agent

| Agent ID | System Role | Allowed Tools | Max Tokens | Timeout |
| :--- | :--- | :--- | :--- | :--- |
| `supervisor` | Orchestration & DAG Planner | `dispatch_agent_task`, `cancel_task`, `synthesize_results` | 4,000 | 60s |
| `data_analyst` | Deterministic Data Analytics | `duckdb_query`, `aggregate_dataset`, `group_by`, `federated_query` | 4,000 | 45s |
| `knowledge_agent` | Knowledge RAG & Citations | `search_knowledge_hybrid`, `get_document_section`, `extract_citations` | 3,000 | 30s |
| `forecasting_agent` | Statistical Time-Series | `run_time_series_forecast`, `backtest_forecast_models` | 4,000 | 60s |
| `anomaly_agent` | Anomaly & Outlier Analysis | `detect_dataset_anomalies`, `analyze_root_cause_breakdown` | 4,000 | 45s |
| `scenario_agent` | What-If Simulation | `simulate_scenario_model`, `calculate_sensitivity_table` | 4,000 | 45s |
| `visualization_agent` | Chart Recommendation & Spec | `recommend_chart_spec`, `validate_chart_spec` | 2,000 | 20s |
| `reporting_agent` | Executive Report Builder | `compile_executive_report`, `format_report_markdown` | 4,000 | 30s |
| `critic_agent` | Factual & Grounding Auditor | `validate_claim_grounding`, `check_numerical_consistency` | 3,000 | 30s |

## 3. Enforcement
Any attempt by a subagent to invoke a tool outside its registered allowlist raises `ToolAccessDeniedError` immediately, preventing privilege escalation and prompt injection attacks.
