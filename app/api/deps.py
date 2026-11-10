"""Servis ve oturum bağımlılıkları. Servisler app.main'de (composition root) kurulur ve app.state'te
durur; api katmanı repositories/db'yi hiç görmez (docs/architecture.md, kural 2)."""

from typing import Annotated

from fastapi import Depends, Request
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.domain.errors import PasswordChangeRequiredError
from app.services.auth_service import AuthContext, AuthService
from app.services.health_service import HealthService
from app.services.user_service import UserService

SESSION_COOKIE = "lm_session"
_WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def get_health_service(request: Request) -> HealthService:
    service: HealthService = request.app.state.health_service
    return service


def get_auth_service(request: Request) -> AuthService:
    service: AuthService = request.app.state.auth_service
    return service


def get_user_service(request: Request) -> UserService:
    service: UserService = request.app.state.user_service
    return service


def session_token(request: Request) -> str | None:
    return request.cookies.get(SESSION_COOKIE)


def require_json(request: Request) -> None:
    """Yazma istekleri yalnızca JSON: SameSite=Strict ile birlikte CSRF koruması (security.md)."""
    if request.method in _WRITE_METHODS:
        content_type = request.headers.get("content-type", "").split(";")[0].strip().lower()
        if content_type != "application/json":
            raise StarletteHTTPException(status_code=415)


def current_session(
    request: Request, auth: Annotated[AuthService, Depends(get_auth_service)]
) -> AuthContext:
    """Geçerli oturum — parola değiştirmesi gereken kullanıcıya da izin verir."""
    return auth.authenticate(session_token(request))


def current_user(context: Annotated[AuthContext, Depends(current_session)]) -> AuthContext:
    """Geçerli oturum + geçici parola değiştirilmiş (R-6)."""
    if context.user.must_change_password:
        raise PasswordChangeRequiredError()
    return context
