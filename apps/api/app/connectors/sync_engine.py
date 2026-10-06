"""Data Synchronization & Dataset Ingestion Engine for Phase 17 Connectors."""

import io
from datetime import datetime, timezone
from typing import Any, Optional

import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession

from app.connectors.registry import ConnectorRegistry
from app.connectors.schemas import SyncTriggerRequest
from app.connectors.secrets import SecretProvider
from app.database.models.connectors import (
    ConnectionHealthStatus,
    DataConnection,
    DataConnectionAuditLog,
    DataConnectionSyncJob,
    SyncJobStatus,
    SyncType,
)
from app.database.models.user import User
from app.datasets.service import create_dataset_version, create_dataset_with_file
from app.profiling.service import ProfilingService


class SyncEngine:
    """Executes connector synchronization jobs, persists physical dataset versions, and triggers profiling."""

    def __init__(self, db: AsyncSession, secret_provider: Optional[SecretProvider] = None):
        self.db = db
        self.secrets = secret_provider or SecretProvider()
        self.profiling_service = ProfilingService()

    async def execute_sync_job(
        self,
        connection: DataConnection,
        user: User,
        request: SyncTriggerRequest,
    ) -> DataConnectionSyncJob:
        """Runs end-to-end sync: extraction, validation, dataset versioning, DuckDB profiling, and lineage recording."""
        now = datetime.now(timezone.utc)

        # 1. Create SyncJob in QUEUED/RUNNING state
        sync_job = DataConnectionSyncJob(
            connection_id=connection.id,
            dataset_id=request.target_dataset_id,
            source_resource=request.source_resource,
            sync_type=request.sync_type,
            status=SyncJobStatus.RUNNING,
            started_at=now,
            rows_processed=0,
            rows_added=0,
            rows_updated=0,
            rows_rejected=0,
            sync_metadata={},
        )
        self.db.add(sync_job)
        await self.db.flush()

        try:
            # 2. Instantiate Connector
            credentials = self.secrets.decrypt_credentials(connection.encrypted_credentials)
            connector = ConnectorRegistry.get_connector(
                connection.connector_type,
                connection.configuration,
                credentials,
            )

            # 3. Extract Records from External Source
            cursor_val = None
            if request.sync_type == SyncType.INCREMENTAL_SYNC:
                cursor_val = connection.health_details.get("last_cursor_value")

            records, metadata = await connector.ingest(
                resource_id=request.source_resource,
                sync_type=request.sync_type,
                cursor_value=cursor_val,
                column_selection=request.column_selection,
                row_limit=request.row_limit,
            )

            if not records:
                # 0 rows extracted (e.g. up-to-date incremental sync)
                sync_job.status = SyncJobStatus.COMPLETED
                sync_job.completed_at = datetime.now(timezone.utc)
                sync_job.rows_processed = 0
                sync_job.sync_metadata = metadata
                await self.db.commit()
                return sync_job

            # 4. Convert to CSV/Parquet Bytes
            df = pd.DataFrame(records)
            csv_buffer = io.BytesIO()
            df.to_csv(csv_buffer, index=False, encoding="utf-8")
            file_bytes = csv_buffer.getvalue()
            filename = f"{request.source_resource.replace('/', '_')}_sync.csv"

            # 5. Create or Update Dataset & Version
            if request.target_dataset_id:
                # Append as new version
                dataset_version = await create_dataset_version(
                    session=self.db,
                    user=user,
                    dataset_id=request.target_dataset_id,
                    file_bytes=file_bytes,
                    original_filename=filename,
                )
                target_dataset_id = request.target_dataset_id
            else:
                # Create brand new Dataset
                ds_name = request.dataset_name or f"{connection.name} - {request.source_resource}"
                dataset = await create_dataset_with_file(
                    session=self.db,
                    user=user,
                    file_bytes=file_bytes,
                    original_filename=filename,
                    name=ds_name,
                    description=f"Synchronized from {connection.name} ({connection.connector_type.value}) table '{request.source_resource}'.",
                )
                target_dataset_id = dataset.id
                dataset_version = dataset.versions[0] if dataset.versions else None

            # 6. Update Sync Job details
            sync_job.dataset_id = target_dataset_id
            if dataset_version:
                sync_job.dataset_version_id = dataset_version.id

            sync_job.rows_processed = len(records)
            sync_job.rows_added = len(records)
            sync_job.status = SyncJobStatus.COMPLETED
            sync_job.completed_at = datetime.now(timezone.utc)
            sync_job.sync_metadata = {
                **metadata,
                "dataset_id": target_dataset_id,
                "dataset_version_id": dataset_version.id if dataset_version else None,
                "columns": list(df.columns),
            }

            # 7. Update Connection state
            connection.last_sync_at = datetime.now(timezone.utc)
            connection.health_status = ConnectionHealthStatus.HEALTHY
            connection.health_details = {
                "last_sync_status": "SUCCESS",
                "last_rows_synced": len(records),
                "last_cursor_value": metadata.get("next_cursor_value"),
            }

            # 8. Trigger Profiling & Quality Engine
            if dataset_version:
                try:
                    await self.profiling_service.profile_version(self.db, dataset_version.id)
                except Exception as prof_err:
                    # Non-fatal to ingestion; logged in metadata
                    sync_job.sync_metadata["profiling_error"] = str(prof_err)

            # 9. Record Audit Log
            audit = DataConnectionAuditLog(
                connection_id=connection.id,
                user_id=user.id,
                action="SYNC_COMPLETED",
                status="SUCCESS",
                details={
                    "sync_job_id": sync_job.id,
                    "rows_synced": len(records),
                    "resource": request.source_resource,
                },
            )
            self.db.add(audit)

            await self.db.commit()
            return sync_job

        except Exception as e:
            await self.db.rollback()
            sync_job.status = SyncJobStatus.FAILED
            sync_job.completed_at = datetime.now(timezone.utc)
            sync_job.error = str(e)

            connection.health_status = ConnectionHealthStatus.ERROR
            connection.health_details = {"last_error": str(e)}

            audit = DataConnectionAuditLog(
                connection_id=connection.id,
                user_id=user.id,
                action="SYNC_FAILED",
                status="FAILED",
                details={"error": str(e), "resource": request.source_resource},
            )
            self.db.add(audit)
            await self.db.commit()
            return sync_job

    @classmethod
    async def execute_sync(
        cls,
        db: AsyncSession,
        connection: DataConnection,
        source_resource: str,
        user_id: Any,
        sync_type: SyncType = SyncType.FULL_SYNC,
        target_dataset_name: Optional[str] = None,
        secret_provider: Optional[SecretProvider] = None,
    ) -> DataConnectionSyncJob:
        """Convenience classmethod for executing a synchronization job."""
        engine = cls(db, secret_provider)
        req = SyncTriggerRequest(
            source_resource=source_resource,
            sync_type=sync_type,
            dataset_name=target_dataset_name,
        )
        fake_user = type("UserShim", (), {"id": str(user_id) if hasattr(user_id, "id") is False else str(user_id.id)})()
        return await engine.execute_sync_job(connection, fake_user, req)
