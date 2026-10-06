"""FastAPI REST API router for Phase 17 Enterprise Data Connectors & Ingestion."""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.connectors.registry import ConnectorRegistry
from app.connectors.schemas import (
    ConnectionCreateRequest,
    ConnectionListResponse,
    ConnectionResponse,
    ConnectionTestRequest,
    ConnectionTestResult,
    ConnectionUpdateRequest,
    ConnectorCatalogResponse,
    ResourcePreviewRequest,
    ResourcePreviewResponse,
    SchemaDiscoveryResponse,
    SyncJobListResponse,
    SyncJobResponse,
    SyncTriggerRequest,
)
from app.connectors.service import (
    ConnectionNotFoundError,
    ConnectorService,
    ConnectorServiceError,
    UnauthorizedConnectionAccessError,
)
from app.database.models.connectors import ConnectorType
from app.database.models.user import User
from app.database.session import get_db
from app.users.dependencies import get_current_user

router = APIRouter(prefix="/connectors", tags=["Enterprise Data Connectors"])


# ==============================================================================
# 1. CATALOG ENDPOINTS
# ==============================================================================


@router.get(
    "/catalog",
    response_model=ConnectorCatalogResponse,
    summary="List available production enterprise connectors",
)
async def get_connector_catalog(
    current_user: User = Depends(get_current_user),
) -> Any:
    return ConnectorRegistry.get_catalog()


# ==============================================================================
# 2. CONNECTION MANAGEMENT ENDPOINTS
# ==============================================================================


@router.post(
    "/connections",
    response_model=ConnectionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new external data connection",
)
async def create_connection(
    payload: ConnectionCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    service = ConnectorService(db)
    conn = await service.create_connection(current_user, payload)
    return ConnectionResponse(
        id=conn.id,
        user_id=conn.user_id,
        workspace_id=conn.workspace_id,
        name=conn.name,
        description=conn.description,
        connector_type=conn.connector_type,
        status=conn.status,
        configuration=conn.configuration,
        credential_reference=conn.credential_reference,
        last_tested_at=conn.last_tested_at,
        last_sync_at=conn.last_sync_at,
        health_status=conn.health_status,
        health_details=conn.health_details,
        sync_schedule=conn.sync_schedule,
        is_active=conn.is_active,
        created_at=conn.created_at,
        updated_at=conn.updated_at,
    )


@router.get(
    "/connections",
    response_model=ConnectionListResponse,
    summary="List all data connections for the authenticated user",
)
async def list_connections(
    connector_type: Optional[ConnectorType] = Query(None, description="Filter by connector type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    service = ConnectorService(db)
    connections = await service.list_connections(current_user, connector_type=connector_type, is_active=is_active)
    items = [
        ConnectionResponse(
            id=c.id,
            user_id=c.user_id,
            workspace_id=c.workspace_id,
            name=c.name,
            description=c.description,
            connector_type=c.connector_type,
            status=c.status,
            configuration=c.configuration,
            credential_reference=c.credential_reference,
            last_tested_at=c.last_tested_at,
            last_sync_at=c.last_sync_at,
            health_status=c.health_status,
            health_details=c.health_details,
            sync_schedule=c.sync_schedule,
            is_active=c.is_active,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )
        for c in connections
    ]
    return ConnectionListResponse(items=items, total=len(items))


@router.get(
    "/connections/{connection_id}",
    response_model=ConnectionResponse,
    summary="Get connection details by ID",
)
async def get_connection(
    connection_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    service = ConnectorService(db)
    try:
        c = await service.get_connection(connection_id, current_user)
        return ConnectionResponse(
            id=c.id,
            user_id=c.user_id,
            workspace_id=c.workspace_id,
            name=c.name,
            description=c.description,
            connector_type=c.connector_type,
            status=c.status,
            configuration=c.configuration,
            credential_reference=c.credential_reference,
            last_tested_at=c.last_tested_at,
            last_sync_at=c.last_sync_at,
            health_status=c.health_status,
            health_details=c.health_details,
            sync_schedule=c.sync_schedule,
            is_active=c.is_active,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )
    except ConnectionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except UnauthorizedConnectionAccessError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.patch(
    "/connections/{connection_id}",
    response_model=ConnectionResponse,
    summary="Update connection metadata, config, or credentials",
)
async def update_connection(
    connection_id: str,
    payload: ConnectionUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    service = ConnectorService(db)
    try:
        c = await service.update_connection(connection_id, current_user, payload)
        return ConnectionResponse(
            id=c.id,
            user_id=c.user_id,
            workspace_id=c.workspace_id,
            name=c.name,
            description=c.description,
            connector_type=c.connector_type,
            status=c.status,
            configuration=c.configuration,
            credential_reference=c.credential_reference,
            last_tested_at=c.last_tested_at,
            last_sync_at=c.last_sync_at,
            health_status=c.health_status,
            health_details=c.health_details,
            sync_schedule=c.sync_schedule,
            is_active=c.is_active,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )
    except ConnectionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except UnauthorizedConnectionAccessError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.delete(
    "/connections/{connection_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a data connection",
)
async def delete_connection(
    connection_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    service = ConnectorService(db)
    try:
        await service.delete_connection(connection_id, current_user)
    except ConnectionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except UnauthorizedConnectionAccessError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


# ==============================================================================
# 3. CONNECTION TESTING ENDPOINTS
# ==============================================================================


@router.post(
    "/connections/{connection_id}/test",
    response_model=ConnectionTestResult,
    summary="Test connectivity for an existing connection",
)
async def test_existing_connection(
    connection_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    service = ConnectorService(db)
    try:
        return await service.test_connection(connection_id, current_user)
    except ConnectionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/test",
    response_model=ConnectionTestResult,
    summary="Ad-hoc test connection parameters before creating",
)
async def test_adhoc_connection(
    payload: ConnectionTestRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    service = ConnectorService(db)
    try:
        return await service.test_connection_adhoc(current_user, payload)
    except ConnectorServiceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/test-direct",
    response_model=ConnectionTestResult,
    summary="Direct test connection parameters before saving",
)
async def test_direct_connection(
    payload: ConnectionTestRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    service = ConnectorService(db)
    try:
        return await service.test_connection_adhoc(current_user, payload)
    except ConnectorServiceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ==============================================================================
# 4. SCHEMA DISCOVERY & PREVIEW ENDPOINTS
# ==============================================================================


@router.get(
    "/connections/{connection_id}/discover",
    response_model=SchemaDiscoveryResponse,
    summary="Discover tables, views, and schema structure",
)
@router.post(
    "/connections/{connection_id}/discover",
    response_model=SchemaDiscoveryResponse,
    summary="Trigger live schema discovery for a connection",
)
async def discover_connection_schema(
    connection_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    service = ConnectorService(db)
    try:
        return await service.discover_schema(connection_id, current_user)
    except ConnectionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/connections/{connection_id}/preview",
    response_model=ResourcePreviewResponse,
    summary="Fetch lightweight data preview for a table or endpoint",
)
async def preview_connection_resource(
    connection_id: str,
    payload: ResourcePreviewRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    service = ConnectorService(db)
    try:
        return await service.preview_resource(connection_id, current_user, payload)
    except ConnectionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ==============================================================================
# 5. SYNC & HEALTH ENDPOINTS
# ==============================================================================


@router.post(
    "/connections/{connection_id}/sync",
    response_model=SyncJobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Trigger an ingestion synchronization job",
)
async def trigger_connection_sync(
    connection_id: str,
    payload: SyncTriggerRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    service = ConnectorService(db)
    try:
        job = await service.trigger_sync(connection_id, current_user, payload)
        return SyncJobResponse(
            id=job.id,
            connection_id=job.connection_id,
            dataset_id=job.dataset_id,
            dataset_version_id=job.dataset_version_id,
            source_resource=job.source_resource,
            sync_type=job.sync_type,
            status=job.status,
            started_at=job.started_at,
            completed_at=job.completed_at,
            rows_processed=job.rows_processed,
            rows_added=job.rows_added,
            rows_updated=job.rows_updated,
            rows_rejected=job.rows_rejected,
            error=job.error,
            sync_metadata=job.sync_metadata,
            created_at=job.created_at,
        )
    except ConnectionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/connections/{connection_id}/syncs",
    response_model=SyncJobListResponse,
    summary="List synchronization job history",
)
async def list_connection_sync_history(
    connection_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    service = ConnectorService(db)
    try:
        jobs = await service.list_sync_jobs(connection_id, current_user)
        items = [
            SyncJobResponse(
                id=j.id,
                connection_id=j.connection_id,
                dataset_id=j.dataset_id,
                dataset_version_id=j.dataset_version_id,
                source_resource=j.source_resource,
                sync_type=j.sync_type,
                status=j.status,
                started_at=j.started_at,
                completed_at=j.completed_at,
                rows_processed=j.rows_processed,
                rows_added=j.rows_added,
                rows_updated=j.rows_updated,
                rows_rejected=j.rows_rejected,
                error=j.error,
                sync_metadata=j.sync_metadata,
                created_at=j.created_at,
            )
            for j in jobs
        ]
        return SyncJobListResponse(items=items, total=len(items))
    except ConnectionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/connections/{connection_id}/health",
    summary="Get multi-dimensional connection health & freshness status",
)
async def get_connection_health(
    connection_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    service = ConnectorService(db)
    try:
        return await service.get_connection_health(connection_id, current_user)
    except ConnectionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/connections/{connection_id}/drift",
    summary="Get latest schema drift analysis for connection",
)
async def get_connection_drift(
    connection_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    service = ConnectorService(db)
    try:
        return await service.get_connection_drift(connection_id, current_user)
    except ConnectionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
