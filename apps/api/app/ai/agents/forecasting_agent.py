"""Forecasting Agent executing time-series preprocessing, model selection, and backtesting."""

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
from app.database.models.forecasting import ForecastModelType
from app.forecasting.schemas import ForecastRunRequest
from app.forecasting.service import ForecastService


class ForecastingAgent(BaseAgent):
    """Specialized agent for generating statistical predictive forecasts and uncertainty intervals."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(AgentID.FORECASTING_AGENT, db)
        self.service = ForecastService(db)

    async def execute(self, request: AgentRequest) -> AgentResponse:
        start_time = time.perf_counter()
        evidence_list: List[EvidenceItem] = []
        claims_list: List[ClaimItem] = []

        params = request.context.get("parameters") or {}
        target_field = params.get("target_field") or "revenue"
        time_field = params.get("time_field") or "order_date"
        horizon = params.get("forecast_horizon", 6)
        confidence_level = params.get("confidence_level", 0.95)

        if not self.is_tool_allowed("run_time_series_forecast"):
            return AgentResponse(
                task_id=request.task_id,
                agent_id=self.agent_id,
                status="FAILED",
                summary="Tool 'run_time_series_forecast' is not permitted.",
                error_message="Unauthorized tool execution",
                execution_time_ms=(time.perf_counter() - start_time) * 1000.0,
            )

        try:
            fc_req = ForecastRunRequest(
                dataset_id=request.dataset_id,
                dataset_version_id=request.dataset_version_id,
                target_field=target_field,
                time_field=time_field,
                forecast_horizon=horizon,
                confidence_level=confidence_level,
                model_type=ForecastModelType.AUTO,
            )
            result = await self.service.run_forecast(fc_req, request.user_id)

            ev_id = f"ev-fc-{uuid.uuid4().hex[:8]}"
            evidence_list.append(
                EvidenceItem(
                    id=ev_id,
                    evidence_type=EvidenceType.FORECAST,
                    source=f"Forecast Model ({result.selected_model_name})",
                    dataset_version_id=request.dataset_version_id,
                    operation="run_time_series_forecast",
                    raw_value={
                        "model": result.selected_model_name,
                        "predictions": [p.model_dump() for p in result.predictions],
                        "metrics": result.metrics.model_dump(),
                    },
                    confidence=confidence_level,
                    provenance=result.provenance,
                )
            )

            claims_list.append(
                ClaimItem(
                    claim_id=f"claim-{uuid.uuid4().hex[:8]}",
                    statement=f"Generated {horizon}-step forecast using {result.selected_model_name} with MAPE of {result.metrics.mape:.2f}%.",
                    claim_type=ClaimType.FORECAST,
                    evidence_ids=[ev_id],
                )
            )

            summary_text = f"Projected {target_field} for {horizon} periods ahead using {result.selected_model_name}."

            return AgentResponse(
                task_id=request.task_id,
                agent_id=self.agent_id,
                status="COMPLETED",
                summary=summary_text,
                data_payload={
                    "forecast_id": result.id,
                    "selected_model": result.selected_model_name,
                    "predictions": [p.model_dump() for p in result.predictions],
                    "metrics": result.metrics.model_dump(),
                },
                evidence=evidence_list,
                claims=claims_list,
                tool_calls_executed=[{"tool": "run_time_series_forecast", "params": params}],
                execution_time_ms=(time.perf_counter() - start_time) * 1000.0,
            )
        except Exception as ex:
            return AgentResponse(
                task_id=request.task_id,
                agent_id=self.agent_id,
                status="FAILED",
                summary="Forecasting failed",
                error_message=str(ex),
                execution_time_ms=(time.perf_counter() - start_time) * 1000.0,
            )
