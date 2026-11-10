"""Servis bağımlılıkları. Servisler app.main'de (composition root) kurulur ve app.state'te durur;
api katmanı repositories/db'yi hiç görmez (docs/architecture.md, kural 2)."""

from fastapi import Request

from app.services.health_service import HealthService


def get_health_service(request: Request) -> HealthService:
    service: HealthService = request.app.state.health_service
    return service
