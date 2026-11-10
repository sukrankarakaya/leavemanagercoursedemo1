"""Hesap listesi ve hesap oluşturma — yalnızca İK (yetki kontrolü servis katmanında)."""

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field

from app.api.deps import current_user, get_user_service, require_json
from app.domain.users import User
from app.services.auth_service import AuthContext
from app.services.user_service import UserService

router = APIRouter(prefix="/api/users", dependencies=[Depends(require_json)])


class UserOut(BaseModel):
    """Dışarı açılan hesap bilgisi — parola veya parola özeti asla yok (R-4)."""

    id: str
    email: str
    full_name: str
    role: str
    manager_id: str | None


def user_out(user: User) -> UserOut:
    return UserOut(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role.value,
        manager_id=user.manager_id,
    )


class CreateUserRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(max_length=320)
    full_name: str = Field(max_length=200)
    role: str = Field(max_length=16)
    manager_id: str | None = Field(default=None, max_length=36)


class CreatedUserOut(BaseModel):
    user: UserOut
    temp_password: str  # yalnızca bu yanıtta, bir kez (R-3)


@router.get("")
def list_users(
    context: Annotated[AuthContext, Depends(current_user)],
    users: Annotated[UserService, Depends(get_user_service)],
) -> list[UserOut]:
    return [user_out(user) for user in users.list_users(context.user)]


@router.post("", status_code=201)
def create_user(
    body: CreateUserRequest,
    context: Annotated[AuthContext, Depends(current_user)],
    users: Annotated[UserService, Depends(get_user_service)],
) -> CreatedUserOut:
    created = users.create_user(
        context.user,
        email=body.email,
        full_name=body.full_name,
        role=body.role,
        manager_id=body.manager_id,
    )
    return CreatedUserOut(user=user_out(created.user), temp_password=created.temp_password)
