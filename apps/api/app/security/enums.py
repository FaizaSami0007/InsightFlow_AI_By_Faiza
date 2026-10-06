from enum import Enum


class Role(str, Enum):
    """Enterprise Role-Based Access Control (RBAC) user roles."""

    OWNER = "owner"
    ADMIN = "admin"
    ANALYST = "analyst"
    MEMBER = "member"
    VIEWER = "viewer"


class Permission(str, Enum):
    """Fine-grained deterministic permission claims."""

    # Dataset permissions
    DATASET_VIEW = "dataset:view"
    DATASET_EDIT = "dataset:edit"
    DATASET_DELETE = "dataset:delete"
    DATASET_EXPORT = "dataset:export"
    DATASET_SHARE = "dataset:share"

    # Connection permissions
    CONNECTION_VIEW = "connection:view"
    CONNECTION_USE = "connection:use"
    CONNECTION_MANAGE = "connection:manage"

    # Model permissions
    MODEL_VIEW = "model:view"
    MODEL_DEPLOY = "model:deploy"
    MODEL_ROLLBACK = "model:rollback"
    MODEL_RETIRE = "model:retire"

    # Knowledge & RAG permissions
    KNOWLEDGE_VIEW = "knowledge:view"
    KNOWLEDGE_UPLOAD = "knowledge:upload"
    KNOWLEDGE_DELETE = "knowledge:delete"
    KNOWLEDGE_MANAGE = "knowledge:manage"

    # Report & Dashboard permissions
    REPORT_VIEW = "report:view"
    REPORT_CREATE = "report:create"
    REPORT_DELETE = "report:delete"
    REPORT_EXPORT = "report:export"

    # System & Audit permissions
    SECURITY_AUDIT_VIEW = "security:audit_view"
    SECURITY_CONFIG_MANAGE = "security:config_manage"
    SYSTEM_ADMIN = "system:admin"


class AuditAction(str, Enum):
    """Security audit trail event types."""

    # Identity events
    LOGIN_SUCCESS = "identity.login_success"
    LOGIN_FAILED = "identity.login_failed"
    LOGOUT = "identity.logout"
    PASSWORD_CHANGE = "identity.password_change"
    PERMISSION_CHANGE = "identity.permission_change"

    # Resource events
    DATASET_CREATED = "dataset.created"
    DATASET_DELETED = "dataset.deleted"
    DOCUMENT_UPLOADED = "document.uploaded"
    DOCUMENT_DELETED = "document.deleted"
    CONNECTION_CREATED = "connection.created"
    CONNECTION_TESTED = "connection.tested"
    SYNC_STARTED = "sync.started"
    SYNC_FAILED = "sync.failed"
    MODEL_PROMOTED = "model.promoted"
    MODEL_ROLLED_BACK = "model.rolled_back"
    EXPORT_CREATED = "export.created"

    # Security & Protection events
    PROMPT_INJECTION_BLOCKED = "security.prompt_injection_blocked"
    TOOL_ACCESS_DENIED = "security.tool_access_denied"
    SSRF_BLOCKED = "security.ssrf_blocked"
    RATE_LIMIT_EXCEEDED = "security.rate_limit_exceeded"
    MALICIOUS_FILE_BLOCKED = "security.malicious_file_blocked"
    FORMULA_INJECTION_SANITIZED = "security.formula_injection_sanitized"


class AuditStatus(str, Enum):
    """Execution status for security audit event entries."""

    SUCCESS = "success"
    DENIED = "denied"
    FAILED = "failed"


class SecurityStatus(str, Enum):
    """Component evaluation status for compliance scorecard."""

    PASS = "PASS"
    WARNING = "WARNING"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"
