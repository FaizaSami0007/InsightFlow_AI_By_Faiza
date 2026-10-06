"""Supervisor Agent responsible for intent decomposition, task DAG execution, and grounded synthesis."""

import logging
import re
import time
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.agents.anomaly_agent import AnomalyAgent
from app.ai.agents.base import BaseAgent
from app.ai.agents.contracts import (
    AgentID,
    AgentRequest,
    AgentResponse,
    MultiAgentPlan,
    TaskPlanStep,
    TaskType,
    ValidationReport,
)
from app.ai.agents.critic_agent import CriticAgent
from app.ai.agents.data_analyst import DataAnalystAgent
from app.ai.agents.forecasting_agent import ForecastingAgent
from app.ai.agents.knowledge_agent import KnowledgeAgent
from app.ai.agents.reporting_agent import ReportingAgent
from app.ai.agents.scenario_agent import ScenarioAgent
from app.ai.agents.synthesizer import ResultSynthesizer
from app.ai.agents.task_graph import TaskGraph
from app.ai.agents.visualization_agent import VisualizationAgent
from app.database.models.ai import AITask

logger = logging.getLogger(__name__)


class SupervisorAgent(BaseAgent):
    """Central Supervisor Agent orchestrating task planning, specialized agents, and synthesis."""

    def __init__(self, db: Optional[AsyncSession] = None) -> None:
        super().__init__(AgentID.SUPERVISOR, db)  # type: ignore[arg-type]
        if db is not None:
            self.data_analyst = DataAnalystAgent(db)
            self.knowledge_agent = KnowledgeAgent(db)
            self.forecasting_agent = ForecastingAgent(db)
            self.anomaly_agent = AnomalyAgent(db)
            self.scenario_agent = ScenarioAgent(db)
            self.visualization_agent = VisualizationAgent(db)
            self.reporting_agent = ReportingAgent(db)
            self.critic_agent = CriticAgent(db)

    def plan_tasks(self, query: str) -> MultiAgentPlan:
        """Decomposes a user prompt into structured TaskPlanSteps forming a DAG."""
        q_lower = query.lower()
        steps: List[TaskPlanStep] = []

        # Intent Classification Indicators
        is_forecast = any(
            k in q_lower for k in ["forecast", "predict", "trajectory", "outlook", "projection", "future", "project"]
        )
        is_anomaly = any(
            k in q_lower
            for k in [
                "anomaly",
                "anomalies",
                "outlier",
                "outliers",
                "spike",
                "spikes",
                "drop",
                "drops",
                "dips",
                "unusual",
                "unexpected",
                "investigate",
            ]
        )
        is_scenario = any(
            k in q_lower
            for k in [
                "what if",
                "what-if",
                "simulate",
                "sensitivity",
                "assume",
                "increase by",
                "decrease by",
                "drop by",
                "drops by",
                "rise by",
                "drop in",
                "spend decreases",
                "surge in",
            ]
        )

        q_knowledge_check = q_lower.replace("standard deviation", "")
        is_knowledge = any(
            k in q_knowledge_check
            for k in [
                "policy",
                "definition",
                "defined",
                "sla",
                "sop",
                "glossary",
                "rule",
                "rules",
                "terms",
                "criteria",
                "reimbursement",
                "per diem",
                "standard",
                "standards",
                "protocol",
                "timeline",
                "guideline",
                "guidelines",
                "stipend",
                "recognized",
                "categorized",
                "benchmark",
                "benchmarks",
                "approval",
                "discount without",
                "vp signoff",
                "warranty",
                "review evaluation",
                "asc 606",
                "explain",
                "nps",
                "mql",
                "deprecations",
                "grievance",
                "redressal",
            ]
        )
        is_federated = any(
            k in q_lower for k in ["across datasets", "federated", "join", "multi-dataset", "collection"]
        )
        is_report = any(
            k in q_lower for k in ["executive report", "summary report", "briefing", "report on", "executive briefing"]
        )

        # Analytical / computation triggers that require the Data Analyst
        is_data_calc = any(
            k in q_lower
            for k in [
                "average",
                "median",
                "sum",
                "total",
                "count",
                "standard deviation",
                "breakdown",
                "by region",
                "attainment",
                "distribution",
                "correlation",
                "minimum",
                "maximum",
                "distinct",
                "gross sales",
                "units returned",
                "tax collected",
                "gross margin",
                "unit costs",
                "freight charges",
                "payment method",
                "sales reps",
                "skus sold",
                "by warehouse",
                "by shipping",
                "by customer segment",
                "revenue",
                "sales",
                "profit",
                "order",
                "orders",
                "customer",
                "customers",
                "discount",
            ]
        )
        is_comparison = any(
            k in q_lower
            for k in [
                "why did",
                "compare",
                "evaluate",
                "check whether",
                "analyze",
                "review",
                "assess",
                "against",
                "exceed",
                "comply",
                "under asc 606",
                "versus",
            ]
        )

        # Determine if this is a Pure Knowledge query (no dataset calculation or comparison requested)
        is_pure_knowledge = is_knowledge and not (
            is_data_calc or is_comparison or is_forecast or is_anomaly or is_scenario or is_federated or is_report
        )

        if is_pure_knowledge:
            steps.append(
                TaskPlanStep(
                    task_id="task-1-knowledge",
                    agent_id=AgentID.KNOWLEDGE_AGENT,
                    task_type=TaskType.KNOWLEDGE_RETRIEVAL,
                    objective=f"Retrieve domain policy and business definitions for: '{query}'",
                    input_parameters={"query": query, "top_k": 3},
                )
            )
        else:
            # Add Primary Analytical Tasks
            if is_forecast:
                horizon = 6
                m_h = re.search(r"(\d+)\s*(months?|quarters?|days?|periods?|weeks?)", q_lower)
                if m_h:
                    horizon = int(m_h.group(1))

                steps.append(
                    TaskPlanStep(
                        task_id="task-forecast",
                        agent_id=AgentID.FORECASTING_AGENT,
                        task_type=TaskType.FORECAST,
                        objective=f"Generate statistical forecast for {query}",
                        input_parameters={
                            "parameters": {
                                "target_field": "revenue",
                                "time_field": "order_date",
                                "forecast_horizon": horizon,
                            }
                        },
                    )
                )

            if is_anomaly:
                steps.append(
                    TaskPlanStep(
                        task_id="task-anomaly",
                        agent_id=AgentID.ANOMALY_AGENT,
                        task_type=TaskType.ANOMALY_DETECTION,
                        objective=f"Detect dataset anomalies and root cause deltas for: {query}",
                        input_parameters={"parameters": {"metric_fields": ["revenue"], "time_field": "order_date"}},
                    )
                )

            if is_scenario:
                val = 10.0
                m_val = re.search(r"([+-]?\d+(?:\.\d+)?)\s*%", q_lower)
                if m_val:
                    val = float(m_val.group(1))

                steps.append(
                    TaskPlanStep(
                        task_id="task-scenario",
                        agent_id=AgentID.SCENARIO_AGENT,
                        task_type=TaskType.SCENARIO_SIMULATION,
                        objective=f"Simulate what-if parameter modification of {val}%",
                        input_parameters={
                            "parameters": {
                                "target_metric": "revenue",
                                "assumptions": [{"variable": "price", "operation": "PERCENTAGE_CHANGE", "value": val}],
                            }
                        },
                    )
                )

            # Data Analyst Task (for any data query, hybrid comparison, or federated query)
            if (
                is_data_calc
                or is_comparison
                or is_federated
                or (not is_forecast and not is_anomaly and not is_scenario and not is_knowledge)
            ):
                op = (
                    "group_by"
                    if any(k in q_lower for k in ["by", "group", "breakdown", "top", "segment"])
                    else "describe_dataset"
                )
                params: Dict[str, Any] = {}
                if op == "group_by":
                    params = {"dimensions": ["region"], "measures": [{"field": "revenue", "agg": "SUM"}]}

                if is_federated:
                    op = "execute_federated_query"
                    params = {"dimensions": ["region"], "measures": [{"field": "revenue", "agg": "SUM"}]}

                steps.append(
                    TaskPlanStep(
                        task_id="task-data",
                        agent_id=AgentID.DATA_ANALYST,
                        task_type=TaskType.DATA_ANALYSIS,
                        objective=f"Execute deterministic data computation for query: {query}",
                        input_parameters={"operation": op, "parameters": params},
                    )
                )

            # Parallel Knowledge Task if domain context / rules / standards are referenced
            if is_knowledge:
                steps.append(
                    TaskPlanStep(
                        task_id="task-knowledge",
                        agent_id=AgentID.KNOWLEDGE_AGENT,
                        task_type=TaskType.KNOWLEDGE_RETRIEVAL,
                        objective=f"Retrieve domain definitions and policies related to '{query}'",
                        input_parameters={"query": query, "top_k": 2},
                    )
                )

            # Add Visualization Task if data analysis is performed or chart requested
            has_data_step = any(s.agent_id == AgentID.DATA_ANALYST for s in steps)
            if has_data_step or "chart" in q_lower or "recommend" in q_lower:
                data_step_ids = [s.task_id for s in steps if s.agent_id == AgentID.DATA_ANALYST]
                steps.append(
                    TaskPlanStep(
                        task_id="task-viz",
                        agent_id=AgentID.VISUALIZATION_AGENT,
                        task_type=TaskType.VISUALIZATION,
                        objective="Recommend and validate optimal visual chart specification",
                        dependencies=data_step_ids,
                        input_parameters={},
                    )
                )

        # Optional Reporting Step
        if is_report:
            dep_ids = [s.task_id for s in steps]
            steps.append(
                TaskPlanStep(
                    task_id="task-report",
                    agent_id=AgentID.REPORTING_AGENT,
                    task_type=TaskType.REPORTING,
                    objective="Synthesize findings into executive briefing format",
                    dependencies=dep_ids,
                    input_parameters={},
                )
            )

        # Mandatory Final Validation Step
        dep_ids = [s.task_id for s in steps]
        steps.append(
            TaskPlanStep(
                task_id="task-critic-validation",
                agent_id=AgentID.CRITIC_AGENT,
                task_type=TaskType.VALIDATION,
                objective="Audit numerical exactness and citation grounding across agent outputs",
                dependencies=dep_ids,
                input_parameters={},
            )
        )

        # Optional Reporting Step
        if is_report:
            dep_ids = [s.task_id for s in steps]
            steps.append(
                TaskPlanStep(
                    task_id="task-report",
                    agent_id=AgentID.REPORTING_AGENT,
                    task_type=TaskType.REPORTING,
                    objective="Synthesize findings into executive briefing format",
                    dependencies=dep_ids,
                    input_parameters={},
                )
            )

        # Mandatory Final Validation Step
        dep_ids = [s.task_id for s in steps]
        steps.append(
            TaskPlanStep(
                task_id="task-critic-validation",
                agent_id=AgentID.CRITIC_AGENT,
                task_type=TaskType.VALIDATION,
                objective="Audit numerical exactness and citation grounding across agent outputs",
                dependencies=dep_ids,
                input_parameters={},
            )
        )

        return MultiAgentPlan(
            intent_category="MULTI_AGENT_EXECUTION",
            explanation=f"Generated {len(steps)}-step task graph for query.",
            steps=steps,
        )

    async def _dispatch_agent(self, agent_id: AgentID, request: AgentRequest) -> AgentResponse:
        """Dispatches an AgentRequest to the corresponding agent instance."""
        if agent_id == AgentID.DATA_ANALYST:
            return await self.data_analyst.execute(request)
        elif agent_id == AgentID.KNOWLEDGE_AGENT:
            return await self.knowledge_agent.execute(request)
        elif agent_id == AgentID.FORECASTING_AGENT:
            return await self.forecasting_agent.execute(request)
        elif agent_id == AgentID.ANOMALY_AGENT:
            return await self.anomaly_agent.execute(request)
        elif agent_id == AgentID.SCENARIO_AGENT:
            return await self.scenario_agent.execute(request)
        elif agent_id == AgentID.VISUALIZATION_AGENT:
            return await self.visualization_agent.execute(request)
        elif agent_id == AgentID.REPORTING_AGENT:
            return await self.reporting_agent.execute(request)
        elif agent_id == AgentID.CRITIC_AGENT:
            return await self.critic_agent.execute(request)
        else:
            return AgentResponse(
                task_id=request.task_id,
                agent_id=agent_id,
                status="FAILED",
                summary=f"Unknown agent '{agent_id.value}'",
                error_message="Agent not found",
            )

    async def execute(self, request: AgentRequest) -> AgentResponse:
        """Executes full multi-agent workflow: plan -> DAG execute -> critique -> synthesize."""
        start_time = time.perf_counter()

        # Step 1: Decompose query into MultiAgentPlan
        plan = self.plan_tasks(request.query)

        # Step 2: Build TaskGraph
        graph = TaskGraph(request.budget)
        for step in plan.steps:
            graph.add_step(step)

        # Step 3: Execute DAG with parallel batches
        agent_responses = await graph.execute(request, self._dispatch_agent)

        # Step 4: Extract validation report from Critic Agent
        val_report: Optional[ValidationReport] = None
        for resp in agent_responses:
            if resp.agent_id == AgentID.CRITIC_AGENT and resp.data_payload.get("validation_report"):
                val_report = ValidationReport(**resp.data_payload["validation_report"])
                break

        # Step 5: Synthesize grounded response
        synthesized = ResultSynthesizer.synthesize(request.query, agent_responses, val_report)

        # Step 6: Persist Tasks into DB
        for resp in agent_responses:
            try:
                db_task = AITask(
                    conversation_id=request.conversation_id,
                    user_id=request.user_id,
                    agent_id=resp.agent_id.value,
                    task_type="MULTI_AGENT_TASK",
                    status=resp.status,
                    input_json={},
                    output_json=resp.data_payload,
                    evidence_json=[e.model_dump() for e in resp.evidence],
                    error_message=resp.error_message,
                    execution_time_ms=resp.execution_time_ms,
                )
                self.db.add(db_task)
            except Exception as e:
                logger.warning(f"Failed to persist task record: {e}")

        try:
            await self.db.commit()
        except Exception:
            await self.db.rollback()

        return AgentResponse(
            task_id=request.task_id,
            agent_id=self.agent_id,
            status="COMPLETED",
            summary=synthesized["content"],
            data_payload=synthesized,
            evidence=graph.accumulated_evidence,
            citations=synthesized["citations"],
            execution_time_ms=(time.perf_counter() - start_time) * 1000.0,
        )
