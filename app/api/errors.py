"""Hataları HTTP'ye çeviren handler'lar (docs/conventions.md, Error handling).

`/api` altındaki her hata standart gövdeyi kullanır: {"error": {"code", "message"}}.
"""

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exception_handlers import http_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.domain.errors import (
    DatabaseUnavailableError,
    DomainError,
    EmailTakenError,
    FirstUserExistsError,
    ForbiddenError,
    InvalidCredentialsError,
    PasswordChangeRequiredError,
    SessionExpiredError,
    UnauthenticatedError,
    ValidationError,
)

logger = logging.getLogger(__name__)

API_PREFIX = "/api"

_STATUS_BY_ERROR: dict[type[DomainError], int] = {
    DatabaseUnavailableError: 503,
    InvalidCredentialsError: 401,
    UnauthenticatedError: 401,
    SessionExpiredError: 401,
    PasswordChangeRequiredError: 403,
    ForbiddenError: 403,
    EmailTakenError: 409,
    FirstUserExistsError: 409,
    ValidationError: 422,
}

_HTTP_ERRORS: dict[int, tuple[str, str]] = {
    404: ("NOT_FOUND", "İstenen kaynak bulunamadı."),
    405: ("METHOD_NOT_ALLOWED", "Bu işlem bu adreste desteklenmiyor."),
    415: ("UNSUPPORTED_MEDIA_TYPE", "İstek gövdesi JSON olmalıdır."),
}
_HTTP_ERROR_DEFAULT = ("HTTP_ERROR", "İstek işlenemedi.")

INTERNAL_ERROR = ("INTERNAL_ERROR", "Beklenmeyen bir hata oluştu.")


def error_body(
    code: str, message: str, fields: dict[str, str] | None = None
) -> dict[str, dict[str, Any]]:
    error: dict[str, Any] = {"code": code, "message": message}
    if fields:
        error["fields"] = fields
    return {"error": error}


def status_for(error: DomainError) -> int:
    for error_type, status in _STATUS_BY_ERROR.items():
        if isinstance(error, error_type):
            return status
    return 400


async def handle_domain_error(_request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, DomainError)  # noqa: S101 — registered for DomainError only
    # İç ayrıntı (neden zinciri) yalnızca log'a gider, istemciye asla.
    logger.warning("domain error %s", exc.code, exc_info=exc.__cause__ is not None)
    fields = exc.fields if isinstance(exc, ValidationError) else None
    return JSONResponse(
        status_code=status_for(exc), content=error_body(exc.code, exc.message, fields)
    )


async def handle_request_validation(_request: Request, exc: Exception) -> JSONResponse:
    """Pydantic doğrulama hatası → 422 standart gövde; girilen değerler geri yansıtılmaz."""
    assert isinstance(exc, RequestValidationError)  # noqa: S101 — registered for it only
    fields: dict[str, str] = {}
    for error in exc.errors():
        location = [str(part) for part in error.get("loc", ()) if part != "body"]
        fields[".".join(location) or "body"] = "Bu alan eksik veya geçersiz."
    return JSONResponse(
        status_code=422,
        content=error_body(ValidationError.code, ValidationError.message, fields),
    )


async def handle_http_error(request: Request, exc: Exception) -> Response:
    assert isinstance(exc, StarletteHTTPException)  # noqa: S101 — registered for it only
    if not request.url.path.startswith(API_PREFIX):
        return await http_exception_handler(request, exc)  # statik sayfalar: varsayılan davranış
    code, message = _HTTP_ERRORS.get(exc.status_code, _HTTP_ERROR_DEFAULT)
    return JSONResponse(
        status_code=exc.status_code,
        content=error_body(code, message),
        headers=getattr(exc, "headers", None),
    )


async def handle_unexpected_error(_request: Request, exc: Exception) -> JSONResponse:
    # Yığın izi yalnızca log'a; istemci genel mesajı görür.
    logger.error("unexpected error", exc_info=exc)
    return JSONResponse(status_code=500, content=error_body(*INTERNAL_ERROR))


def install_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(DomainError, handle_domain_error)
    app.add_exception_handler(RequestValidationError, handle_request_validation)
    app.add_exception_handler(StarletteHTTPException, handle_http_error)
    app.add_exception_handler(Exception, handle_unexpected_error)
