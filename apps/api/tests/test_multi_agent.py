"""Unit and integration tests for Phase 15 Multi-Agent Intelligence & Advanced AI Orchestration."""

import pytest
from fastapi.testclient import TestClient

from app.ai.agents.contracts import (
    AgentID,
    AgentRequest,
    EvidenceItem,
    EvidenceType,
    ExecutionBudget,
    TaskPlanStep,
    TaskType,
    ValidationStatus,
)
from app.ai.agents.critic_agent import CriticAgent
from app.ai.agents.registry import agent_registry
from app.ai.agents.supervisor import SupervisorAgent
from app.ai.agents.task_graph import TaskGraph, TaskGraphCycleError
from tests.conftest import TestingSessionLocal


@pytest.mark.asyncio
async def test_agent_registry_allowlists_and_budgets() -> None:
    """Verifies that all 9 agents are registered with correct tool permissions."""
    agents = agent_registry.list_agents()
    assert len(agents) >= 9

    # 1. Data Analyst tool permissions
    assert agent_registry.is_tool_allowed(AgentID.DATA_ANALYST, "describe_dataset") is True
    assert agent_registry.is_tool_allowed(AgentID.DATA_ANALYST, "group_by") is True
    assert agent_registry.is_tool_allowed(AgentID.DATA_ANALYST, "search_business_knowledge") is False

    # 2. Knowledge Agent tool permissions
    assert agent_registry.is_tool_allowed(AgentID.KNOWLEDGE_AGENT, "search_business_knowledge") is True
    assert agent_registry.is_tool_allowed(AgentID.KNOWLEDGE_AGENT, "describe_dataset") is False

    # 3. Forecasting Agent tool permissions
    assert agent_registry.is_tool_allowed(AgentID.FORECASTING_AGENT, "run_time_series_forecast") is True
    assert agent_registry.is_tool_allowed(AgentID.FORECASTING_AGENT, "simulate_what_if_scenario") is False

    # 4. Critic Agent tool permissions (pure auditor, no execution tools)
    assert agent_registry.is_tool_allowed(AgentID.CRITIC_AGENT, "group_by") is False


@pytest.mark.asyncio
async def test_task_graph_dag_execution_and_cycle_detection() -> None:
    """Tests topological batching, parallel execution, and cycle detection."""
    # Test 1: Valid DAG with parallel branches
    graph = TaskGraph(ExecutionBudget(max_tasks=5, max_recursion_depth=3))
    step1 = TaskPlanStep(
        task_id="t1",
        agent_id=AgentID.DATA_ANALYST,
        task_type=TaskType.DATA_ANALYSIS,
        objective="Data Step 1",
    )
    step2 = TaskPlanStep(
        task_id="t2",
        agent_id=AgentID.KNOWLEDGE_AGENT,
        task_type=TaskType.KNOWLEDGE_RETRIEVAL,
        objective="Knowledge Step 2",
    )
    step3 = TaskPlanStep(
        task_id="t3",
        agent_id=AgentID.CRITIC_AGENT,
        task_type=TaskType.VALIDATION,
        objective="Validation Step 3",
        dependencies=["t1", "t2"],
    )
    graph.add_step(step1)
    graph.add_step(step2)
    graph.add_step(step3)

    batches = graph.validate_and_get_batches()
    assert len(batches) == 2
    # Batch 0 contains t1 and t2 in parallel
    batch_0_ids = {n.task_id for n in batches[0]}
    assert batch_0_ids == {"t1", "t2"}
    # Batch 1 contains t3
    assert batches[1][0].task_id == "t3"

    # Test 2: Cyclical graph should raise TaskGraphCycleError
    cycle_graph = TaskGraph()
    c1 = TaskPlanStep(task_id="c1", agent_id=AgentID.DATA_ANALYST, task_type=TaskType.DATA_ANALYSIS, objective="C1", dependencies=["c2"])
    c2 = TaskPlanStep(task_id="c2", agent_id=AgentID.KNOWLEDGE_AGENT, task_type=TaskType.KNOWLEDGE_RETRIEVAL, objective="C2", dependencies=["c1"])
    cycle_graph.add_step(c1)
    cycle_graph.add_step(c2)

    with pytest.raises(TaskGraphCycleError):
        cycle_graph.validate_and_get_batches()


@pytest.mark.asyncio
async def test_critic_agent_validation() -> None:
    """Tests that CriticAgent audits numerical consistency and citation grounding."""
    async with TestingSessionLocal() as db:
        critic = CriticAgent(db)

        # Case 1: Valid evidence with provenance
        ev1 = EvidenceItem(
            id="ev-1",
            evidence_type=EvidenceType.KNOWLEDGE,
            source="Refund Policy Document",
            operation="search_business_knowledge",
            raw_value="Refunds are valid within 30 days.",
            provenance={"document_id": "doc-1", "page_number": 2},
        )
        ev2 = EvidenceItem(
            id="ev-2",
            evidence_type=EvidenceType.CALCULATION,
            source="Dataset Analysis",
            operation="group_by",
            raw_value=[{"region": "North", "revenue": 1000}],
            provenance={"analysis_id": "ana-1"},
        )

        req = AgentRequest(
            task_id="t-crit",
            conversation_id="conv-1",
            user_id="user-1",
            dataset_id="ds-1",
            dataset_version_id="ver-1",
            query="Audit findings",
            objective="Validate evidence",
            prior_evidence=[ev1, ev2],
        )

        resp = await critic.execute(req)
        assert resp.status == "COMPLETED"
        report = resp.data_payload["validation_report"]
        assert report["overall_status"] == ValidationStatus.VALID.value
        assert report["numerical_consistency"] is True
        assert report["citation_grounding"] is True
        assert report["validation_score"] == 1.0


@pytest.mark.asyncio
async def test_supervisor_planning_heuristics() -> None:
    """Verifies that SupervisorAgent decomposes prompts into correct task DAGs."""
    async with TestingSessionLocal() as db:
        supervisor = SupervisorAgent(db)

        # 1. Forecasting query
        plan_fc = supervisor.plan_tasks("Forecast revenue for the next 12 months")
        agent_ids_fc = [s.agent_id for s in plan_fc.steps]
        assert AgentID.FORECASTING_AGENT in agent_ids_fc
        assert AgentID.CRITIC_AGENT in agent_ids_fc

        # 2. Anomaly query
        plan_anom = supervisor.plan_tasks("Why are there unusual anomalies and drops in sales?")
        agent_ids_anom = [s.agent_id for s in plan_anom.steps]
        assert AgentID.ANOMALY_AGENT in agent_ids_anom
        assert AgentID.CRITIC_AGENT in agent_ids_anom

        # 3. What-if Scenario query
        plan_sc = supervisor.plan_tasks("What if price increases by 15%?")
        agent_ids_sc = [s.agent_id for s in plan_sc.steps]
        assert AgentID.SCENARIO_AGENT in agent_ids_sc

        # 4. Knowledge query
        plan_kn = supervisor.plan_tasks("What is our official refund policy definition and SLA terms?")
        agent_ids_kn = [s.agent_id for s in plan_kn.steps]
        assert AgentID.KNOWLEDGE_AGENT in agent_ids_kn


def test_agent_api_endpoints(client: TestClient) -> None:
    """Verifies /api/v1/ai/agents endpoint returns registered agents."""
    client.post(
        "/api/v1/auth/register",
        json={"email": "agent_test_user@example.com", "password": "Password123!", "full_name": "Agent Tester"},
    )
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "agent_test_user@example.com", "password": "Password123!"},
    )
    token = login_res.json()["access_token"]

    resp = client.get("/api/v1/ai/agents", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    agents = resp.json()
    assert len(agents) >= 9
    agent_names = [a["name"] for a in agents]
    assert any("Supervisor" in n for n in agent_names)
    assert any("Data Analyst" in n for n in agent_names)
    assert any("Knowledge" in n for n in agent_names)
    assert any("Forecasting" in n for n in agent_names)
    assert any("Critic" in n for n in agent_names)

