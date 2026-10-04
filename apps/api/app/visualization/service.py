"""Visualization Service coordinating analysis result resolution, recommendation, and validation."""

import logging
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.database.models.analytics import AnalysisJob
from app.database.models.user import User
from app.visualization.engine.registry import chart_registry
from app.visualization.engine.rules import recommendation_engine
from app.visualization.engine.validator import chart_validator
from app.visualization.schemas import (
    ChartTypeMetadata,
    VisualizationRecommendRequest,
    VisualizationSpec,
    VisualizationValidateRequest,
    VisualizationValidationResult,
)

logger = logging.getLogger(__name__)


class VisualizationService:
    """Service providing safe, validated visualization specifications for analytical results."""

    async def get_chart_types(self) -> List[ChartTypeMetadata]:
        """Returns metadata and constraints for all registered chart types."""
        return chart_registry.list_all()

    async def recommend_visualization(
        self,
        request: VisualizationRecommendRequest,
        current_user: User,
        db: AsyncSession,
    ) -> VisualizationSpec:
        """Generates a context-aware, validated visualization specification for an analysis job."""
        # 1. Fetch Analysis Job & Verify Ownership
        stmt = select(AnalysisJob).where(
            AnalysisJob.id == request.analysis_id,
            AnalysisJob.user_id == current_user.id,
        )
        res = await db.execute(stmt)
        job = res.scalar_one_or_none()
        if not job:
            raise NotFoundError("Analysis record not found or access unauthorized.")

        result_payload = job.result_json or {}
        columns = result_payload.get("columns", [])
        rows = result_payload.get("rows", [])
        summary = job.summary_json or {}
        parameters = job.parameters_json or {}
        filters = job.filters_json or {}

        # 2. Run Recommendation Engine
        spec = recommendation_engine.recommend(
            operation=job.operation,
            columns=columns,
            rows=rows,
            summary=summary,
            parameters=parameters,
            filters=filters,
            dataset_id=job.dataset_id,
            dataset_version_id=job.dataset_version_id,
            analysis_id=job.id,
            preferred_chart_type=request.preferred_chart_type,
        )

        return spec

    async def validate_visualization(
        self,
        request: VisualizationValidateRequest,
        current_user: User,
        db: AsyncSession,
    ) -> VisualizationValidationResult:
        """Validates a candidate visualization specification against the actual analysis result."""
        stmt = select(AnalysisJob).where(
            AnalysisJob.id == request.analysis_id,
            AnalysisJob.user_id == current_user.id,
        )
        res = await db.execute(stmt)
        job = res.scalar_one_or_none()
        if not job:
            raise NotFoundError("Analysis record not found or access unauthorized.")

        result_payload = job.result_json or {}
        columns = result_payload.get("columns", [])
        rows = result_payload.get("rows", [])
        summary = job.summary_json or {}

        validation = chart_validator.validate(
            spec=request.spec,
            operation=job.operation,
            columns=columns,
            rows=rows,
            summary=summary,
            dataset_id=job.dataset_id,
            dataset_version_id=job.dataset_version_id,
            analysis_id=job.id,
        )

        return validation


visualization_service = VisualizationService()
