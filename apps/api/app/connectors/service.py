"""Service layer orchestrating Phase 17 Enterprise Data Connectors."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.connectors.drift_engine import ConnectorDriftEngine, FreshnessEngine
from app.connectors.registry import ConnectorRegistry
from app.connectors.schemas import (
    ConnectionCreateRequest,
    ConnectionTestRequest,
    ConnectionTestResult,
    ConnectionUpdateRequest,
    ResourcePreviewRequest,
    ResourcePreviewResponse,
    SchemaDiscoveryResponse,
    SyncTriggerRequest,
)
from app.connectors.secrets import SecretProvider
from app.connectors.sync_engine import SyncEngine
from app.database.models.connectors import (
    ConnectionHealthStatus,
    ConnectionStatus,
    ConnectorType,
    DataConnection,
    DataConnectionAuditLog,
    DataConnectionSchemaSnapshot,
    DataConnectionSyncJob,
)
from app.database.models.user import User


class ConnectorServiceError(Exception):
    """Base exception for connector service failures."""

    pass


class ConnectionNotFoundError(ConnectorServiceError):
    """Raised when a requested connection does not exist."""

    pass


class UnauthorizedConnectionAccessError(ConnectorServiceError):
    """Raised when a user attempts cross-tenant access to another user's connection."""

    pass


class ConnectorService:
    """Core domain service managing enterprise data connections, schema discovery, sync jobs, and security."""

    def __init__(self, db: AsyncSession, secret_provider: Optional[SecretProvider] = None):
        self.db = db
        self.secrets = secret_provider or SecretProvider()
        self.sync_engine = SyncEngine(db, self.secrets)

    async def create_connection(self, user: User, request: ConnectionCreateRequest) -> DataConnection:
        """Registers a new external data connection with securely encrypted credentials."""
        encrypted_creds = None
        if request.credentials:
            encrypted_creds = self.secrets.encrypt_credentials(request.credentials)

        conn = DataConnection(
            user_id=user.id,
            workspace_id=request.workspace_id,
            name=request.name.strip(),
            description=request.description.strip() if request.description else None,
            connector_type=request.connector_type,
            status=ConnectionStatus.CONFIGURED,
            configuration=request.configuration,
            encrypted_credentials=encrypted_creds,
            credential_reference=f"vault-ref-{user.id[:8]}",
            health_status=ConnectionHealthStatus.UNKNOWN,
            health_details={},
            sync_schedule=request.sync_schedule,
            is_active=True,
        )
        self.db.add(conn)
        await self.db.flush()

        audit = DataConnectionAuditLog(
            connection_id=conn.id,
            user_id=user.id,
            action="CONNECTION_CREATED",
            status="SUCCESS",
            details={"connector_type": request.connector_type.value, "name": request.name},
        )
        self.db.add(audit)
        await self.db.commit()
        await self.db.refresh(conn)
        return conn

    async def list_connections(
        self,
        user: User,
        connector_type: Optional[ConnectorType] = None,
        is_active: Optional[bool] = None,
    ) -> List[DataConnection]:
        """Lists data connections owned by the user or workspace."""
        stmt = (
            select(DataConnection)
            .where(DataConnection.user_id == user.id)
            .options(
                selectinload(DataConnection.sync_jobs),
                selectinload(DataConnection.schema_snapshots),
            )
            .order_by(DataConnection.created_at.desc())
        )
        if connector_type:
            stmt = stmt.where(DataConnection.connector_type == connector_type)
        if is_active is not None:
            stmt = stmt.where(DataConnection.is_active == is_active)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    def _extract_user_id(self, user: Any) -> str:
        if isinstance(user, str):
            return user
        if hasattr(user, "id"):
            return str(user.id)
        return str(user)

    async def get_connection(self, connection_id: str, user: Any) -> DataConnection:
        """Retrieves a specific connection with IDOR ownership validation."""
        stmt = (
            select(DataConnection)
            .where(DataConnection.id == connection_id)
            .options(
                selectinload(DataConnection.sync_jobs),
                selectinload(DataConnection.schema_snapshots),
                selectinload(DataConnection.audit_logs),
            )
        )
        result = await self.db.execute(stmt)
        conn = result.scalar_one_or_none()
        if not conn:
            raise ConnectionNotFoundError(f"Connection '{connection_id}' not found.")
        user_id = self._extract_user_id(user)
        if str(conn.user_id) != user_id:
            raise ConnectionNotFoundError(f"Connection '{connection_id}' not found.")
        return conn

    async def update_connection(
        self,
        connection_id: str,
        user: User,
        request: ConnectionUpdateRequest,
    ) -> DataConnection:
        """Updates connection metadata, configuration, or credentials."""
        conn = await self.get_connection(connection_id, user)

        if request.name is not None:
            conn.name = request.name.strip()
        if request.description is not None:
            conn.description = request.description.strip()
        if request.configuration is not None:
            conn.configuration = request.configuration
        if request.credentials is not None:
            conn.encrypted_credentials = self.secrets.encrypt_credentials(request.credentials)
        if request.sync_schedule is not None:
            conn.sync_schedule = request.sync_schedule
        if request.is_active is not None:
            conn.is_active = request.is_active

        audit = DataConnectionAuditLog(
            connection_id=conn.id,
            user_id=user.id,
            action="CONNECTION_UPDATED",
            status="SUCCESS",
            details={
                "updated_fields": [k for k, v in request.model_dump(exclude_unset=True).items() if k != "credentials"]
            },
        )
        self.db.add(audit)
        await self.db.commit()
        await self.db.refresh(conn)
        return conn

    async def delete_connection(self, connection_id: str, user: User) -> None:
        """Deletes a connection and associated sync jobs/snapshots."""
        conn = await self.get_connection(connection_id, user)
        await self.db.delete(conn)
        await self.db.commit()

    async def test_connection(self, connection_id: str, user: User) -> ConnectionTestResult:
        """Executes connection validation against an existing registered connection."""
        conn = await self.get_connection(connection_id, user)
        credentials = self.secrets.decrypt_credentials(conn.encrypted_credentials)

        connector = ConnectorRegistry.get_connector(conn.connector_type, conn.configuration, credentials)
        test_res = await connector.validate_connection()

        # Update connection health state
        conn.last_tested_at = datetime.now(timezone.utc)
        if test_res.success:
            conn.status = ConnectionStatus.ACTIVE
            conn.health_status = ConnectionHealthStatus.HEALTHY
            conn.health_details = {"last_test_message": test_res.message, "latency_ms": test_res.latency_ms}
        else:
            conn.status = ConnectionStatus.FAILED
            conn.health_status = ConnectionHealthStatus.ERROR
            conn.health_details = {"last_test_error": test_res.message, "status": test_res.status}

        audit = DataConnectionAuditLog(
            connection_id=conn.id,
            user_id=user.id,
            action="CONNECTION_TESTED",
            status="SUCCESS" if test_res.success else "FAILED",
            details={"status": test_res.status, "message": test_res.message},
        )
        self.db.add(audit)
        await self.db.commit()
        return test_res

    async def test_connection_adhoc(self, user: User, request: ConnectionTestRequest) -> ConnectionTestResult:
        """Tests connection parameters before formal registration."""
        if not request.connector_type:
            raise ConnectorServiceError("Missing connector_type in ad-hoc test request.")
        connector = ConnectorRegistry.get_connector(
            request.connector_type,
            request.configuration or {},
            request.credentials or {},
        )
        return await connector.validate_connection()

    async def discover_schema(self, connection_id: str, user: User) -> SchemaDiscoveryResponse:
        """Discovers tables, columns, and data types, tracking schema drift against historical snapshots."""
        conn = await self.get_connection(connection_id, user)
        credentials = self.secrets.decrypt_credentials(conn.encrypted_credentials)

        connector = ConnectorRegistry.get_connector(conn.connector_type, conn.configuration, credentials)
        resources = await connector.discover_schema()

        # Record schema snapshot & drift check
        for r in resources:
            snap_stmt = (
                select(DataConnectionSchemaSnapshot)
                .where(
                    DataConnectionSchemaSnapshot.connection_id == conn.id,
                    DataConnectionSchemaSnapshot.source_resource == r.resource_id,
                )
                .order_by(DataConnectionSchemaSnapshot.created_at.desc())
            )
            snap_res = await self.db.execute(snap_stmt)
            prev_snap = snap_res.scalars().first()

            prev_def = prev_snap.schema_definition if prev_snap else {}
            drift_report = ConnectorDriftEngine.compare_schemas(prev_def, r)

            snapshot = DataConnectionSchemaSnapshot(
                connection_id=conn.id,
                source_resource=r.resource_id,
                schema_definition=r.model_dump(),
                detected_drift=drift_report.model_dump() if drift_report.has_drift else None,
            )
            self.db.add(snapshot)

        await self.db.commit()
        return SchemaDiscoveryResponse(
            connection_id=conn.id,
            resources=resources,
        )

    async def preview_resource(
        self,
        connection_id: str,
        user: User,
        request: ResourcePreviewRequest,
    ) -> ResourcePreviewResponse:
        """Fetches lightweight data preview for a table/endpoint without downloading entire dataset."""
        conn = await self.get_connection(connection_id, user)
        credentials = self.secrets.decrypt_credentials(conn.encrypted_credentials)

        connector = ConnectorRegistry.get_connector(conn.connector_type, conn.configuration, credentials)
        return await connector.preview(
            resource_id=request.resource_id,
            limit=request.row_limit,
            query_filter=request.query_filter,
        )

    async def trigger_sync(
        self,
        connection_id: str,
        user: User,
        request: SyncTriggerRequest,
    ) -> DataConnectionSyncJob:
        """Triggers an ingestion sync job from external resource into an immutable dataset version."""
        conn = await self.get_connection(connection_id, user)
        return await self.sync_engine.execute_sync_job(conn, user, request)

    async def list_sync_jobs(self, connection_id: str, user: User) -> List[DataConnectionSyncJob]:
        """Lists sync job history for a connection."""
        conn = await self.get_connection(connection_id, user)
        stmt = (
            select(DataConnectionSyncJob)
            .where(DataConnectionSyncJob.connection_id == conn.id)
            .order_by(DataConnectionSyncJob.created_at.desc())
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def get_connection_health(self, connection_id: str, user: User) -> Dict[str, Any]:
        """Computes multi-dimensional connection health, freshness status, and recommendations."""
        conn = await self.get_connection(connection_id, user)
        freshness = FreshnessEngine.calculate_freshness(conn.last_sync_at, conn.sync_schedule)

        # Retrieve latest schema drift
        snap_stmt = (
            select(DataConnectionSchemaSnapshot)
            .where(DataConnectionSchemaSnapshot.connection_id == conn.id)
            .order_by(DataConnectionSchemaSnapshot.created_at.desc())
        )
        snap_res = await self.db.execute(snap_stmt)
        latest_snap = snap_res.scalars().first()
        drift_data = latest_snap.detected_drift if (latest_snap and latest_snap.detected_drift) else {}

        recommendations = []
        if conn.health_status == ConnectionHealthStatus.ERROR:
            recommendations.append("Connection has failed. Run connection test to diagnose network or auth errors.")
        if freshness.get("is_stale"):
            recommendations.append(
                f"Data is stale ({freshness.get('hours_since_sync')}h elapsed). Trigger a synchronization job."
            )
        if drift_data.get("has_drift"):
            recommendations.append("Schema drift detected on external resource. Review schema differences.")
        if not recommendations:
            recommendations.append("Connection is healthy and synchronized within scheduled parameters.")

        return {
            "connection_id": conn.id,
            "health_status": conn.health_status.value,
            "health_score": 95.0
            if conn.health_status == ConnectionHealthStatus.HEALTHY
            else (60.0 if conn.health_status == ConnectionHealthStatus.WARNING else 25.0),
            "last_successful_sync": conn.last_sync_at,
            "freshness": freshness,
            "drift_status": drift_data or {"has_drift": False, "severity": "NONE"},
            "recommendations": recommendations,
        }

    async def get_connection_drift(self, connection_id: str, user: User) -> Dict[str, Any]:
        """Retrieves latest schema drift report for a connection."""
        conn = await self.get_connection(connection_id, user)
        snap_stmt = (
            select(DataConnectionSchemaSnapshot)
            .where(DataConnectionSchemaSnapshot.connection_id == conn.id)
            .order_by(DataConnectionSchemaSnapshot.created_at.desc())
        )
        snap_res = await self.db.execute(snap_stmt)
        latest_snap = snap_res.scalars().first()
        drift = (
            latest_snap.detected_drift
            if (latest_snap and latest_snap.detected_drift)
            else {"has_drift": False, "severity": "NONE", "recommendation": "NO_ACTION"}
        )
        return {
            "connection_id": conn.id,
            "drift_report": drift,
            "last_checked_at": latest_snap.created_at if latest_snap else None,
        }
