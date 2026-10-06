"""Pydantic schemas for Phase 18 Security, RBAC, Audit, and Threat Model APIs."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.security.enums import AuditAction, AuditStatus, Role, SecurityStatus


class PasswordValidationRequest(BaseModel):
    """Payload for evaluating password complexity."""

    password: str = Field(..., description="Plaintext password to validate against enterprise policy.")


class PasswordValidationResponse(BaseModel):
    """Response containing password validation outcome and strength score."""

    is_valid: bool
    strength_score: int = Field(..., ge=0, le=100)
    violations: List[str] = []


class SecurityAuditLogResponse(BaseModel):
    """Serialized audit log entry."""

    id: str
    timestamp: datetime
    actor_id: Optional[str] = None
    actor_email: Optional[str] = None
    actor_role: Optional[str] = None
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    workspace_id: Optional[str] = None
    status: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    correlation_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class ScorecardDimension(BaseModel):
    """Single security evaluation dimension."""

    id: str
    name: str
    status: SecurityStatus
    score: int
    controls_enforced: List[str]
    summary: str


class SecurityScorecardResponse(BaseModel):
    """Complete 15-Dimension Enterprise Security Scorecard."""

    overall_status: SecurityStatus
    overall_score: float
    environment: str
    config_audit: Dict[str, Any]
    dimensions: List[ScorecardDimension]
    total_dimensions: int
    passed_dimensions: int


class ThreatVectorItem(BaseModel):
    """Description of a threat vector and applied mitigations."""

    id: str
    profile: str
    threat_description: str
    entry_point: str
    trust_boundary: str
    mitigation_controls: List[str]
    residual_risk: str


class ThreatModelResponse(BaseModel):
    """System-wide threat model and trust boundary definitions."""

    platform_name: str
    updated_at: str
    total_threat_vectors: int
    trust_boundaries: List[str]
    threat_vectors: List[ThreatVectorItem]
