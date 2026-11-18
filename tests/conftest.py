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
from fastapi import HTTPException, Request
from fastapi.testclient import TestClient

from app.auth.dependencies import usuario_actual
from app.auth.usuario import Perfil, Usuario
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
    aplicacion = crear_aplicacion(repositorios, RelojDePrueba())
    aplicacion.dependency_overrides[usuario_actual] = _usuario_de_prueba
    with TestClient(aplicacion) as cliente:
        yield cliente


def _usuario_de_prueba(request: Request) -> Usuario:
    """Reemplaza al token de Keycloak en las pruebas: el usuario y su perfil viajan en encabezados.

    Solo existe en las pruebas. La verificación real del token se prueba en test_autorizacion.py.
    """
    if "X-Usuario" not in request.headers:
        raise HTTPException(401, "Falta el token")
    return Usuario(request.headers["X-Usuario"], Perfil(request.headers["X-Perfil"]))


def como(usuario: str, perfil: Perfil) -> dict[str, str]:
    """Encabezados de identidad de prueba (en la aplicación real, el usuario sale del token)."""
    return {"X-Usuario": usuario, "X-Perfil": perfil.value}


def reportante(usuario: str = "hospital") -> dict[str, str]:
    return como(usuario, Perfil.REPORTANTE)


def operador(usuario: str = "operador1") -> dict[str, str]:
    return como(usuario, Perfil.OPERADOR)


def jefe(usuario: str) -> dict[str, str]:
    return como(usuario, Perfil.JEFE_UNIDAD)


def responsable(usuario: str = "recursos1") -> dict[str, str]:
    return como(usuario, Perfil.RESPONSABLE_RECURSOS)


def supervisor(usuario: str = "supervisor1") -> dict[str, str]:
    return como(usuario, Perfil.SUPERVISOR)


AVISO_DE_INCENDIO = {
    "ubicacion": {"direccion": "Av. San Martín 450", "localidad": "Ushuaia"},
    "tipo": "incendio",
    "gravedad_estimada": "alta",
    "descripcion": "Humo saliendo de una vivienda",
}
