"""Kullanıcı hesabı kuralları (spec 0002, R-2/R-3/R-7) — yalnızca standart kütüphane."""

import re
import secrets
import string
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from app.domain.errors import ValidationError

EMAIL_MAX_LENGTH = 254
NAME_MAX_LENGTH = 100
PASSWORD_MIN_LENGTH = 12
PASSWORD_MAX_LENGTH = 128
TEMP_PASSWORD_LENGTH = 12
# Karıştırılabilir karakterler (0/O, 1/l/I) çıkarıldı: geçici parola elle aktarılır.
TEMP_PASSWORD_ALPHABET = "".join(
    c for c in string.ascii_letters + string.digits if c not in "0O1lI"
)
_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class Role(StrEnum):
    EMPLOYEE = "EMPLOYEE"
    MANAGER = "MANAGER"
    HR = "HR"


@dataclass(frozen=True)
class User:
    id: str
    email: str
    full_name: str
    role: Role
    manager_id: str | None
    must_change_password: bool
    created_at: datetime


def normalize_email(raw: str) -> str:
    """Baş/son boşluk kırpılır, küçük harfe çevrilir; biçim ve uzunluk doğrulanır."""
    email = raw.strip().lower()
    if not email or len(email) > EMAIL_MAX_LENGTH or not _EMAIL_PATTERN.match(email):
        raise ValidationError(
            {"email": "Geçerli bir e-posta adresi girin (en fazla 254 karakter)."}
        )
    return email


def normalize_full_name(raw: str) -> str:
    name = raw.strip()
    if not name or len(name) > NAME_MAX_LENGTH:
        raise ValidationError({"full_name": "Ad soyad 1–100 karakter olmalıdır."})
    return name


def validate_new_password(new_password: str, *, email: str, current_password: str) -> None:
    """R-7: 12–128 karakter; e-postayla ve mevcut parolayla aynı olamaz."""
    if not PASSWORD_MIN_LENGTH <= len(new_password) <= PASSWORD_MAX_LENGTH:
        raise ValidationError({"new_password": "Parola 12–128 karakter olmalıdır."})
    if new_password.lower() == email.lower():
        raise ValidationError({"new_password": "Parola e-posta adresinizle aynı olamaz."})
    if new_password == current_password:
        raise ValidationError({"new_password": "Yeni parola mevcut parolanızla aynı olamaz."})


def validate_manager(role: Role, manager: User | None, manager_requested: bool) -> None:
    """R-2: Çalışan için yönetici zorunlu; seçilen yönetici Yönetici rolünde olmalı."""
    if manager_requested and (manager is None or manager.role is not Role.MANAGER):
        raise ValidationError(
            {"manager_id": "Yönetici, Yönetici rolündeki mevcut bir hesap olmalıdır."}
        )
    if role is Role.EMPLOYEE and not manager_requested:
        raise ValidationError({"manager_id": "Çalışan rolü için yönetici zorunludur."})


def generate_temp_password() -> str:
    """Kriptografik rastgelelikle 12 karakterlik geçici parola (R-3)."""
    return "".join(secrets.choice(TEMP_PASSWORD_ALPHABET) for _ in range(TEMP_PASSWORD_LENGTH))
