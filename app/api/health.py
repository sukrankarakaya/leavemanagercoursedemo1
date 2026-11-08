"""Sistem sağlık ucu (spec 0001, AC-1/AC-2)."""

from datetime import UTC, datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict

from app.api.deps import get_health_service
from app.services.health_service import HealthService

router = APIRouter(prefix="/api")


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["ok"]
    database: Literal["ok"]
    server_time: str


def format_utc(moment: datetime) -> str:
    """ISO 8601, saniye hassasiyetinde, `Z` son ekiyle: 2026-11-08T09:30:00Z."""
    return moment.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


@router.get("/health")
def get_health(service: Annotated[HealthService, Depends(get_health_service)]) -> HealthResponse:
    # Düz `def`: senkron DB çağrısı event loop'u kilitlemesin (Known traps 4).
    report = service.check()
    return HealthResponse(status="ok", database="ok", server_time=format_utc(report.server_time))
