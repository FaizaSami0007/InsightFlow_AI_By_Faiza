"""Scenario Agent executing deterministic what-if simulations, sensitivity analysis, and comparisons."""

import time
import uuid
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.agents.base import BaseAgent
from app.ai.agents.contracts import (
    AgentID,
    AgentRequest,
    AgentResponse,
    ClaimItem,
    ClaimType,
    EvidenceItem,
    EvidenceType,
)
from app.scenarios.schemas import AssumptionSpec, WhatIfScenarioRequest
from app.scenarios.service import ScenarioService


class ScenarioAgent(BaseAgent):
    """Specialized agent for simulating what-if business assumptions and sensitivity sweeps."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(AgentID.SCENARIO_AGENT, db)
        self.service = ScenarioService(db)

    async def execute(self, request: AgentRequest) -> AgentResponse:
        start_time = time.perf_counter()
        evidence_list: List[EvidenceItem] = []
        claims_list: List[ClaimItem] = []

        params = request.context.get("parameters") or {}
        target_metric = params.get("target_metric") or "revenue"
        raw_assumptions = params.get("assumptions") or [
            {"variable": "price", "operation": "PERCENTAGE_CHANGE", "value": 10.0}
        ]

        if not self.is_tool_allowed("simulate_what_if_scenario"):
            return AgentResponse(
                task_id=request.task_id,
                agent_id=self.agent_id,
                status="FAILED",
                summary="Tool 'simulate_what_if_scenario' is not permitted.",
                error_message="Unauthorized tool execution",
                execution_time_ms=(time.perf_counter() - start_time) * 1000.0,
            )

        try:
            assumptions = [
                AssumptionSpec(
                    variable=a.get("variable", "price"),
                    operation=a.get("operation", "PERCENTAGE_CHANGE"),
                    value=float(a.get("value", 0.0)),
                    unit=a.get("unit"),
                    description=a.get("description"),
                )
                for a in raw_assumptions
            ]

            sc_req = WhatIfScenarioRequest(
                dataset_id=request.dataset_id,
                dataset_version_id=request.dataset_version_id,
                name=f"What-If Simulation for {target_metric}",
                target_metric=target_metric,
                assumptions=assumptions,
            )

            result = await self.service.run_what_if_scenario(sc_req, request.user_id)

            ev_id = f"ev-sc-{uuid.uuid4().hex[:8]}"
            evidence_list.append(
                EvidenceItem(
                    id=ev_id,
                    evidence_type=EvidenceType.SCENARIO,
                    source="Deterministic Scenario Engine",
                    dataset_version_id=request.dataset_version_id,
                    operation="simulate_what_if_scenario",
                    raw_value={
                        "target_metric": target_metric,
                        "baseline_value": result.baseline_value,
                        "scenario_value": result.scenario_value,
                        "absolute_change": result.absolute_change,
                        "percentage_change": result.percentage_change,
                    },
                    provenance=result.provenance,
                )
            )

            claims_list.append(
                ClaimItem(
                    claim_id=f"claim-{uuid.uuid4().hex[:8]}",
                    statement=f"Simulated {target_metric} delta: baseline {result.baseline_value:,.2f} → scenario {result.scenario_value:,.2f} ({result.percentage_change:+.2f}%).",
                    claim_type=ClaimType.ASSUMPTION,
                    evidence_ids=[ev_id],
                )
            )

            summary_text = (
                f"Simulated {target_metric} change: {result.absolute_change:+,.2f} ({result.percentage_change:+.2f}%)."
            )

            return AgentResponse(
                task_id=request.task_id,
                agent_id=self.agent_id,
                status="COMPLETED",
                summary=summary_text,
                data_payload={
                    "scenario_id": result.id,
                    "target_metric": target_metric,
                    "baseline_value": result.baseline_value,
                    "scenario_value": result.scenario_value,
                    "delta_pct": result.percentage_change,
                    "delta_abs": result.absolute_change,
                },
                evidence=evidence_list,
                claims=claims_list,
                tool_calls_executed=[{"tool": "simulate_what_if_scenario", "params": params}],
                execution_time_ms=(time.perf_counter() - start_time) * 1000.0,
            )
        except Exception as ex:
            return AgentResponse(
                task_id=request.task_id,
                agent_id=self.agent_id,
                status="FAILED",
                summary="Scenario simulation failed",
                error_message=str(ex),
                execution_time_ms=(time.perf_counter() - start_time) * 1000.0,
            )
