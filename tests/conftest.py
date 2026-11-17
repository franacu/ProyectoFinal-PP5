"""Fixtures de la API: la aplicación se arma en memoria y con un reloj fijo."""

from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.main import Repositorios, crear_aplicacion


class RelojDePrueba:
    """Avanza un minuto en cada consulta: los registros quedan ordenados y son predecibles."""

    def __init__(self) -> None:
        self._ahora = datetime(2026, 11, 20, 8, 0, tzinfo=UTC)

    def __call__(self) -> datetime:
        self._ahora += timedelta(minutes=1)
        return self._ahora


@pytest.fixture
def cliente():
    with TestClient(crear_aplicacion(Repositorios.en_memoria(), RelojDePrueba())) as cliente:
        yield cliente


def como(usuario: str) -> dict[str, str]:
    """Encabezado de identidad provisorio (se reemplaza por el token en la etapa de autenticación)."""
    return {"X-Usuario": usuario}


AVISO_DE_INCENDIO = {
    "ubicacion": {"direccion": "Av. San Martín 450", "localidad": "Ushuaia"},
    "tipo": "incendio",
    "gravedad_estimada": "alta",
    "descripcion": "Humo saliendo de una vivienda",
}
