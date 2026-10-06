"""Role-Based Access Control (RBAC) definitions and dependency checkers."""

from typing import Callable, Dict, List, Set

from fastapi import Depends

from app.core.exceptions import ForbiddenError
from app.database.models.user import User
from app.security.enums import Permission, Role
from app.users.dependencies import get_current_user

# Deterministic Role-Permission mapping matrix
ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
    Role.OWNER: {
        Permission.DATASET_VIEW,
        Permission.DATASET_EDIT,
        Permission.DATASET_DELETE,
        Permission.DATASET_EXPORT,
        Permission.DATASET_SHARE,
        Permission.CONNECTION_VIEW,
        Permission.CONNECTION_USE,
        Permission.CONNECTION_MANAGE,
        Permission.MODEL_VIEW,
        Permission.MODEL_DEPLOY,
        Permission.MODEL_ROLLBACK,
        Permission.MODEL_RETIRE,
        Permission.KNOWLEDGE_VIEW,
        Permission.KNOWLEDGE_UPLOAD,
        Permission.KNOWLEDGE_DELETE,
        Permission.KNOWLEDGE_MANAGE,
        Permission.REPORT_VIEW,
        Permission.REPORT_CREATE,
        Permission.REPORT_DELETE,
        Permission.REPORT_EXPORT,
        Permission.SECURITY_AUDIT_VIEW,
        Permission.SECURITY_CONFIG_MANAGE,
        Permission.SYSTEM_ADMIN,
    },
    Role.ADMIN: {
        Permission.DATASET_VIEW,
        Permission.DATASET_EDIT,
        Permission.DATASET_DELETE,
        Permission.DATASET_EXPORT,
        Permission.DATASET_SHARE,
        Permission.CONNECTION_VIEW,
        Permission.CONNECTION_USE,
        Permission.CONNECTION_MANAGE,
        Permission.MODEL_VIEW,
        Permission.MODEL_DEPLOY,
        Permission.MODEL_ROLLBACK,
        Permission.MODEL_RETIRE,
        Permission.KNOWLEDGE_VIEW,
        Permission.KNOWLEDGE_UPLOAD,
        Permission.KNOWLEDGE_DELETE,
        Permission.KNOWLEDGE_MANAGE,
        Permission.REPORT_VIEW,
        Permission.REPORT_CREATE,
        Permission.REPORT_DELETE,
        Permission.REPORT_EXPORT,
        Permission.SECURITY_AUDIT_VIEW,
        Permission.SECURITY_CONFIG_MANAGE,
    },
    Role.ANALYST: {
        Permission.DATASET_VIEW,
        Permission.DATASET_EDIT,
        Permission.DATASET_EXPORT,
        Permission.DATASET_SHARE,
        Permission.CONNECTION_VIEW,
        Permission.CONNECTION_USE,
        Permission.MODEL_VIEW,
        Permission.MODEL_DEPLOY,
        Permission.KNOWLEDGE_VIEW,
        Permission.KNOWLEDGE_UPLOAD,
        Permission.REPORT_VIEW,
        Permission.REPORT_CREATE,
        Permission.REPORT_EXPORT,
    },
    Role.MEMBER: {
        Permission.DATASET_VIEW,
        Permission.DATASET_EXPORT,
        Permission.CONNECTION_VIEW,
        Permission.CONNECTION_USE,
        Permission.MODEL_VIEW,
        Permission.KNOWLEDGE_VIEW,
        Permission.REPORT_VIEW,
    },
    Role.VIEWER: {
        Permission.DATASET_VIEW,
        Permission.MODEL_VIEW,
        Permission.KNOWLEDGE_VIEW,
        Permission.REPORT_VIEW,
    },
}


def get_user_role(user: User) -> Role:
    """Retrieve validated Role enum for a user entity."""
    user_role_str = getattr(user, "role", "admin")
    try:
        return Role(user_role_str)
    except ValueError:
        return Role.MEMBER


def has_permission(user_role: Role, required_permission: Permission) -> bool:
    """Check if given role possesses the required permission claim."""
    allowed_permissions = ROLE_PERMISSIONS.get(user_role, set())
    return required_permission in allowed_permissions or Permission.SYSTEM_ADMIN in allowed_permissions


def require_permission(required_permission: Permission) -> Callable:
    """FastAPI dependency factory enforcing that current user has the required permission."""

    async def _permission_dependency(current_user: User = Depends(get_current_user)) -> User:
        user_role = get_user_role(current_user)
        if not has_permission(user_role, required_permission):
            raise ForbiddenError(
                message=f"Access denied. Missing required permission: '{required_permission.value}'.",
                details={
                    "user_id": current_user.id,
                    "user_role": user_role.value,
                    "required_permission": required_permission.value,
                },
            )
        return current_user

    return _permission_dependency


def require_role(allowed_roles: List[Role]) -> Callable:
    """FastAPI dependency factory enforcing that current user has one of allowed roles."""

    async def _role_dependency(current_user: User = Depends(get_current_user)) -> User:
        user_role = get_user_role(current_user)
        if user_role not in allowed_roles:
            raise ForbiddenError(
                message=f"Access denied. Role '{user_role.value}' is not permitted to perform this action.",
                details={
                    "user_id": current_user.id,
                    "user_role": user_role.value,
                    "allowed_roles": [r.value for r in allowed_roles],
                },
            )
        return current_user

    return _role_dependency
