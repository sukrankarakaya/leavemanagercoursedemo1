"""Alan hatalarını HTTP'ye çeviren tek handler (docs/conventions.md, Error handling)."""

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.domain.errors import DatabaseUnavailableError, DomainError

logger = logging.getLogger(__name__)

_STATUS_BY_ERROR: dict[type[DomainError], int] = {
    DatabaseUnavailableError: 503,
}


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


def install_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(DomainError, handle_domain_error)
