import logging
from collections.abc import Sequence
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    BusinessRuleViolationError,
    DomainError,
    EntityAlreadyExistsError,
    EntityNotFoundError,
)

logger = logging.getLogger(__name__)

# The ONE place where domain concepts become HTTP concepts.
STATUS_BY_ERROR: dict[type[DomainError], int] = {
    EntityNotFoundError: status.HTTP_404_NOT_FOUND,
    EntityAlreadyExistsError: status.HTTP_409_CONFLICT,
    BusinessRuleViolationError: 422,  # unprocessable
    AuthenticationError: status.HTTP_401_UNAUTHORIZED,
    AuthorizationError: status.HTTP_403_FORBIDDEN,
}


def _status_for(exc: DomainError) -> int:
    for klass in type(exc).__mro__:
        if klass in STATUS_BY_ERROR:
            return STATUS_BY_ERROR[klass]
    return status.HTTP_400_BAD_REQUEST


def _payload(code: str, message: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"error": {"code": code, "message": message, "context": context or {}}}


async def domain_error_handler(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, DomainError)
    return JSONResponse(
        status_code=_status_for(exc),
        content=_payload(exc.code, exc.message, exc.context),
    )


async def validation_error_handler(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)
    return JSONResponse(
        status_code=422,
        content=_payload(
            "validation_error", "Request validation failed", {"errors": jsonable(exc.errors())}
        ),
    )


def jsonable(errors: Sequence[Any]) -> list[Any]:
    # ValueError instances in ctx are not JSON serializable
    cleaned = []
    for err in errors:
        item = {k: v for k, v in err.items() if k != "ctx"}
        if "ctx" in err:
            item["ctx"] = {k: str(v) for k, v in err["ctx"].items()}
        cleaned.append(item)
    return cleaned


async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=_payload("internal_error", "Internal server error"),
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(DomainError, domain_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(Exception, unhandled_error_handler)
