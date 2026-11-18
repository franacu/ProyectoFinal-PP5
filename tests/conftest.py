"""Fixtures de la API: la aplicación se arma con un reloj fijo y dos persistencias.

Cada prueba de la API corre dos veces:
- "memoria": repositorios en memoria;
- "mongo": repositorios de MongoDB sobre mongomock (Mongo simulado). Cada pedido vuelve a
  leer y guardar en la base, así que también se prueba el esquema de persistencia
  (documento ⇄ dominio) de punta a punta.
"""

from datetime import UTC, datetime, timedelta

import mongomock
import pytest
from fastapi.testclient import TestClient

from app.avisos.mongo_repository import RepositorioAvisosMongo
from app.emergencias.mongo_repository import RepositorioEmergenciasMongo
from app.main import Repositorios, crear_aplicacion
from app.recursos.mongo_repository import RepositorioFlotaMongo


class RelojDePrueba:
    """Avanza un minuto en cada consulta: los registros quedan ordenados y son predecibles."""

    def __init__(self) -> None:
        self._ahora = datetime(2026, 11, 20, 8, 0, tzinfo=UTC)

    def __call__(self) -> datetime:
        self._ahora += timedelta(minutes=1)
        return self._ahora


def repositorios_mongo(base) -> Repositorios:
    return Repositorios(RepositorioAvisosMongo(base), RepositorioEmergenciasMongo(base), RepositorioFlotaMongo(base))


@pytest.fixture(params=["memoria", "mongo"])
def cliente(request):
    repositorios = (Repositorios.en_memoria() if request.param == "memoria"
                    else repositorios_mongo(mongomock.MongoClient(tz_aware=True)["crce"]))
    with TestClient(crear_aplicacion(repositorios, RelojDePrueba())) as cliente:
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
