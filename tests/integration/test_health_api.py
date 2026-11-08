"""AC-1, AC-2: sağlık ucu gerçek SQLite ile, uçtan uca HTTP."""

from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.domain.clock import FixedClock
from app.main import create_app


def test_health_ok_reports_db_and_fixed_utc_time(db_url: str, fixed_clock: FixedClock) -> None:
    with TestClient(create_app(Settings(database_url=db_url), fixed_clock)) as client:
        response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "database": "ok",
        "server_time": "2026-11-08T09:30:00Z",
    }


def test_health_db_unavailable_returns_503_without_internals(
    tmp_path: Path, fixed_clock: FixedClock
) -> None:
    unreachable = tmp_path / "missing-dir" / "unreachable.db"
    app = create_app(
        Settings(database_url=f"sqlite:///{unreachable.as_posix()}"), fixed_clock, migrate=False
    )
    with TestClient(app) as client:
        response = client.get("/api/health")

    assert response.status_code == 503
    assert response.json() == {
        "error": {"code": "DB_UNAVAILABLE", "message": "Sistem şu anda kullanılamıyor."}
    }
    body = response.text.lower()
    for leak in ("missing-dir", "unreachable.db", str(tmp_path).lower(), "traceback", "sqlite"):
        assert leak not in body


def test_index_page_is_served_in_turkish(db_url: str, fixed_clock: FixedClock) -> None:
    with TestClient(create_app(Settings(database_url=db_url), fixed_clock)) as client:
        response = client.get("/")
        script = client.get("/app.js")

    assert response.status_code == 200
    assert '<html lang="tr">' in response.text
    assert 'aria-live="polite"' in response.text
    # ES module'ü tarayıcı yalnızca JavaScript MIME türüyle yükler (Windows kayıt defteri farkları).
    assert script.status_code == 200
    assert script.headers["content-type"].split(";")[0] in {
        "application/javascript",
        "text/javascript",
    }


class ExplodingHealthService:
    def check(self) -> None:
        raise RuntimeError("secret internal detail /var/db/path")


def test_unexpected_error_returns_500_standard_body_without_internals(
    db_url: str, fixed_clock: FixedClock
) -> None:
    app = create_app(Settings(database_url=db_url), fixed_clock)
    app.state.health_service = ExplodingHealthService()
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/api/health")

    assert response.status_code == 500
    assert response.headers["content-type"].startswith("application/json")
    assert response.json() == {
        "error": {"code": "INTERNAL_ERROR", "message": "Beklenmeyen bir hata oluştu."}
    }
    assert "secret" not in response.text


def test_unknown_api_path_returns_404_standard_body(db_url: str, fixed_clock: FixedClock) -> None:
    with TestClient(create_app(Settings(database_url=db_url), fixed_clock)) as client:
        missing = client.get("/api/does-not-exist")
        wrong_method = client.post("/api/health")

    assert missing.status_code == 404
    assert missing.json() == {
        "error": {"code": "NOT_FOUND", "message": "İstenen kaynak bulunamadı."}
    }
    assert wrong_method.status_code == 405
    assert wrong_method.json()["error"]["code"] == "METHOD_NOT_ALLOWED"
