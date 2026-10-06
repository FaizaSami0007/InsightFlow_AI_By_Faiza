"""Anomaly Agent executing anomaly detection, root-cause decomposition, and severity grading."""

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
from app.anomalies.schemas import AnomalyDetectionRequest
from app.anomalies.service import AnomalyService


class AnomalyAgent(BaseAgent):
    """Specialized agent for discovering statistical anomalies and decomposing root causes."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(AgentID.ANOMALY_AGENT, db)
        self.service = AnomalyService(db)

    async def execute(self, request: AgentRequest) -> AgentResponse:
        start_time = time.perf_counter()
        evidence_list: List[EvidenceItem] = []
        claims_list: List[ClaimItem] = []

        params = request.context.get("parameters") or {}
        metric_fields = params.get("metric_fields") or ["revenue"]
        time_field = params.get("time_field") or "order_date"
        dimension_fields = params.get("dimension_fields") or ["region", "category"]

        if not self.is_tool_allowed("detect_dataset_anomalies"):
            return AgentResponse(
                task_id=request.task_id,
                agent_id=self.agent_id,
                status="FAILED",
                summary="Tool 'detect_dataset_anomalies' is not permitted.",
                error_message="Unauthorized tool execution",
                execution_time_ms=(time.perf_counter() - start_time) * 1000.0,
            )

        try:
            anom_req = AnomalyDetectionRequest(
                dataset_id=request.dataset_id,
                dataset_version_id=request.dataset_version_id,
                metric_fields=metric_fields,
                time_field=time_field,
                dimension_fields=dimension_fields,
            )
            result = await self.service.detect_anomalies(request.user_id, anom_req)

            ev_id = f"ev-anom-{uuid.uuid4().hex[:8]}"
            evidence_list.append(
                EvidenceItem(
                    id=ev_id,
                    evidence_type=EvidenceType.ANOMALY,
                    source=f"Anomaly Detector ({len(result.anomalies)} anomalies found)",
                    dataset_version_id=request.dataset_version_id,
                    operation="detect_dataset_anomalies",
                    raw_value={
                        "total_anomalies": result.total_anomalies_count,
                        "critical_count": result.critical_count,
                        "anomalies": [a.model_dump() for a in result.anomalies[:5]],
                    },
                    provenance={"execution_time_ms": result.execution_time_ms},
                )
            )

            claims_list.append(
                ClaimItem(
                    claim_id=f"claim-{uuid.uuid4().hex[:8]}",
                    statement=f"Detected {result.total_anomalies_count} anomalies ({result.critical_count} critical) across {metric_fields}.",
                    claim_type=ClaimType.FACT,
                    evidence_ids=[ev_id],
                )
            )

            summary_text = f"Identified {result.total_anomalies_count} anomalous points in {metric_fields}."

            return AgentResponse(
                task_id=request.task_id,
                agent_id=self.agent_id,
                status="COMPLETED",
                summary=summary_text,
                data_payload={
                    "anomalies_count": result.total_anomalies_count,
                    "critical_count": result.critical_count,
                    "top_anomalies": [a.model_dump() for a in result.anomalies[:3]],
                    "insights": [i.model_dump() for i in result.insights[:3]],
                },
                evidence=evidence_list,
                claims=claims_list,
                tool_calls_executed=[{"tool": "detect_dataset_anomalies", "params": params}],
                execution_time_ms=(time.perf_counter() - start_time) * 1000.0,
            )
        except Exception as ex:
            return AgentResponse(
                task_id=request.task_id,
                agent_id=self.agent_id,
                status="FAILED",
                summary="Anomaly detection failed",
                error_message=str(ex),
                execution_time_ms=(time.perf_counter() - start_time) * 1000.0,
            )
