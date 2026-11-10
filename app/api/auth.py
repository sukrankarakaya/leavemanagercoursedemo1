"""Giriş, çıkış, kimlik bilgisi, parola değiştirme uçları (spec 0002)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel, ConfigDict, Field

from app.api.deps import (
    SESSION_COOKIE,
    current_session,
    current_user,
    get_auth_service,
    require_json,
    session_token,
)
from app.api.users import UserOut, user_out
from app.services.auth_service import AuthContext, AuthService

router = APIRouter(prefix="/api/auth", dependencies=[Depends(require_json)])


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(max_length=320)
    password: str = Field(max_length=1024)  # Argon2'ye dev girdi verilmesin


class LoginResponse(BaseModel):
    user: UserOut
    must_change_password: bool


class ChangePasswordRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    current_password: str = Field(max_length=1024)
    new_password: str = Field(max_length=1024)


def _set_session_cookie(request: Request, response: Response, token: str) -> None:
    response.set_cookie(
        SESSION_COOKIE,
        token,
        httponly=True,
        samesite="strict",
        secure=request.app.state.settings.cookie_secure,
        path="/",
    )


@router.post("/login")
def login(
    body: LoginRequest,
    request: Request,
    response: Response,
    auth: Annotated[AuthService, Depends(get_auth_service)],
) -> LoginResponse:
    result = auth.login(body.email, body.password, previous_token=session_token(request))
    _set_session_cookie(request, response, result.token)
    return LoginResponse(
        user=user_out(result.user), must_change_password=result.user.must_change_password
    )


@router.post("/logout", status_code=204)
def logout(
    request: Request, response: Response, auth: Annotated[AuthService, Depends(get_auth_service)]
) -> None:
    auth.logout(session_token(request))
    response.delete_cookie(SESSION_COOKIE, path="/", httponly=True, samesite="strict")


@router.get("/me")
def me(context: Annotated[AuthContext, Depends(current_user)]) -> UserOut:
    return user_out(context.user)


@router.post("/password", status_code=204)
def change_password(
    body: ChangePasswordRequest,
    context: Annotated[AuthContext, Depends(current_session)],
    auth: Annotated[AuthService, Depends(get_auth_service)],
) -> None:
    auth.change_password(context, body.current_password, body.new_password)
