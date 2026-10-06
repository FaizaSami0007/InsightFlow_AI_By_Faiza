from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from app.database.models.connectors import (
    ConnectionHealthStatus,
    ConnectionStatus,
    ConnectorType,
    SyncJobStatus,
    SyncType,
)

# ==============================================================================
# 1. CONNECTOR CATALOG SCHEMAS
# ==============================================================================


class ConnectorCatalogItem(BaseModel):
    connector_type: ConnectorType
    name: str
    category: str
    description: str
    supported_auth: List[str]
    capabilities: List[str]
    required_config: List[str]
    is_available: bool = True


class ConnectorCatalogResponse(BaseModel):
    items: List[ConnectorCatalogItem]
    total: int


# ==============================================================================
# 2. CONNECTION MANAGEMENT SCHEMAS
# ==============================================================================


class ConnectionCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    description: Optional[str] = None
    connector_type: ConnectorType
    configuration: Dict[str, Any] = Field(default_factory=dict)
    credentials: Optional[Dict[str, Any]] = Field(default_factory=dict)
    sync_schedule: Optional[str] = None  # e.g. "0 */6 * * *" or "HOURLY"
    workspace_id: Optional[str] = None

    @field_validator("connector_type", mode="before")
    @classmethod
    def normalize_connector_type(cls, v: Any) -> Any:
        if isinstance(v, str):
            v_upper = v.strip().upper()
            if v_upper in ConnectorType.__members__:
                return ConnectorType[v_upper]
        return v


class ConnectionUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    configuration: Optional[Dict[str, Any]] = None
    credentials: Optional[Dict[str, Any]] = None
    sync_schedule: Optional[str] = None
    is_active: Optional[bool] = None


class ConnectionTestRequest(BaseModel):
    connector_type: Optional[ConnectorType] = None
    configuration: Optional[Dict[str, Any]] = None
    credentials: Optional[Dict[str, Any]] = None

    @field_validator("connector_type", mode="before")
    @classmethod
    def normalize_connector_type(cls, v: Any) -> Any:
        if isinstance(v, str):
            v_upper = v.strip().upper()
            if v_upper in ConnectorType.__members__:
                return ConnectorType[v_upper]
        return v


class ConnectionTestResult(BaseModel):
    success: bool
    status: str  # SUCCESS, AUTHENTICATION_FAILED, NETWORK_ERROR, INVALID_CONFIGURATION, TIMEOUT, PERMISSION_DENIED
    message: str
    latency_ms: float
    discovered_resources_count: int = 0
    tested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ConnectionResponse(BaseModel):
    id: str
    user_id: str
    workspace_id: Optional[str] = None
    name: str
    description: Optional[str] = None
    connector_type: ConnectorType
    status: ConnectionStatus
    configuration: Dict[str, Any]
    credential_reference: Optional[str] = None
    last_tested_at: Optional[datetime] = None
    last_sync_at: Optional[datetime] = None
    health_status: ConnectionHealthStatus
    health_details: Dict[str, Any]
    sync_schedule: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ConnectionListResponse(BaseModel):
    items: List[ConnectionResponse]
    total: int


# ==============================================================================
# 3. SCHEMA DISCOVERY & PREVIEW SCHEMAS
# ==============================================================================


class ResourceColumnSpec(BaseModel):
    name: str
    data_type: str
    nullable: bool = True
    is_primary_key: bool = False


class ResourceSpec(BaseModel):
    resource_id: str
    name: str
    resource_type: str  # TABLE, VIEW, ENDPOINT, FILE, SHEET
    schema_name: Optional[str] = None
    estimated_rows: Optional[int] = None
    columns: List[ResourceColumnSpec] = Field(default_factory=list)


class SchemaDiscoveryResponse(BaseModel):
    connection_id: str
    resources: List[ResourceSpec]
    discovered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ResourcePreviewRequest(BaseModel):
    resource_id: str
    row_limit: int = Field(default=50, ge=1, le=500)
    query_filter: Optional[str] = None


class ResourcePreviewResponse(BaseModel):
    resource_id: str
    columns: List[str]
    data_types: Dict[str, str]
    rows: List[Dict[str, Any]]
    total_preview_rows: int
    estimated_total_rows: Optional[int] = None


# ==============================================================================
# 4. SYNC & INGESTION SCHEMAS
# ==============================================================================


class SyncTriggerRequest(BaseModel):
    source_resource: str
    dataset_name: Optional[str] = None
    sync_type: SyncType = SyncType.FULL_SYNC
    target_dataset_id: Optional[str] = None
    incremental_cursor_column: Optional[str] = None
    column_selection: Optional[List[str]] = None
    row_limit: Optional[int] = None


class SyncJobResponse(BaseModel):
    id: str
    connection_id: str
    dataset_id: Optional[str] = None
    dataset_version_id: Optional[str] = None
    source_resource: str
    sync_type: SyncType
    status: SyncJobStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    rows_processed: int
    rows_added: int
    rows_updated: int
    rows_rejected: int
    error: Optional[str] = None
    sync_metadata: Dict[str, Any]
    created_at: datetime


class SyncJobListResponse(BaseModel):
    items: List[SyncJobResponse]
    total: int


# ==============================================================================
# 5. SCHEMA DRIFT & HEALTH SCHEMAS
# ==============================================================================


class SchemaDriftReport(BaseModel):
    has_drift: bool
    added_columns: List[str] = Field(default_factory=list)
    removed_columns: List[str] = Field(default_factory=list)
    type_changes: Dict[str, Dict[str, str]] = Field(default_factory=dict)
    severity: str = "NONE"  # NONE, WARNING, CRITICAL
    recommendation: str = "NO_ACTION"


class ConnectionHealthResponse(BaseModel):
    connection_id: str
    health_status: ConnectionHealthStatus
    health_score: float
    last_successful_sync: Optional[datetime] = None
    freshness_status: str  # FRESH, STALE, OVERDUE, UNKNOWN
    drift_status: SchemaDriftReport
    recommendations: List[str]
