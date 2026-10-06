"""API router for Phase 18 Security, RBAC, Scorecard, Audit Logs & Adversarial Testing."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.user import User
from app.database.session import get_db
from app.security.audit import SecurityAuditService
from app.security.config_check import ProductionSecurityVerifier
from app.security.enums import Permission, Role
from app.security.export_guard import ExportGuard
from app.security.password_policy import PasswordPolicyValidator
from app.security.prompt_guard import PromptGuard
from app.security.rbac import require_permission
from app.security.schemas import (
    PasswordValidationRequest,
    PasswordValidationResponse,
    SecurityAuditLogResponse,
    SecurityScorecardResponse,
    ThreatModelResponse,
)
from app.users.dependencies import get_current_user

router = APIRouter(prefix="/security", tags=["Security & Compliance"])


@router.get("/scorecard", response_model=SecurityScorecardResponse, summary="Get 15-Dimension Enterprise Security Scorecard")
async def get_scorecard(
    current_user: User = Depends(get_current_user),
) -> SecurityScorecardResponse:
    """Retrieve the real-time enterprise security posture across 15 technical dimensions."""
    scorecard_data = ProductionSecurityVerifier.get_security_scorecard()
    return SecurityScorecardResponse(**scorecard_data)


@router.get("/threat-model", response_model=ThreatModelResponse, summary="Get System Threat Model & Trust Boundaries")
async def get_threat_model(
    current_user: User = Depends(get_current_user),
) -> ThreatModelResponse:
    """Retrieve the 13-vector Threat Model covering all trust boundaries and attacker profiles."""
    catalog = SecurityAuditService.get_threat_model_catalog()
    return ThreatModelResponse(**catalog)


@router.get("/config-check", summary="Audit Runtime Production Security Configuration")
async def get_config_check(
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Inspect environment variables, CORS policies, debug mode, and database settings."""
    return ProductionSecurityVerifier.audit_configuration()


@router.get(
    "/audit-logs",
    response_model=List[SecurityAuditLogResponse],
    summary="Query Immutable Security Audit Event Trail",
)
async def list_audit_logs(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    action: Optional[str] = Query(None),
    actor_id: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    resource_type: Optional[str] = Query(None),
    current_user: User = Depends(require_permission(Permission.SECURITY_AUDIT_VIEW)),
    db: AsyncSession = Depends(get_db),
) -> List[SecurityAuditLogResponse]:
    """Retrieve immutable security audit trail entries with filtering. Requires SECURITY_AUDIT_VIEW permission."""
    logs = await SecurityAuditService.query_logs(
        db=db,
        limit=limit,
        offset=offset,
        action=action,
        actor_id=actor_id,
        status=status_filter,
        resource_type=resource_type,
    )
    return [SecurityAuditLogResponse.model_validate(log) for log in logs]


@router.post("/validate-password", response_model=PasswordValidationResponse, summary="Validate Password Against Enterprise Policy")
async def validate_password(
    payload: PasswordValidationRequest,
) -> PasswordValidationResponse:
    """Evaluate candidate password complexity, character distribution, and strength score."""
    is_valid, violations = PasswordPolicyValidator.validate(payload.password)
    strength_score = PasswordPolicyValidator.calculate_strength_score(payload.password)
    return PasswordValidationResponse(
        is_valid=is_valid,
        strength_score=strength_score,
        violations=violations,
    )


@router.post("/test-prompt", summary="Test Prompt Against PromptGuard Injection Defense")
async def test_prompt(
    payload: Dict[str, str],
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Live diagnostic endpoint to test prompt injection patterns and context escaping."""
    prompt = payload.get("prompt", "")
    is_safe, threat_category, reason = PromptGuard.check_prompt_safety(prompt)
    sanitized_context = PromptGuard.sanitize_untrusted_context(prompt, source_label="diagnostic_test")
    return {
        "is_safe": is_safe,
        "threat_category": threat_category,
        "reason": reason,
        "sanitized_context_preview": sanitized_context,
    }


@router.post("/sanitize-formula", summary="Sanitize Tabular Data for Safe Export")
async def sanitize_formula(
    payload: Dict[str, Any],
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Live diagnostic endpoint testing formula injection (CSV Injection / DDE) neutralization."""
    value = payload.get("value", "")
    sanitized_val = ExportGuard.sanitize_cell_value(value)
    return {
        "original_value": value,
        "sanitized_value": sanitized_val,
        "was_sanitized": sanitized_val != value,
    }
