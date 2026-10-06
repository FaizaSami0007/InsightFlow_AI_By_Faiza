"""AI Tool Security, Policy Boundaries & Multi-Agent Execution Guardrails."""

from typing import Any, Dict, List, Optional, Set

from app.core.exceptions import ForbiddenError, ValidationError
from app.database.models.user import User
from app.security.enums import Permission, Role
from app.security.rbac import get_user_role, has_permission

# Explicit tool privilege requirements
TOOL_PERMISSION_MAP: Dict[str, Permission] = {
    # Read-only query tools
    "query_dataset_aggregate": Permission.DATASET_VIEW,
    "get_column_summary": Permission.DATASET_VIEW,
    "search_business_knowledge": Permission.KNOWLEDGE_VIEW,
    "get_model_metrics": Permission.MODEL_VIEW,
    "explain_metric_variance": Permission.DATASET_VIEW,
    "forecast_series": Permission.DATASET_VIEW,
    "detect_anomalies": Permission.DATASET_VIEW,
    
    # Mutating / Sensitive tools
    "train_ml_model": Permission.MODEL_DEPLOY,
    "promote_model_version": Permission.MODEL_DEPLOY,
    "rollback_model_version": Permission.MODEL_ROLLBACK,
    "delete_dataset": Permission.DATASET_DELETE,
    "trigger_connector_sync": Permission.CONNECTION_MANAGE,
    "export_compliance_report": Permission.REPORT_EXPORT,
}


class AIGuard:
    """Deterministic security guardrails for AI tool calling and agent orchestration."""

    MAX_TOOL_CALLS_PER_CONVERSATION_TURN = 8
    MAX_AGENT_DELEGATION_DEPTH = 3
    MAX_PARALLEL_SUBTASKS = 5

    @classmethod
    def validate_tool_execution(
        cls,
        tool_name: str,
        caller_role: Role,
        tool_arguments: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Validate that the caller role is authorized to execute the given AI tool.
        Throws ForbiddenError if execution is unauthorized.
        """
        if tool_name not in TOOL_PERMISSION_MAP:
            # Tool is unknown or not explicitly registered in security policy
            raise ForbiddenError(
                message=f"Execution of unapproved AI tool '{tool_name}' is prohibited.",
                details={"tool_name": tool_name},
            )

        required_permission = TOOL_PERMISSION_MAP[tool_name]
        if not has_permission(caller_role, required_permission):
            raise ForbiddenError(
                message=f"Role '{caller_role.value}' is not authorized to execute tool '{tool_name}'.",
                details={
                    "tool_name": tool_name,
                    "required_permission": required_permission.value,
                    "caller_role": caller_role.value,
                },
            )

        return True

    @classmethod
    def validate_agent_execution_limits(
        cls,
        total_tool_calls: int,
        current_recursion_depth: int,
    ) -> None:
        """Enforce strict bounding limits on multi-agent execution to prevent resource exhaustion and runaway loops."""
        if total_tool_calls > cls.MAX_TOOL_CALLS_PER_CONVERSATION_TURN:
            raise ValidationError(
                f"Exceeded maximum allowed tool executions ({cls.MAX_TOOL_CALLS_PER_CONVERSATION_TURN}) for single turn."
            )

        if current_recursion_depth > cls.MAX_AGENT_DELEGATION_DEPTH:
            raise ValidationError(
                f"Exceeded maximum agent recursion depth ({cls.MAX_AGENT_DELEGATION_DEPTH}). Potential loop detected."
            )
