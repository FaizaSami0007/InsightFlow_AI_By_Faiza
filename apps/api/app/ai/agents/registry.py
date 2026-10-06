"""Agent Registry declaring all specialized agents, capabilities, and tool permissions."""

from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.ai.agents.contracts import AgentID, TaskType


class AgentDefinition(BaseModel):
    """Metadata specification for a registered agent."""
    model_config = ConfigDict(extra="ignore")

    agent_id: AgentID
    name: str
    description: str
    primary_task_type: TaskType
    capabilities: List[str] = Field(default_factory=list)
    allowed_tools: List[str] = Field(default_factory=list)
    prohibited_tools: List[str] = Field(default_factory=list)
    timeout_seconds: float = 20.0
    token_budget: int = 4000
    is_autonomous_action_allowed: bool = False


class AgentRegistry:
    """Central registry of all specialized agents in InsightFlow AI."""

    def __init__(self) -> None:
        self._agents: Dict[AgentID, AgentDefinition] = {}
        self._register_default_agents()

    def _register_default_agents(self) -> None:
        # 1. Supervisor / Orchestrator Agent
        self.register(
            AgentDefinition(
                agent_id=AgentID.SUPERVISOR,
                name="Supervisor & Task Planner Agent",
                description="Classifies intent, decomposes complex requests into DAG task plans, coordinates agents, and synthesizes grounded answers.",
                primary_task_type=TaskType.PLANNING,
                capabilities=["intent_classification", "task_decomposition", "dag_scheduling", "evidence_synthesis"],
                allowed_tools=[],
                prohibited_tools=["*"],
                timeout_seconds=30.0,
                token_budget=6000,
            )
        )

        # 2. Data Analyst Agent
        self.register(
            AgentDefinition(
                agent_id=AgentID.DATA_ANALYST,
                name="Data Analyst Agent",
                description="Executes deterministic data operations, aggregations, percentiles, correlations, group-bys, and multi-dataset federations.",
                primary_task_type=TaskType.DATA_ANALYSIS,
                capabilities=["dataset_profiling", "group_by", "aggregations", "percentiles", "correlations", "federation"],
                allowed_tools=[
                    "describe_dataset",
                    "group_by",
                    "correlation",
                    "filter_and_sort_data",
                    "frequency",
                    "percentiles",
                    "time_series_aggregate",
                    "execute_federated_query",
                ],
                prohibited_tools=["search_business_knowledge", "delete_dataset", "manage_users"],
                timeout_seconds=25.0,
                token_budget=4000,
            )
        )

        # 3. Knowledge / Domain RAG Agent
        self.register(
            AgentDefinition(
                agent_id=AgentID.KNOWLEDGE_AGENT,
                name="Domain Knowledge Agent",
                description="Retrieves domain policies, KPI definitions, SLA benchmarks, and SOP guides via hybrid dense/sparse RAG with citations.",
                primary_task_type=TaskType.KNOWLEDGE_RETRIEVAL,
                capabilities=["rag_retrieval", "kpi_glossary", "policy_lookup", "citation_formatting"],
                allowed_tools=["search_business_knowledge"],
                prohibited_tools=["group_by", "describe_dataset", "execute_federated_query"],
                timeout_seconds=20.0,
                token_budget=4000,
            )
        )

        # 4. Forecasting Agent
        self.register(
            AgentDefinition(
                agent_id=AgentID.FORECASTING_AGENT,
                name="Predictive Forecasting Agent",
                description="Preprocesses time-series, tests stationarity/seasonality, and executes statistical forecasts with prediction bounds.",
                primary_task_type=TaskType.FORECAST,
                capabilities=["time_series_forecasting", "model_selection", "backtesting", "prediction_intervals"],
                allowed_tools=["run_time_series_forecast", "time_series_aggregate"],
                prohibited_tools=["search_business_knowledge", "simulate_what_if_scenario"],
                timeout_seconds=30.0,
                token_budget=4000,
            )
        )

        # 5. Anomaly Investigation Agent
        self.register(
            AgentDefinition(
                agent_id=AgentID.ANOMALY_AGENT,
                name="Anomaly Investigation Agent",
                description="Detects statistical anomalies, spikes, drops, and evaluates multi-dimensional root-cause contribution deltas.",
                primary_task_type=TaskType.ANOMALY_DETECTION,
                capabilities=["outlier_detection", "trend_break_detection", "root_cause_analysis", "severity_grading"],
                allowed_tools=["detect_dataset_anomalies", "group_by", "time_series_aggregate"],
                prohibited_tools=["run_time_series_forecast", "search_business_knowledge"],
                timeout_seconds=25.0,
                token_budget=4000,
            )
        )

        # 6. Scenario Simulation Agent
        self.register(
            AgentDefinition(
                agent_id=AgentID.SCENARIO_AGENT,
                name="Decision Intelligence & Scenario Agent",
                description="Executes deterministic parameter sensitivity sweeps, what-if simulations, and branch comparisons over immutable data.",
                primary_task_type=TaskType.SCENARIO_SIMULATION,
                capabilities=["what_if_simulation", "sensitivity_sweeps", "branch_comparison", "elasticity_modeling"],
                allowed_tools=["simulate_what_if_scenario", "group_by", "describe_dataset"],
                prohibited_tools=["run_time_series_forecast"],
                timeout_seconds=25.0,
                token_budget=4000,
            )
        )

        # 7. Visualization Agent
        self.register(
            AgentDefinition(
                agent_id=AgentID.VISUALIZATION_AGENT,
                name="Visualization Intelligence Agent",
                description="Recommends optimal chart types based on cardinality and semantic types, validates specs, and ensures visual accessibility.",
                primary_task_type=TaskType.VISUALIZATION,
                capabilities=["chart_recommendation", "spec_validation", "palette_selection", "chart_refinement"],
                allowed_tools=["describe_dataset"],
                prohibited_tools=["run_time_series_forecast", "search_business_knowledge"],
                timeout_seconds=15.0,
                token_budget=3000,
            )
        )

        # 8. Reporting Agent
        self.register(
            AgentDefinition(
                agent_id=AgentID.REPORTING_AGENT,
                name="Executive Reporting Agent",
                description="Compiles multi-step findings into executive summaries, key takeaways, and structured reporting artifacts.",
                primary_task_type=TaskType.REPORTING,
                capabilities=["executive_summaries", "findings_synthesis", "audit_trace_preservation"],
                allowed_tools=[],
                prohibited_tools=["*"],
                timeout_seconds=20.0,
                token_budget=4000,
            )
        )

        # 9. Validation / Critic Agent
        self.register(
            AgentDefinition(
                agent_id=AgentID.CRITIC_AGENT,
                name="Critic & Validation Agent",
                description="Verifies numerical accuracy against tool outputs, validates document citation grounding, and flags contradictions.",
                primary_task_type=TaskType.VALIDATION,
                capabilities=["numerical_consistency_check", "citation_grounding_audit", "contradiction_detection"],
                allowed_tools=[],
                prohibited_tools=["*"],
                timeout_seconds=20.0,
                token_budget=4000,
            )
        )

    def register(self, definition: AgentDefinition) -> None:
        self._agents[definition.agent_id] = definition

    def get_agent(self, agent_id: AgentID) -> Optional[AgentDefinition]:
        return self._agents.get(agent_id)

    def list_agents(self) -> List[AgentDefinition]:
        return list(self._agents.values())

    def is_tool_allowed(self, agent_id: AgentID, tool_name: str) -> bool:
        agent = self.get_agent(agent_id)
        if not agent:
            return False
        if "*" in agent.prohibited_tools:
            return False
        if tool_name in agent.prohibited_tools:
            return False
        return tool_name in agent.allowed_tools


agent_registry = AgentRegistry()
