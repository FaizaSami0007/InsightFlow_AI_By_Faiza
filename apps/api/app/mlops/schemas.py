"""Pydantic schemas and data contracts for Phase 16 Production MLOps."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.database.models.mlops import (
    MLAlertSeverity,
    MLDeploymentEnvironment,
    MLDeploymentStatus,
    MLModelType,
    MLModelVersionStatus,
)

# ==============================================================================
# 1. MODEL REGISTRY SCHEMAS
# ==============================================================================


class MLModelCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    description: Optional[str] = None
    model_type: MLModelType
    task_type: str = Field(..., min_length=1, max_length=80)
    framework: str = Field(default="statsmodels", max_length=60)
    provider: str = Field(default="insightflow_native", max_length=60)
    owner: str = Field(default="system", max_length=120)
    workspace_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MLModelUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    owner: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class MLModelResponse(BaseModel):
    id: str
    user_id: str
    workspace_id: Optional[str] = None
    name: str
    description: Optional[str] = None
    model_type: MLModelType
    task_type: str
    framework: str
    provider: str
    status: str
    owner: str
    tags: List[str]
    metadata_json: Dict[str, Any]
    versions_count: int = 0
    active_production_version: Optional[str] = None
    health_status: str = "GOOD"
    created_at: datetime
    updated_at: datetime


class MLModelListResponse(BaseModel):
    items: List[MLModelResponse]
    total: int


# ==============================================================================
# 2. MODEL VERSION SCHEMAS
# ==============================================================================


class FeatureContractDefinition(BaseModel):
    name: str
    data_type: str  # numeric, categorical, datetime, text
    is_required: bool = True
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    allowed_categories: Optional[List[str]] = None
    nullable: bool = False
    fill_value: Optional[Any] = None


class MLModelVersionCreateRequest(BaseModel):
    version: str = Field(..., min_length=1, max_length=30)
    artifact_location: str = Field(..., min_length=1, max_length=255)
    checksum: Optional[str] = None
    training_dataset_id: Optional[str] = None
    training_dataset_version_id: Optional[str] = None
    feature_schema: Dict[str, Any] = Field(default_factory=dict)
    preprocessing_version: str = Field(default="v1.0.0", max_length=60)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    baseline_metrics: Dict[str, Any] = Field(default_factory=dict)


class MLModelVersionResponse(BaseModel):
    id: str
    model_id: str
    model_name: Optional[str] = None
    model_type: Optional[MLModelType] = None
    version: str
    artifact_location: str
    checksum: str
    training_dataset_id: Optional[str] = None
    training_dataset_version_id: Optional[str] = None
    feature_schema: Dict[str, Any]
    preprocessing_version: str
    parameters: Dict[str, Any]
    metrics: Dict[str, Any]
    baseline_metrics: Dict[str, Any]
    status: MLModelVersionStatus
    approval_record: Optional[Dict[str, Any]] = None
    health_status: str = "GOOD"
    health_details: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class MLModelVersionListResponse(BaseModel):
    items: List[MLModelVersionResponse]
    total: int


# ==============================================================================
# 3. EXPERIMENT TRACKING SCHEMAS
# ==============================================================================


class MLExperimentCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    dataset_id: Optional[str] = None
    dataset_version_id: Optional[str] = None
    features: List[str] = Field(default_factory=list)
    preprocessing_config: Dict[str, Any] = Field(default_factory=dict)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    evaluation_config: Dict[str, Any] = Field(default_factory=dict)


class MLExperimentResponse(BaseModel):
    id: str
    model_id: str
    name: str
    dataset_id: Optional[str] = None
    dataset_version_id: Optional[str] = None
    features: List[str]
    preprocessing_config: Dict[str, Any]
    parameters: Dict[str, Any]
    metrics: Dict[str, Any]
    evaluation_config: Dict[str, Any]
    status: str
    created_at: datetime


# ==============================================================================
# 4. EVALUATION & BASELINE COMPARISON SCHEMAS
# ==============================================================================


class MLModelEvaluationRequest(BaseModel):
    dataset_id: Optional[str] = None
    dataset_version_id: Optional[str] = None
    evaluation_type: str = Field(default="HOLDOUT", max_length=60)
    metrics: Optional[Dict[str, Any]] = None
    baseline_metrics: Optional[Dict[str, Any]] = None
    require_improvement_over_baseline: bool = True
    min_relative_improvement_pct: float = 0.0


class MLModelEvaluationResponse(BaseModel):
    id: str
    model_version_id: str
    dataset_id: Optional[str] = None
    dataset_version_id: Optional[str] = None
    evaluation_type: str
    metrics: Dict[str, Any]
    baseline_comparison: Dict[str, Any]
    passed_validation: bool
    warnings: List[str]
    evaluated_at: datetime


# ==============================================================================
# 5. LIFECYCLE, PROMOTION, DEPLOYMENT & ROLLBACK SCHEMAS
# ==============================================================================


class MLModelPromotionRequest(BaseModel):
    target_status: MLModelVersionStatus
    reason: str = Field(..., min_length=3, max_length=500)
    environment: MLDeploymentEnvironment = MLDeploymentEnvironment.PRODUCTION
    approver_notes: Optional[str] = None


class MLModelRollbackRequest(BaseModel):
    target_version_id: str
    reason: str = Field(..., min_length=3, max_length=500)
    environment: MLDeploymentEnvironment = MLDeploymentEnvironment.PRODUCTION


class MLModelDeploymentCreateRequest(BaseModel):
    environment: MLDeploymentEnvironment = MLDeploymentEnvironment.PRODUCTION
    configuration: Dict[str, Any] = Field(default_factory=dict)


class MLModelDeploymentResponse(BaseModel):
    id: str
    model_version_id: str
    version: Optional[str] = None
    environment: MLDeploymentEnvironment
    status: MLDeploymentStatus
    deployed_by: str
    configuration: Dict[str, Any]
    deployed_at: datetime
    retired_at: Optional[datetime] = None


# ==============================================================================
# 6. DRIFT DETECTION & MONITORING SCHEMAS
# ==============================================================================


class MLModelDriftCheckRequest(BaseModel):
    inference_dataset_id: Optional[str] = None
    inference_dataset_version_id: Optional[str] = None
    inference_records: Optional[List[Dict[str, Any]]] = None
    ground_truth_records: Optional[List[Dict[str, Any]]] = None
    psi_threshold: float = 0.2
    ks_significance: float = 0.05
    missingness_threshold_pct: float = 10.0


class MLModelDriftReportResponse(BaseModel):
    id: str
    model_version_id: str
    dataset_id: Optional[str] = None
    dataset_version_id: Optional[str] = None
    drift_detected: bool
    data_drift_score: float
    feature_drift_results: Dict[str, Any]
    prediction_drift_results: Dict[str, Any]
    concept_drift_results: Dict[str, Any]
    data_quality_results: Dict[str, Any]
    recommendation: str
    evaluated_at: datetime


class MLModelAlertResponse(BaseModel):
    id: str
    model_id: str
    model_version_id: Optional[str] = None
    model_name: Optional[str] = None
    alert_type: str
    severity: MLAlertSeverity
    metric_name: str
    observed_value: float
    threshold: float
    message: str
    evidence: Dict[str, Any]
    is_acknowledged: bool
    created_at: datetime


class MLModelAlertListResponse(BaseModel):
    items: List[MLModelAlertResponse]
    total: int


class MLAlertAcknowledgeRequest(BaseModel):
    notes: Optional[str] = None


# ==============================================================================
# 7. HEALTH, LINEAGE & COMPARISON SCHEMAS
# ==============================================================================


class MLModelHealthDimension(BaseModel):
    score: float
    status: str
    details: Dict[str, Any]


class MLModelHealthResponse(BaseModel):
    model_id: str
    model_name: str
    version_id: str
    version: str
    overall_health: str  # GOOD, WARNING, CRITICAL, UNKNOWN
    overall_score: float
    data_quality: MLModelHealthDimension
    drift: MLModelHealthDimension
    performance: MLModelHealthDimension
    latency: MLModelHealthDimension
    freshness: MLModelHealthDimension
    retraining_recommended: bool
    recommendations: List[str]
    evaluated_at: datetime


class MLModelLineageNode(BaseModel):
    id: str
    node_type: str  # DATASET, PREPROCESSING, EXPERIMENT, MODEL_VERSION, DEPLOYMENT, PREDICTION
    label: str
    details: Dict[str, Any]


class MLModelLineageEdge(BaseModel):
    source: str
    target: str
    relationship: str


class MLModelLineageResponse(BaseModel):
    model_version_id: str
    nodes: List[MLModelLineageNode]
    edges: List[MLModelLineageEdge]


class MLModelComparisonResponse(BaseModel):
    model_id: str
    versions: List[MLModelVersionResponse]
    metric_comparison: Dict[str, Dict[str, Optional[float]]]
    feature_comparison: Dict[str, List[str]]
    parameter_comparison: Dict[str, Dict[str, Any]]
    recommendation: str
