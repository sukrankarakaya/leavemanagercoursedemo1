"""Parola özeti: Argon2id (docs/security.md). Düz parola hiçbir yerde saklanmaz."""

from typing import Protocol

from argon2 import PasswordHasher as _Argon2
from argon2 import Type
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError


class PasswordHasher(Protocol):
    def hash(self, password: str) -> str: ...
    def verify(self, password_hash: str, password: str) -> bool: ...
    def dummy_verify(self, password: str) -> None:
        """Var olmayan hesapta da aynı işi yapar: yanıt süresi hesabın varlığını sızdırmasın."""
        ...


class Argon2PasswordHasher:
    def __init__(
        self, *, time_cost: int = 3, memory_cost: int = 65536, parallelism: int = 4
    ) -> None:
        self._hasher = _Argon2(
            time_cost=time_cost, memory_cost=memory_cost, parallelism=parallelism, type=Type.ID
        )
        self._dummy_hash = self._hasher.hash("dummy-password-for-timing")

    def hash(self, password: str) -> str:
        return self._hasher.hash(password)

    def verify(self, password_hash: str, password: str) -> bool:
        try:
            return self._hasher.verify(password_hash, password)
        except (VerifyMismatchError, VerificationError, InvalidHashError):
            return False

    def dummy_verify(self, password: str) -> None:
        self.verify(self._dummy_hash, password)
