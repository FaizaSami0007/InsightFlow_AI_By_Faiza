"""Tests for RBAC matrix, permission checking, and authorization barriers."""

import pytest
from app.database.models.user import User
from app.security.enums import Permission, Role
from app.security.rbac import get_user_role, has_permission, ROLE_PERMISSIONS


def test_role_permission_hierarchy():
    # OWNER has all permissions
    assert has_permission(Role.OWNER, Permission.DATASET_DELETE)
    assert has_permission(Role.OWNER, Permission.MODEL_DEPLOY)
    assert has_permission(Role.OWNER, Permission.SECURITY_AUDIT_VIEW)

    # ADMIN has audit view and config
    assert has_permission(Role.ADMIN, Permission.SECURITY_AUDIT_VIEW)
    assert has_permission(Role.ADMIN, Permission.CONNECTION_MANAGE)

    # ANALYST can create & edit datasets, train models, but cannot manage security audits
    assert has_permission(Role.ANALYST, Permission.DATASET_VIEW)
    assert has_permission(Role.ANALYST, Permission.DATASET_EDIT)
    assert not has_permission(Role.ANALYST, Permission.SECURITY_AUDIT_VIEW)
    assert not has_permission(Role.ANALYST, Permission.DATASET_DELETE)

    # VIEWER is read-only
    assert has_permission(Role.VIEWER, Permission.DATASET_VIEW)
    assert not has_permission(Role.VIEWER, Permission.DATASET_EDIT)
    assert not has_permission(Role.VIEWER, Permission.DATASET_DELETE)
    assert not has_permission(Role.VIEWER, Permission.CONNECTION_MANAGE)
    assert not has_permission(Role.VIEWER, Permission.MODEL_DEPLOY)


def test_get_user_role():
    u_admin = User(id="u1", email="admin@test.com", password_hash="h", full_name="Admin", role="admin")
    assert get_user_role(u_admin) == Role.ADMIN

    u_analyst = User(id="u2", email="analyst@test.com", password_hash="h", full_name="Analyst", role="analyst")
    assert get_user_role(u_analyst) == Role.ANALYST

    u_viewer = User(id="u3", email="viewer@test.com", password_hash="h", full_name="Viewer", role="viewer")
    assert get_user_role(u_viewer) == Role.VIEWER

    u_invalid = User(id="u4", email="unknown@test.com", password_hash="h", full_name="Unknown", role="non_existent")
    assert get_user_role(u_invalid) == Role.MEMBER
