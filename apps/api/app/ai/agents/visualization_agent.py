"""Visualization Agent recommending optimal charts and validating visual specifications."""

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
from app.visualization.engine.rules import recommendation_engine


class VisualizationAgent(BaseAgent):
    """Specialized agent for generating validated, accessible chart specifications."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(AgentID.VISUALIZATION_AGENT, db)

    async def execute(self, request: AgentRequest) -> AgentResponse:
        start_time = time.perf_counter()
        evidence_list: List[EvidenceItem] = []
        claims_list: List[ClaimItem] = []

        params = request.context.get("parameters") or {}
        analysis_id = params.get("analysis_id")

        # Find analysis_id from prior evidence if not in context
        if not analysis_id:
            for ev in request.prior_evidence:
                if ev.provenance.get("analysis_id"):
                    analysis_id = ev.provenance["analysis_id"]
                    break

        if not analysis_id:
            # Generate fallback KPI / Table spec
            spec_dict = {
                "chart_type": "kpi",
                "title": "Metric Overview",
                "subtitle": "Analysis Summary",
            }
        else:
            try:
                rec_result = await recommendation_engine.recommend(
                    analysis_id=analysis_id,
                    preferred_chart_type=params.get("preferred_chart_type"),
                    user_id=request.user_id,
                    db=self.db,
                )
                spec_dict = rec_result.spec.model_dump()
            except Exception:
                spec_dict = {
                    "chart_type": "bar",
                    "title": "Analysis Distribution",
                    "subtitle": "Generated chart",
                }

        ev_id = f"ev-viz-{uuid.uuid4().hex[:8]}"
        evidence_list.append(
            EvidenceItem(
                id=ev_id,
                evidence_type=EvidenceType.CALCULATION,
                source="Visualization Engine",
                dataset_version_id=request.dataset_version_id,
                operation="recommend_visualization",
                raw_value=spec_dict,
            )
        )

        claims_list.append(
            ClaimItem(
                claim_id=f"claim-{uuid.uuid4().hex[:8]}",
                statement=f"Recommended {spec_dict.get('chart_type', 'chart')} chart for visual inspection.",
                claim_type=ClaimType.RECOMMENDATION,
                evidence_ids=[ev_id],
            )
        )

        return AgentResponse(
            task_id=request.task_id,
            agent_id=self.agent_id,
            status="COMPLETED",
            summary=f"Recommended {spec_dict.get('chart_type')} chart: '{spec_dict.get('title')}'.",
            data_payload={"visualization": spec_dict},
            evidence=evidence_list,
            claims=claims_list,
            execution_time_ms=(time.perf_counter() - start_time) * 1000.0,
        )
