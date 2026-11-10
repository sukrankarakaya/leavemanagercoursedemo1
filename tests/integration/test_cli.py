"""AC-1: ilk İK hesabı yönetim komutu yalnızca boş sistemde çalışır."""

import io
import re

from app.cli import main
from app.config import Settings
from app.services.passwords import Argon2PasswordHasher
from tests.conftest import MutableClock


def test_create_first_hr_only_when_no_users(
    db_url: str,
    fast_hasher: Argon2PasswordHasher,
    clock: MutableClock,
    make_client,  # type: ignore[no-untyped-def]
) -> None:
    settings = Settings(database_url=db_url)
    out, err = io.StringIO(), io.StringIO()
    argv = ["create-first-hr", "--email", "IK@Firma.com", "--name", "İK Uzmanı"]
    code = main(argv, settings=settings, hasher=fast_hasher, clock=clock, out=out, err=err)
    assert code == 0, err.getvalue()
    match = re.search(r"Geçici parola \(yalnızca bir kez gösterilir\): (\S+)", out.getvalue())
    assert match is not None
    temp_password = match.group(1)
    assert len(temp_password) == 12

    login = make_client().post(
        "/api/auth/login", json={"email": "ik@firma.com", "password": temp_password}
    )
    assert login.status_code == 200
    assert login.json()["must_change_password"] is True

    out2, err2 = io.StringIO(), io.StringIO()
    argv2 = ["create-first-hr", "--email", "ikinci@firma.com", "--name", "İK 2"]
    code2 = main(argv2, settings=settings, hasher=fast_hasher, clock=clock, out=out2, err=err2)
    assert code2 == 1
    assert out2.getvalue() == ""
    assert "zaten kullanıcı var" in err2.getvalue()
