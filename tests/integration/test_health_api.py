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
