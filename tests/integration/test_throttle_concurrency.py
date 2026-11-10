"""AC-17: eşzamanlı başarısız denemeler sayımdan kaçmaz (gerçek SQLite, thread havuzu)."""

from concurrent.futures import ThreadPoolExecutor

import pytest

from app.db.engine import make_engine
from app.db.migrate import upgrade_to_head
from app.domain.errors import InvalidCredentialsError
from app.repositories.unit_of_work import SqlUnitOfWorkFactory
from app.services.auth_service import AuthService
from app.services.passwords import Argon2PasswordHasher
from app.services.user_service import UserService
from tests.conftest import MutableClock


def test_concurrent_failures_still_lock(
    db_url: str, fast_hasher: Argon2PasswordHasher, clock: MutableClock
) -> None:
    upgrade_to_head(db_url)
    engine = make_engine(db_url)
    try:
        uow = SqlUnitOfWorkFactory(engine)
        temp = (
            UserService(uow, fast_hasher, clock)
            .create_first_hr(email="ik@firma.com", full_name="İK")
            .temp_password
        )
        auth = AuthService(uow, fast_hasher, clock)

        def attempt(_: int) -> str:
            try:
                auth.login("ik@firma.com", "yanlis parola!!")
            except InvalidCredentialsError:
                return "rejected"
            return "accepted"

        with ThreadPoolExecutor(max_workers=10) as pool:
            results = list(pool.map(attempt, range(10)))
        assert results == ["rejected"] * 10

        with pytest.raises(InvalidCredentialsError):
            auth.login("ik@firma.com", temp)  # doğru parola da kilitli
        clock.advance(minutes=15)
        assert auth.login("ik@firma.com", temp).user.email == "ik@firma.com"
    finally:
        engine.dispose()
