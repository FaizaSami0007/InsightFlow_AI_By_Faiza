import logging
import time
from datetime import datetime
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.duckdb.dataset import AnalyticalDataset
from app.analytics.duckdb.manager import duckdb_manager
from app.analytics.engine.contracts import AnalysisProvenance
from app.analytics.engine.registry import analysis_registry
from app.analytics.schemas import (
    AnalysisHistoryItem,
    AnalysisResponse,
    AnalysisRunRequest,
)
from app.core.exceptions import AppError, NotFoundError, ValidationError
from app.database.models.analytics import AnalysisJob, AnalysisJobStatus
from app.database.models.dataset import Dataset, DatasetVersion
from app.database.models.user import User
from app.datasets.storage import StorageProvider, get_storage_provider

logger = logging.getLogger(__name__)


class AnalyticsService:
    """
    Orchestrates deterministic analytics execution, dataset resolution,
    tenant authorization, and result persistence.
    """

    async def run_analysis(
        self,
        request: AnalysisRunRequest,
        current_user: User,
        db: AsyncSession,
        storage: Optional[StorageProvider] = None,
    ) -> AnalysisResponse:
        # Step 1: Verify Dataset Ownership & Version
        dataset_res = await db.execute(
            select(Dataset).where(Dataset.id == request.dataset_id, Dataset.owner_id == current_user.id)
        )
        dataset = dataset_res.scalar_one_or_none()
        if not dataset:
            raise NotFoundError("Dataset not found or access unauthorized")

        ver_res = await db.execute(
            select(DatasetVersion).where(
                DatasetVersion.id == request.dataset_version_id,
                DatasetVersion.dataset_id == dataset.id,
            )
        )
        version = ver_res.scalar_one_or_none()
        if not version:
            raise NotFoundError("Dataset version not found")

        # Step 2: Resolve storage and register in DuckDB
        storage_backend = storage or get_storage_provider()
        physical_path = str(storage_backend.get_file_path(version.storage_reference))

        view_name = duckdb_manager.register_dataset(
            dataset_version_id=version.id,
            file_path=physical_path,
            file_format=version.file_format.value,
        )
        schema_dict = duckdb_manager.get_schema(version.id)
        dataset_columns = list(schema_dict.keys())

        analytical_dataset = AnalyticalDataset(
            dataset_id=dataset.id,
            version_id=version.id,
            view_name=view_name,
            file_path=physical_path,
            file_format=version.file_format.value,
            schema=schema_dict,
            columns=dataset_columns,
        )

        # Step 3: Create initial DB Job Record
        filter_dict = request.filters.model_dump() if hasattr(request.filters, "model_dump") else request.filters
        job = AnalysisJob(
            user_id=current_user.id,
            dataset_id=dataset.id,
            dataset_version_id=version.id,
            operation=request.operation,
            parameters_json=request.parameters,
            filters_json=filter_dict,
            status=AnalysisJobStatus.RUNNING,
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)

        # Step 4: Validate and Execute Analysis Tool
        start_time = time.perf_counter()
        try:
            analysis_registry.validate(
                tool_name=request.operation,
                dataset=analytical_dataset,
                parameters=request.parameters,
                filters=request.filters,
            )

            cols, rows, summary = analysis_registry.execute(
                tool_name=request.operation,
                dataset=analytical_dataset,
                parameters=request.parameters,
                filters=request.filters,
                sort_by=request.sort_by,
                limit=request.limit or 1000,
                offset=request.offset or 0,
            )

            execution_time_ms = round((time.perf_counter() - start_time) * 1000, 2)

            provenance = AnalysisProvenance(
                dataset_id=dataset.id,
                dataset_version_id=version.id,
                operation=request.operation,
                parameters=request.parameters,
                filters=filter_dict,
                execution_time_ms=execution_time_ms,
            )

            # Update DB Job
            job.status = AnalysisJobStatus.COMPLETED
            job.execution_time_ms = execution_time_ms
            job.row_count = len(rows)
            job.summary_json = summary
            job.result_json = {"columns": cols, "rows": rows}
            job.completed_at = datetime.utcnow()
            await db.commit()

            return AnalysisResponse(
                analysis_id=job.id,
                dataset_id=dataset.id,
                dataset_version_id=version.id,
                operation=request.operation,
                status=AnalysisJobStatus.COMPLETED.value,
                columns=cols,
                rows=rows,
                summary=summary,
                execution_time_ms=execution_time_ms,
                row_count=len(rows),
                provenance=provenance,
                created_at=job.created_at,
            )

        except Exception as e:
            execution_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.error("Analysis execution failed for operation '%s': %s", request.operation, str(e), exc_info=True)
            job.status = AnalysisJobStatus.FAILED
            job.error_message = str(e)
            job.execution_time_ms = execution_time_ms
            job.completed_at = datetime.utcnow()
            await db.commit()

            if isinstance(e, ValueError):
                raise ValidationError(f"Analysis validation failed: {str(e)}")
            raise AppError(f"Analysis execution error: {str(e)}", status_code=500)

    async def get_analysis(
        self,
        analysis_id: str,
        current_user: User,
        db: AsyncSession,
    ) -> AnalysisResponse:
        res = await db.execute(
            select(AnalysisJob).where(AnalysisJob.id == analysis_id, AnalysisJob.user_id == current_user.id)
        )
        job = res.scalar_one_or_none()
        if not job:
            raise NotFoundError("Analysis record not found or access unauthorized")

        result_payload = job.result_json or {}
        columns = result_payload.get("columns", [])
        rows = result_payload.get("rows", [])

        provenance = None
        if job.status == AnalysisJobStatus.COMPLETED:
            provenance = AnalysisProvenance(
                dataset_id=job.dataset_id,
                dataset_version_id=job.dataset_version_id,
                operation=job.operation,
                parameters=job.parameters_json,
                filters=job.filters_json,
                execution_time_ms=job.execution_time_ms or 0.0,
            )

        return AnalysisResponse(
            analysis_id=job.id,
            dataset_id=job.dataset_id,
            dataset_version_id=job.dataset_version_id,
            operation=job.operation,
            status=job.status.value if hasattr(job.status, "value") else str(job.status),
            columns=columns,
            rows=rows,
            summary=job.summary_json,
            execution_time_ms=job.execution_time_ms or 0.0,
            row_count=job.row_count or 0,
            provenance=provenance,
            error_message=job.error_message,
            created_at=job.created_at,
        )

    async def list_history(
        self,
        current_user: User,
        dataset_id: Optional[str],
        db: AsyncSession,
        limit: int = 50,
    ) -> List[AnalysisHistoryItem]:
        query = select(AnalysisJob).where(AnalysisJob.user_id == current_user.id)
        if dataset_id:
            query = query.where(AnalysisJob.dataset_id == dataset_id)
        query = query.order_by(AnalysisJob.created_at.desc()).limit(limit)

        res = await db.execute(query)
        jobs = res.scalars().all()

        return [
            AnalysisHistoryItem(
                id=j.id,
                dataset_id=j.dataset_id,
                dataset_version_id=j.dataset_version_id,
                operation=j.operation,
                status=j.status.value if hasattr(j.status, "value") else str(j.status),
                execution_time_ms=j.execution_time_ms,
                row_count=j.row_count,
                created_at=j.created_at,
                error_message=j.error_message,
            )
            for j in jobs
        ]


analytics_service = AnalyticsService()
