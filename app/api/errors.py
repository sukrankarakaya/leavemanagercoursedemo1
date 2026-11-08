"""Hataları HTTP'ye çeviren handler'lar (docs/conventions.md, Error handling).

`/api` altındaki her hata standart gövdeyi kullanır: {"error": {"code", "message"}}.
"""

import logging

from fastapi import FastAPI, Request
from fastapi.exception_handlers import http_exception_handler
from fastapi.responses import JSONResponse, Response
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.domain.errors import DatabaseUnavailableError, DomainError

logger = logging.getLogger(__name__)

API_PREFIX = "/api"

_STATUS_BY_ERROR: dict[type[DomainError], int] = {
    DatabaseUnavailableError: 503,
}

_HTTP_ERRORS: dict[int, tuple[str, str]] = {
    404: ("NOT_FOUND", "İstenen kaynak bulunamadı."),
    405: ("METHOD_NOT_ALLOWED", "Bu işlem bu adreste desteklenmiyor."),
}
_HTTP_ERROR_DEFAULT = ("HTTP_ERROR", "İstek işlenemedi.")

INTERNAL_ERROR = ("INTERNAL_ERROR", "Beklenmeyen bir hata oluştu.")


def error_body(code: str, message: str) -> dict[str, dict[str, str]]:
    return {"error": {"code": code, "message": message}}


def status_for(error: DomainError) -> int:
    for error_type, status in _STATUS_BY_ERROR.items():
        if isinstance(error, error_type):
            return status
    return 400


async def handle_domain_error(_request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, DomainError)  # noqa: S101 — registered for DomainError only
    # İç ayrıntı (neden zinciri) yalnızca log'a gider, istemciye asla.
    logger.warning("domain error %s", exc.code, exc_info=exc.__cause__ is not None)
    return JSONResponse(status_code=status_for(exc), content=error_body(exc.code, exc.message))


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
    app.add_exception_handler(StarletteHTTPException, handle_http_error)
    app.add_exception_handler(Exception, handle_unexpected_error)
