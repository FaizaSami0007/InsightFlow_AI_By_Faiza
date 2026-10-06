"""Data Analyst Agent executing deterministic analytical operations over DuckDB and Polars."""

import time
import uuid
from typing import Any, Dict, List

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
from app.analytics.schemas import AnalysisRunRequest
from app.analytics.service import analytics_service
from app.database.models.user import User


class DataAnalystAgent(BaseAgent):
    """Specialized agent for quantitative calculations, aggregations, and data profiling."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(AgentID.DATA_ANALYST, db)

    async def execute(self, request: AgentRequest) -> AgentResponse:
        start_time = time.perf_counter()
        evidence_list: List[EvidenceItem] = []
        claims_list: List[ClaimItem] = []
        tool_calls: List[Dict[str, Any]] = []

        # Determine analytical tool based on context or query intent
        op = request.context.get("operation") or "describe_dataset"
        params = request.context.get("parameters") or {}

        # Default fallback if describe_dataset
        if "describe_dataset" in op or not params:
            tool_name = "describe_dataset"
            tool_params = {}
        else:
            tool_name = op
            tool_params = params

        if not self.is_tool_allowed(tool_name):
            return AgentResponse(
                task_id=request.task_id,
                agent_id=self.agent_id,
                status="FAILED",
                summary=f"Tool '{tool_name}' is not permitted for Data Analyst Agent.",
                error_message=f"Unauthorized tool execution: {tool_name}",
                execution_time_ms=(time.perf_counter() - start_time) * 1000.0,
            )

        mock_user = User(id=request.user_id, email="agent@insightflow.ai", full_name="AI Agent")

        # Execute deterministic analytics tool
        try:
            if tool_name == "execute_federated_query":
                from app.federation.schemas import FederatedAnalysisRequest
                from app.federation.service import federation_service

                fed_req = FederatedAnalysisRequest(
                    dataset_version_ids=tool_params.get("dataset_version_ids", [request.dataset_version_id]),
                    dimensions=tool_params.get("dimensions", []),
                    measures=tool_params.get("measures", []),
                    filters=tool_params.get("filters", []),
                    limit=tool_params.get("limit", 100),
                )
                fed_res = await federation_service.execute_federated_analysis(fed_req, request.user_id, self.db)
                tool_calls.append({"tool": tool_name, "params": tool_params, "result": fed_res.model_dump()})
                ev_id = f"ev-fed-{uuid.uuid4().hex[:8]}"
                evidence_list.append(
                    EvidenceItem(
                        id=ev_id,
                        evidence_type=EvidenceType.DATA,
                        source="Federated Datasets",
                        dataset_version_id=request.dataset_version_id,
                        operation=tool_name,
                        raw_value=fed_res.rows,
                        provenance=fed_res.provenance,
                    )
                )
                claims_list.append(
                    ClaimItem(
                        claim_id=f"claim-{uuid.uuid4().hex[:8]}",
                        statement=f"Federated query across {len(fed_res.datasets_involved)} datasets returned {fed_res.row_count} aggregated rows.",
                        claim_type=ClaimType.FACT,
                        evidence_ids=[ev_id],
                    )
                )
                summary_text = f"Executed federated join across datasets: {fed_res.join_path_description}"
                data_payload = {"rows": fed_res.rows, "columns": fed_res.columns, "row_count": fed_res.row_count}

            else:
                run_req = AnalysisRunRequest(
                    dataset_id=request.dataset_id,
                    dataset_version_id=request.dataset_version_id,
                    tool_name=tool_name,
                    parameters=tool_params,
                )
                result = await analytics_service.run_analysis(run_req, mock_user, self.db)
                tool_calls.append({"tool": tool_name, "params": tool_params, "result": result.model_dump()})

                ev_id = f"ev-data-{uuid.uuid4().hex[:8]}"
                evidence_list.append(
                    EvidenceItem(
                        id=ev_id,
                        evidence_type=EvidenceType.CALCULATION
                        if "group_by" in tool_name or "aggregate" in tool_name
                        else EvidenceType.DATA,
                        source=f"Dataset {request.dataset_id}",
                        dataset_version_id=request.dataset_version_id,
                        operation=tool_name,
                        raw_value=result.result_data,
                        provenance={"analysis_id": result.id, "execution_time_ms": result.execution_time_ms},
                    )
                )
                claims_list.append(
                    ClaimItem(
                        claim_id=f"claim-{uuid.uuid4().hex[:8]}",
                        statement=f"Operation '{tool_name}' computed successfully with {result.row_count} records returned.",
                        claim_type=ClaimType.CALCULATION,
                        evidence_ids=[ev_id],
                    )
                )
                summary_text = f"Computed {tool_name} with result {result.result_summary or result.result_data}"
                data_payload = {
                    "analysis_id": result.id,
                    "result_data": result.result_data,
                    "summary": result.result_summary,
                }

            return AgentResponse(
                task_id=request.task_id,
                agent_id=self.agent_id,
                status="COMPLETED",
                summary=summary_text,
                data_payload=data_payload,
                evidence=evidence_list,
                claims=claims_list,
                tool_calls_executed=tool_calls,
                execution_time_ms=(time.perf_counter() - start_time) * 1000.0,
            )
        except Exception as ex:
            return AgentResponse(
                task_id=request.task_id,
                agent_id=self.agent_id,
                status="FAILED",
                summary="Analytical computation failed",
                error_message=str(ex),
                execution_time_ms=(time.perf_counter() - start_time) * 1000.0,
            )
