import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.analytics.duckdb.manager import DuckDBManager
from app.database.models.dataset import DatasetVersion
from app.database.models.profiling import (
    ColumnProfile,
    ConceptualType,
    DataQualityReport,
    DatasetProfile,
    ProfileStatus,
    SemanticColumn,
    SemanticRole,
)
from app.datasets.storage import StorageProvider
from app.profiling.engine.profiler import ProfilingEngine
from app.profiling.quality.quality_engine import DataQualityEngine
from app.profiling.readers.factory import get_data_reader
from app.profiling.schemas import (
    AnalyticalQueryRequest,
    AnalyticalQueryResponse,
    SemanticOverrideRequest,
)

logger = logging.getLogger("insightflow.profiling.service")


class ProfilingService:
    """Orchestrates deterministic dataset profiling, quality evaluation, semantic discovery, and DuckDB analytics."""

    def __init__(
        self,
        profiling_engine: Optional[ProfilingEngine] = None,
        quality_engine: Optional[DataQualityEngine] = None,
        duckdb_manager: Optional[DuckDBManager] = None,
    ):
        self.profiler = profiling_engine or ProfilingEngine()
        self.quality = quality_engine or DataQualityEngine()
        self.duckdb = duckdb_manager or DuckDBManager.get_instance()

    async def get_profile(self, db: AsyncSession, version_id: str) -> Optional[DatasetProfile]:
        """Fetch profile with full column, quality, and semantic relationships."""
        stmt = (
            select(DatasetProfile)
            .where(DatasetProfile.dataset_version_id == version_id)
            .options(
                selectinload(DatasetProfile.column_profiles),
                selectinload(DatasetProfile.quality_report),
                selectinload(DatasetProfile.semantic_columns),
            )
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def profile_version(
        self,
        db: AsyncSession,
        dataset_version: DatasetVersion,
        storage: StorageProvider,
        force_refresh: bool = False,
    ) -> DatasetProfile:
        """Deterministically profile an immutable dataset version and persist results in PostgreSQL."""
        existing_profile = await self.get_profile(db, dataset_version.id)
        if existing_profile and existing_profile.status == ProfileStatus.COMPLETED and not force_refresh:
            logger.info(f"Returning cached profile for dataset version {dataset_version.id}")
            return existing_profile

        # Clear existing profile records if force_refresh
        if existing_profile:
            await db.delete(existing_profile)
            await db.flush()

        profile = DatasetProfile(
            dataset_version_id=dataset_version.id,
            status=ProfileStatus.RUNNING,
        )
        db.add(profile)
        await db.flush()

        try:
            file_path = storage.get_file_path(dataset_version.storage_reference)
            reader = get_data_reader(dataset_version.file_format)
            df = reader.read_dataframe(file_path)

            if df.is_empty():
                raise ValueError("Dataset is empty or contains no records to profile.")

            # 1. Profile dataset & columns
            profile_meta = self.profiler.profile_dataframe(df)

            # 2. Evaluate Data Quality
            quality_meta = self.quality.evaluate_quality(
                row_count=profile_meta["row_count"],
                column_count=profile_meta["column_count"],
                duplicate_rows=profile_meta["duplicate_rows"],
                duplicate_percentage=profile_meta["duplicate_percentage"],
                columns_profile=profile_meta["columns"],
            )

            # 3. Infer Semantics
            from app.profiling.semantics.semantic_classifier import SemanticClassifier

            semantic_classifier = SemanticClassifier()
            semantic_meta = semantic_classifier.classify_all(
                profile_meta["columns"],
                profile_meta["row_count"],
            )

            # Update Profile record
            profile.status = ProfileStatus.COMPLETED
            profile.row_count = profile_meta["row_count"]
            profile.column_count = profile_meta["column_count"]
            profile.memory_size_bytes = profile_meta["memory_size_bytes"]
            profile.duration_ms = profile_meta["duration_ms"]
            profile.error_message = None

            # Persist Column Profiles
            for col in profile_meta["columns"]:
                c_prof = ColumnProfile(
                    profile_id=profile.id,
                    column_name=col["column_name"],
                    normalized_name=col["normalized_name"],
                    ordinal_position=col["ordinal_position"],
                    data_type=col["data_type"],
                    conceptual_type=ConceptualType(col["conceptual_type"]),
                    null_count=col["null_count"],
                    null_percentage=col["null_percentage"],
                    unique_count=col["unique_count"],
                    unique_percentage=col["unique_percentage"],
                    is_constant=col["is_constant"],
                    is_near_constant=col["is_near_constant"],
                    numeric_stats=col["numeric_stats"],
                    categorical_stats=col["categorical_stats"],
                    temporal_stats=col["temporal_stats"],
                    boolean_stats=col["boolean_stats"],
                    outlier_count=col["outlier_count"],
                    outlier_percentage=col["outlier_percentage"],
                )
                db.add(c_prof)

            # Persist Data Quality Report
            q_rep = DataQualityReport(
                profile_id=profile.id,
                overall_score=quality_meta["overall_score"],
                grade=quality_meta["grade"],
                total_issues=quality_meta["total_issues"],
                missing_summary=quality_meta["missing_summary"],
                duplicate_summary=quality_meta["duplicate_summary"],
                constant_columns=quality_meta["constant_columns"],
                outlier_summary=quality_meta["outlier_summary"],
                warnings=quality_meta["warnings"],
            )
            db.add(q_rep)

            # Persist Semantic Columns
            for sem in semantic_meta:
                s_col = SemanticColumn(
                    profile_id=profile.id,
                    column_name=sem["column_name"],
                    inferred_role=SemanticRole(sem["inferred_role"]),
                    inferred_confidence=sem["inferred_confidence"],
                    user_role=None,
                    is_dimension=sem["is_dimension"],
                    is_measure=sem["is_measure"],
                    is_identifier=sem["is_identifier"],
                    is_temporal=sem["is_temporal"],
                    possible_currency=sem["possible_currency"],
                    description=sem["description"],
                    unit=sem["unit"],
                    format_hint=sem["format_hint"],
                )
                db.add(s_col)

            # Update DatasetVersion counts
            dataset_version.row_count = profile_meta["row_count"]
            dataset_version.column_count = profile_meta["column_count"]

            await db.commit()
            return await self.get_profile(db, dataset_version.id)  # type: ignore

        except Exception as e:
            logger.error(f"Profiling failed for dataset version {dataset_version.id}: {str(e)}", exc_info=True)
            profile.status = ProfileStatus.FAILED
            profile.error_message = str(e)
            await db.commit()
            return profile

    async def update_semantic_override(
        self,
        db: AsyncSession,
        version_id: str,
        column_name: str,
        override: SemanticOverrideRequest,
    ) -> SemanticColumn:
        """Allow human users to override inferred semantic roles and descriptions."""
        profile = await self.get_profile(db, version_id)
        if not profile:
            raise ValueError(f"Profile not found for dataset version '{version_id}'.")

        stmt = select(SemanticColumn).where(
            SemanticColumn.profile_id == profile.id,
            SemanticColumn.column_name == column_name,
        )
        res = await db.execute(stmt)
        sem_col = res.scalar_one_or_none()
        if not sem_col:
            raise ValueError(f"Column '{column_name}' not found in semantic schema.")

        if override.user_role is not None:
            sem_col.user_role = override.user_role
            # Sync flags
            sem_col.is_dimension = override.user_role == SemanticRole.DIMENSION
            sem_col.is_measure = override.user_role == SemanticRole.MEASURE
            sem_col.is_identifier = override.user_role == SemanticRole.IDENTIFIER
            sem_col.is_temporal = override.user_role in (SemanticRole.DATE, SemanticRole.DATETIME)

        if override.description is not None:
            sem_col.description = override.description
        if override.unit is not None:
            sem_col.unit = override.unit
        if override.format_hint is not None:
            sem_col.format_hint = override.format_hint

        await db.commit()
        await db.refresh(sem_col)
        return sem_col

    def execute_analytical_query(
        self,
        dataset_version: DatasetVersion,
        storage: StorageProvider,
        request: AnalyticalQueryRequest,
    ) -> AnalyticalQueryResponse:
        """Register and execute a safe read-only SQL query in DuckDB."""
        file_path = storage.get_file_path(dataset_version.storage_reference)
        if not self.duckdb.is_registered(dataset_version.id):
            self.duckdb.register_dataset(dataset_version.id, file_path, dataset_version.file_format.value)

        result = self.duckdb.execute_query(
            dataset_version_id=dataset_version.id,
            sql_query=request.query,
            parameters=request.parameters,
            max_rows=request.max_rows,
        )

        return AnalyticalQueryResponse(
            columns=result["columns"],
            rows=result["rows"],
            row_count=result["row_count"],
            execution_time_ms=result["execution_time_ms"],
            metadata=result["metadata"],
        )
