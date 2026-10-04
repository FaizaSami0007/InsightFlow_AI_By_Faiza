from typing import Any, Dict, Optional


class AppError(Exception):
    """Base application exception with machine-readable code and status mapping."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_SERVER_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}


class NotFoundError(AppError):
    def __init__(
        self,
        message: str = "Requested resource was not found",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message=message, code="NOT_FOUND", status_code=404, details=details)


class ValidationError(AppError):
    def __init__(self, message: str = "Validation failed", details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message=message, code="VALIDATION_ERROR", status_code=422, details=details)


class AuthenticationError(AppError):
    def __init__(
        self,
        message: str = "Authentication required or invalid credentials",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message=message, code="AUTHENTICATION_ERROR", status_code=401, details=details)


class PermissionDeniedError(AppError):
    def __init__(
        self,
        message: str = "Access to this resource is denied",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message=message, code="PERMISSION_DENIED", status_code=403, details=details)


class ConflictError(AppError):
    def __init__(self, message: str = "Resource conflict", details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message=message, code="CONFLICT", status_code=409, details=details)


class DatabaseUnavailableError(AppError):
    def __init__(
        self,
        message: str = "Database service is currently unreachable",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message=message, code="DATABASE_UNAVAILABLE", status_code=503, details=details)


class ServiceUnavailableError(AppError):
    def __init__(
        self,
        message: str = "Service temporarily unavailable",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message=message, code="SERVICE_UNAVAILABLE", status_code=503, details=details)
