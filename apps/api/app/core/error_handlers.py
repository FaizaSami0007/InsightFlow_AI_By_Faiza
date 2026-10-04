import uuid
from typing import Any, Dict

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import AppError
from app.core.logging import logger, request_id_ctx


def format_error_response(
    code: str,
    message: str,
    details: Dict[str, Any] | None = None,
    request_id: str | None = None,
) -> Dict[str, Any]:
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details if details is not None else {},
            "request_id": request_id or request_id_ctx.get() or str(uuid.uuid4()),
        }
    }


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        req_id = getattr(request.state, "request_id", request_id_ctx.get())
        logger.warning(
            f"Handled application error: [{exc.code}] {exc.message}",
            extra={"extra_data": {"code": exc.code, "details": exc.details, "path": request.url.path}},
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=format_error_response(
                code=exc.code,
                message=exc.message,
                details=exc.details,
                request_id=req_id,
            ),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        req_id = getattr(request.state, "request_id", request_id_ctx.get())
        formatted_details = {"validation_errors": exc.errors()}
        logger.info(
            f"Validation error on {request.method} {request.url.path}",
            extra={"extra_data": formatted_details},
        )
        return JSONResponse(
            status_code=422,
            content=format_error_response(
                code="VALIDATION_ERROR",
                message="Invalid request payload or query parameters",
                details=formatted_details,
                request_id=req_id,
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        req_id = getattr(request.state, "request_id", request_id_ctx.get())
        code_map = {
            400: "BAD_REQUEST",
            401: "AUTHENTICATION_ERROR",
            403: "PERMISSION_DENIED",
            404: "NOT_FOUND",
            405: "METHOD_NOT_ALLOWED",
            409: "CONFLICT",
            422: "VALIDATION_ERROR",
            429: "RATE_LIMIT_EXCEEDED",
            500: "INTERNAL_SERVER_ERROR",
            503: "SERVICE_UNAVAILABLE",
        }
        code = code_map.get(exc.status_code, "HTTP_ERROR")
        return JSONResponse(
            status_code=exc.status_code,
            content=format_error_response(
                code=code,
                message=str(exc.detail),
                details={},
                request_id=req_id,
            ),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        req_id = getattr(request.state, "request_id", request_id_ctx.get()) or str(uuid.uuid4())
        logger.error(
            f"Unhandled server error on {request.method} {request.url.path}: {str(exc)}",
            exc_info=exc,
            extra={"request_id": req_id},
        )
        return JSONResponse(
            status_code=500,
            content=format_error_response(
                code="INTERNAL_SERVER_ERROR",
                message="An unexpected internal server error occurred.",
                details={},
                request_id=req_id,
            ),
        )
