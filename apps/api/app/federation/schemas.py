"""Pydantic schemas for Phase 10 Multi-Dataset Intelligence and Federation."""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.database.models.federation import RelationshipStatus, RelationshipType


class DatasetCollectionItemCreate(BaseModel):
    dataset_id: str
    dataset_version_id: Optional[str] = None


class DatasetCollectionCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    dataset_ids: List[str] = Field(default_factory=list)


class DatasetCollectionUpdateRequest(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None


class DatasetCollectionItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    collection_id: str
    dataset_id: str
    dataset_version_id: Optional[str] = None
    dataset_name: Optional[str] = None
    created_at: datetime


class RelationshipResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    collection_id: Optional[str] = None
    user_id: str
    source_dataset_id: str
    source_version_id: str
    source_field: str
    target_dataset_id: str
    target_version_id: str
    target_field: str
    relationship_type: RelationshipType
    status: RelationshipStatus
    coverage_ratio: float = 0.0
    source_unique_ratio: float = 0.0
    target_unique_ratio: float = 0.0
    null_rate: float = 0.0
    quality_score: float = 0.0
    evidence: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class DatasetCollectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: Optional[str] = None
    user_id: str
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    items: List[DatasetCollectionItemResponse] = Field(default_factory=list)
    relationships: List[RelationshipResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class DatasetCollectionListResponse(BaseModel):
    items: List[DatasetCollectionResponse]
    total: int


class RelationshipProposeRequest(BaseModel):
    collection_id: Optional[str] = None
    source_dataset_id: str
    source_version_id: str
    source_field: str
    target_dataset_id: str
    target_version_id: str
    target_field: str
    relationship_type: RelationshipType = RelationshipType.MANY_TO_ONE


class RelationshipStatusUpdateRequest(BaseModel):
    status: RelationshipStatus


class RelationshipListResponse(BaseModel):
    items: List[RelationshipResponse]
    total: int


class DiscoveredRelationshipCandidate(BaseModel):
    source_dataset_id: str
    source_dataset_name: Optional[str] = None
    source_version_id: str
    source_field: str
    source_type: str
    target_dataset_id: str
    target_dataset_name: Optional[str] = None
    target_version_id: str
    target_field: str
    target_type: str
    inferred_type: RelationshipType
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str


class DiscoveryResponse(BaseModel):
    candidates: List[DiscoveredRelationshipCandidate]
    total: int


# Federated Analysis Schemas
class FederatedAggregationSpec(BaseModel):
    field: str = Field(description="Qualified field name, e.g. 'Orders.revenue' or 'revenue'")
    agg: Literal["SUM", "AVG", "COUNT", "MIN", "MAX", "COUNT_DISTINCT"] = "SUM"
    alias: Optional[str] = None


class FederatedFilterSpec(BaseModel):
    field: str = Field(description="Qualified field name, e.g. 'Customers.city'")
    operator: Literal["=", "!=", ">", ">=", "<", "<=", "IN", "LIKE", "IS_NULL", "IS_NOT_NULL"] = "="
    value: Any = None


class FederatedAnalysisRequest(BaseModel):
    collection_id: Optional[str] = None
    dataset_version_ids: List[str] = Field(min_length=1, max_length=5)
    dimensions: List[str] = Field(default_factory=list, description="Fields to group by, e.g. ['Customers.segment']")
    measures: List[FederatedAggregationSpec] = Field(min_length=1, description="List of aggregations to compute")
    filters: Optional[List[FederatedFilterSpec]] = Field(default=None)
    limit: Optional[int] = Field(default=100, ge=1, le=10000)
    sort_by: Optional[str] = None
    sort_order: Optional[Literal["ASC", "DESC"]] = "DESC"


class FederatedAnalysisResponse(BaseModel):
    analysis_id: str
    columns: List[str]
    rows: List[Dict[str, Any]]
    row_count: int
    execution_time_ms: float
    datasets_involved: List[Dict[str, Any]]
    relationships_used: List[Dict[str, Any]]
    join_path_description: str
    provenance: Dict[str, Any]
    warnings: List[str] = Field(default_factory=list)
