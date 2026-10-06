"""Reporting Agent organizing multi-agent findings into structured executive summaries."""

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


class ReportingAgent(BaseAgent):
    """Specialized agent for synthesizing multi-agent findings into structured executive reports."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(AgentID.REPORTING_AGENT, db)

    async def execute(self, request: AgentRequest) -> AgentResponse:
        start_time = time.perf_counter()
        evidence_list: List[EvidenceItem] = []
        claims_list: List[ClaimItem] = []

        findings: List[str] = []
        for ev in request.prior_evidence:
            findings.append(f"- [{ev.evidence_type.value}] {ev.operation} from {ev.source}")

        report_summary = (
            f"Executive Report on: {request.query}\n\n"
            f"Key Findings ({len(request.prior_evidence)} evidence sources):\n"
            + ("\n".join(findings) if findings else "No prior evidence generated.")
        )

        ev_id = f"ev-rep-{uuid.uuid4().hex[:8]}"
        evidence_list.append(
            EvidenceItem(
                id=ev_id,
                evidence_type=EvidenceType.CALCULATION,
                source="Executive Reporting Agent",
                dataset_version_id=request.dataset_version_id,
                operation="generate_report_summary",
                raw_value=report_summary,
            )
        )

        claims_list.append(
            ClaimItem(
                claim_id=f"claim-{uuid.uuid4().hex[:8]}",
                statement="Compiled structured multi-agent executive summary.",
                claim_type=ClaimType.RECOMMENDATION,
                evidence_ids=[ev_id],
            )
        )

        return AgentResponse(
            task_id=request.task_id,
            agent_id=self.agent_id,
            status="COMPLETED",
            summary="Compiled executive summary report.",
            data_payload={"report_text": report_summary},
            evidence=evidence_list,
            claims=claims_list,
            execution_time_ms=(time.perf_counter() - start_time) * 1000.0,
        )
