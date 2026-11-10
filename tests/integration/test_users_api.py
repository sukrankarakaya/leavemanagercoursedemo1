"""Hesap oluşturma ve liste — uçtan uca HTTP, gerçek SQLite."""

import logging
import sqlite3
from pathlib import Path

import pytest

from tests.conftest import NEW_PASSWORD, Account, Accounts


def test_hr_creates_user_temp_password_shown_once(accounts: Accounts) -> None:
    manager = accounts.create("yonetici@firma.com", "MANAGER")
    response = accounts.admin.post(
        "/api/users",
        json={
            "email": "Calisan@Firma.com",
            "full_name": "  Çalışan Kişi ",
            "role": "EMPLOYEE",
            "manager_id": manager.id,
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["user"] == {
        "id": body["user"]["id"],
        "email": "calisan@firma.com",
        "full_name": "Çalışan Kişi",
        "role": "EMPLOYEE",
        "manager_id": manager.id,
    }
    temp = body["temp_password"]
    assert len(temp) == 12
    assert temp != manager.password

    listing = accounts.admin.get("/api/users")
    assert listing.status_code == 200
    assert temp not in listing.text
    assert "password" not in listing.text
    assert "$argon2" not in listing.text
    assert {u["email"] for u in listing.json()} == {
        "ik@firma.com",
        "yonetici@firma.com",
        "calisan@firma.com",
    }
    employee_client = accounts.login(Account(body["user"]["id"], "calisan@firma.com", temp))
    me = employee_client.get("/api/auth/me")
    assert me.status_code == 403  # geçici parola → önce değiştir
    assert temp not in me.text


def test_duplicate_email_case_insensitive_rejected(accounts: Accounts) -> None:
    duplicate = accounts.admin.post(
        "/api/users", json={"email": "IK@FIRMA.COM", "full_name": "Kopya", "role": "HR"}
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "EMAIL_TAKEN"

    invalid = accounts.admin.post(
        "/api/users", json={"email": "bozuk", "full_name": " ", "role": "EMPLOYEE"}
    )
    assert invalid.status_code == 422
    assert set(invalid.json()["error"]["fields"]) == {"email", "full_name", "manager_id"}

    missing = accounts.admin.post("/api/users", json={"email": "a@firma.com"})
    assert missing.status_code == 422
    assert invalid.json()["error"]["code"] == "VALIDATION_ERROR"
    assert set(missing.json()["error"]["fields"]) == {"full_name", "role"}


def test_non_hr_cannot_create_or_list(accounts: Accounts, make_client) -> None:  # type: ignore[no-untyped-def]
    manager = accounts.activate(accounts.create("yonetici@firma.com", "MANAGER"))
    employee = accounts.activate(accounts.create("calisan@firma.com", "EMPLOYEE", manager.id))
    for account in (manager, employee):
        client = accounts.login(account)
        listing = client.get("/api/users")
        create = client.post(
            "/api/users", json={"email": "x@firma.com", "full_name": "X", "role": "HR"}
        )
        for response in (listing, create):
            assert response.status_code == 403
            assert response.json()["error"]["code"] == "FORBIDDEN"
    anonymous = make_client()
    assert anonymous.get("/api/users").status_code == 401
    assert (
        anonymous.post(
            "/api/users", json={"email": "x@firma.com", "full_name": "X", "role": "HR"}
        ).status_code
        == 401
    )
    emails = {u["email"] for u in accounts.admin.get("/api/users").json()}
    assert "x@firma.com" not in emails


def test_only_argon2id_hashes_stored_and_no_secrets_logged(
    accounts: Accounts, db_url: str, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.DEBUG)
    temp_account = accounts.create("yonetici@firma.com", "MANAGER")
    client = accounts.login(temp_account)
    token = client.cookies["lm_session"]
    client.post(
        "/api/auth/password",
        json={"current_password": temp_account.password, "new_password": NEW_PASSWORD},
    )
    client.post("/api/auth/login", json={"email": temp_account.email, "password": "yanlis!!"})

    database = Path(db_url.removeprefix("sqlite:///"))
    with sqlite3.connect(database) as connection:
        hashes = [row[0] for row in connection.execute("SELECT password_hash FROM users")]
        session_ids = [row[0] for row in connection.execute("SELECT token_hash FROM sessions")]
    assert hashes and all(h.startswith("$argon2id$") for h in hashes)
    assert token not in session_ids
    raw = database.read_bytes()
    for secret in (temp_account.password, NEW_PASSWORD, accounts.hr_temp.password, token):
        assert secret.encode() not in raw
        assert secret not in caplog.text
