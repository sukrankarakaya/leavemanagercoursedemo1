"""Giriş, oturum, parola değiştirme ve sınır — uçtan uca HTTP, gerçek SQLite, ilerleyen saat."""

from fastapi.testclient import TestClient

from tests.conftest import NEW_PASSWORD, Account, Accounts, MutableClock

GENERIC = {
    "error": {
        "code": "INVALID_CREDENTIALS",
        "message": "E-posta veya parola hatalı ya da çok fazla deneme yapıldı.",
    }
}


def _login(client: TestClient, email: str, password: str):  # type: ignore[no-untyped-def]
    return client.post("/api/auth/login", json={"email": email, "password": password})


def _code(response) -> str:  # type: ignore[no-untyped-def]
    return str(response.json()["error"]["code"])


def test_login_success_case_insensitive_email(accounts: Accounts, make_client) -> None:  # type: ignore[no-untyped-def]
    client = make_client()
    response = _login(client, "  IK@Firma.COM ", accounts.hr.password)
    assert response.status_code == 200
    assert response.json() == {
        "user": {
            "id": accounts.hr.id,
            "email": "ik@firma.com",
            "full_name": "İK Uzmanı",
            "role": "HR",
            "manager_id": None,
        },
        "must_change_password": False,
    }
    assert client.get("/api/auth/me").status_code == 200


def test_wrong_password_unknown_email_and_locked_look_identical(
    accounts: Accounts,
    make_client,  # type: ignore[no-untyped-def]
) -> None:
    client = make_client()
    wrong = _login(client, accounts.hr.email, "yanlis parola!!")
    unknown = _login(client, "yok@firma.com", accounts.hr.password)
    for _ in range(4):
        _login(client, accounts.hr.email, "yanlis parola!!")
    locked = _login(client, accounts.hr.email, accounts.hr.password)
    for response in (wrong, unknown, locked):
        assert response.status_code == 401
        assert response.json() == GENERIC
        assert "set-cookie" not in response.headers


def test_temp_password_user_limited_until_change(accounts: Accounts, make_client) -> None:  # type: ignore[no-untyped-def]
    manager_temp = accounts.create("yonetici@firma.com", "MANAGER")
    client = accounts.login(manager_temp)
    for response in (
        client.get("/api/auth/me"),
        client.get("/api/users"),
        client.post("/api/users", json={"email": "x@firma.com", "full_name": "X", "role": "HR"}),
    ):
        assert response.status_code == 403
        assert _code(response) == "PASSWORD_CHANGE_REQUIRED"
    other = accounts.login(manager_temp)
    assert other.post("/api/auth/logout", json={}).status_code == 204  # çıkış serbest
    changed = client.post(
        "/api/auth/password",
        json={"current_password": manager_temp.password, "new_password": NEW_PASSWORD},
    )
    assert changed.status_code == 204
    assert client.get("/api/auth/me").status_code == 200


def test_change_password_requires_current(accounts: Accounts) -> None:
    client = accounts.login(accounts.hr)
    wrong_current = client.post(
        "/api/auth/password",
        json={"current_password": "yanlis mevcut", "new_password": "baska uzun parola"},
    )
    assert wrong_current.status_code == 422
    assert wrong_current.json()["error"]["fields"] == {"current_password": "Mevcut parola hatalı."}
    too_short = client.post(
        "/api/auth/password",
        json={"current_password": accounts.hr.password, "new_password": "a" * 11},
    )
    assert too_short.status_code == 422
    assert set(too_short.json()["error"]["fields"]) == {"new_password"}
    ok = client.post(
        "/api/auth/password",
        json={"current_password": accounts.hr.password, "new_password": "a" * 128},
    )
    assert ok.status_code == 204


def test_session_rotated_cookie_flags_and_json_only_writes(
    accounts: Accounts,
    make_client,  # type: ignore[no-untyped-def]
) -> None:
    client = make_client()
    first = _login(client, accounts.hr.email, accounts.hr.password)
    cookie_header = first.headers["set-cookie"].lower()
    assert "lm_session=" in cookie_header
    assert "httponly" in cookie_header
    assert "samesite=strict" in cookie_header
    assert "path=/" in cookie_header
    old_token = client.cookies["lm_session"]

    _login(client, accounts.hr.email, accounts.hr.password)  # eski cookie ile yeniden giriş
    assert client.cookies["lm_session"] != old_token
    stale = make_client()
    stale.cookies.set("lm_session", old_token)
    assert stale.get("/api/auth/me").status_code == 401

    form = make_client().post(
        "/api/auth/login",
        data={"email": accounts.hr.email, "password": accounts.hr.password},
    )
    assert form.status_code == 415
    assert _code(form) == "UNSUPPORTED_MEDIA_TYPE"


def test_idle_session_expires(accounts: Accounts, clock: MutableClock) -> None:
    client = accounts.login(accounts.hr)
    clock.advance(minutes=29, seconds=59)
    assert client.get("/api/auth/me").status_code == 200  # hareket: sayaç baştan
    clock.advance(minutes=29, seconds=59)
    assert client.get("/api/auth/me").status_code == 200
    clock.advance(minutes=30)
    expired = client.get("/api/auth/me")
    assert expired.status_code == 401
    assert _code(expired) == "SESSION_EXPIRED"


def test_absolute_session_expires(accounts: Accounts, clock: MutableClock) -> None:
    client = accounts.login(accounts.hr)
    for _ in range(16):  # 16 × 29:59 = 7 sa 59 dk 44 sn, her adımda işlem
        clock.advance(minutes=29, seconds=59)
        assert client.get("/api/auth/me").status_code == 200
    clock.advance(seconds=16)  # girişten tam 8 saat
    expired = client.get("/api/auth/me")
    assert expired.status_code == 401
    assert _code(expired) == "SESSION_EXPIRED"


def test_logout_invalidates_session(accounts: Accounts, make_client) -> None:  # type: ignore[no-untyped-def]
    client = accounts.login(accounts.hr)
    token = client.cookies["lm_session"]
    assert client.post("/api/auth/logout", json={}).status_code == 204
    replay = make_client()
    replay.cookies.set("lm_session", token)
    for response in (replay.get("/api/auth/me"), replay.get("/api/users")):
        assert response.status_code == 401
        assert _code(response) == "UNAUTHENTICATED"


def test_password_change_revokes_other_sessions(accounts: Accounts) -> None:
    laptop = accounts.login(accounts.hr)
    phone = accounts.login(accounts.hr)
    changed = laptop.post(
        "/api/auth/password",
        json={"current_password": accounts.hr.password, "new_password": "bambaska uzun parola"},
    )
    assert changed.status_code == 204
    assert laptop.get("/api/auth/me").status_code == 200
    assert phone.get("/api/auth/me").status_code == 401


def test_me_requires_session(accounts: Accounts, make_client) -> None:  # type: ignore[no-untyped-def]
    anonymous = make_client().get("/api/auth/me")
    assert anonymous.status_code == 401
    assert _code(anonymous) == "UNAUTHENTICATED"
    me = accounts.login(accounts.hr).get("/api/auth/me")
    assert me.json() == {
        "id": accounts.hr.id,
        "email": "ik@firma.com",
        "full_name": "İK Uzmanı",
        "role": "HR",
        "manager_id": None,
    }


def test_unknown_email_is_throttled_too(
    accounts: Accounts,
    make_client,
    clock: MutableClock,  # type: ignore[no-untyped-def]
) -> None:
    client = make_client()
    ghost = Account("-", "hayalet@firma.com", "ne olursa olsun")
    for _ in range(5):
        assert _login(client, ghost.email, ghost.password).status_code == 401
    # Kilit hesabın varlığından bağımsız; gerçek hesap etkilenmez.
    assert _login(client, accounts.hr.email, accounts.hr.password).status_code == 200
    for _ in range(5):
        _login(client, accounts.hr.email, "yanlis parola!!")
    assert _login(client, accounts.hr.email, accounts.hr.password).status_code == 401
    clock.advance(minutes=15)
    assert _login(client, accounts.hr.email, accounts.hr.password).status_code == 200


def test_expired_vs_missing_session_codes(
    accounts: Accounts,
    make_client,
    clock: MutableClock,  # type: ignore[no-untyped-def]
) -> None:
    client = accounts.login(accounts.hr)
    clock.advance(minutes=30)
    assert _code(client.get("/api/auth/me")) == "SESSION_EXPIRED"
    assert _code(client.get("/api/auth/me")) == "UNAUTHENTICATED"  # süresi dolan silindi
    bogus = make_client()
    bogus.cookies.set("lm_session", "uydurma-kimlik")
    assert _code(bogus.get("/api/auth/me")) == "UNAUTHENTICATED"
