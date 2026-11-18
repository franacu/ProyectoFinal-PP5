"""Armado de la aplicación FastAPI.

`crear_aplicacion()` sin argumentos conecta con MongoDB al arrancar.
`crear_aplicacion(Repositorios.en_memoria())` no usa base: es lo que usan los tests.
"""

from contextlib import asynccontextmanager
from dataclasses import dataclass

from fastapi import FastAPI

from app.avisos.mongo_repository import RepositorioAvisosMongo
from app.avisos.repository import RepositorioAvisos, RepositorioAvisosEnMemoria
from app.avisos.router import Router as RouterAvisos
from app.avisos.service import ServicioAvisos
from app.emergencias.mongo_repository import RepositorioEmergenciasMongo
from app.emergencias.repository import RepositorioEmergencias, RepositorioEmergenciasEnMemoria
from app.emergencias.router import Router as RouterEmergencias
from app.emergencias.service import ServicioEmergencias
from app.internal.database import ConexionMongo
from app.internal.errores_http import registrar_manejadores
from app.internal.reloj import Reloj, reloj_del_sistema
from app.recursos.mongo_repository import RepositorioFlotaMongo
from app.recursos.repository import RepositorioFlota, RepositorioFlotaEnMemoria
from app.recursos.router import Router as RouterRecursos
from app.recursos.service import ServicioRecursos

conexion = ConexionMongo()


@dataclass(frozen=True)
class Repositorios:
    avisos: RepositorioAvisos
    emergencias: RepositorioEmergencias
    flota: RepositorioFlota

    @classmethod
    def en_memoria(cls) -> "Repositorios":
        return cls(RepositorioAvisosEnMemoria(), RepositorioEmergenciasEnMemoria(), RepositorioFlotaEnMemoria())


def crear_aplicacion(repositorios: Repositorios | None = None, reloj: Reloj = reloj_del_sistema) -> FastAPI:

    def _instalar_servicios(aplicacion: FastAPI, repos: Repositorios) -> None:
        """Privada: crea los servicios una sola vez y los deja en app.state."""
        aplicacion.state.servicio_avisos = ServicioAvisos(repos.avisos, repos.emergencias, reloj)
        aplicacion.state.servicio_emergencias = ServicioEmergencias(repos.emergencias, repos.flota, reloj)
        aplicacion.state.servicio_recursos = ServicioRecursos(repos.flota, reloj)

    @asynccontextmanager
    async def lifespan(aplicacion: FastAPI):
        if repositorios is not None:
            _instalar_servicios(aplicacion, repositorios)
            yield
            return

        base = conexion.conectar()
        _instalar_servicios(aplicacion, Repositorios(RepositorioAvisosMongo(base), RepositorioEmergenciasMongo(base),
                                                     RepositorioFlotaMongo(base)))
        try:
            yield
        finally:
            conexion.cerrar()

    aplicacion = FastAPI(
        title="CRCE — Centro Regional de Coordinación de Emergencias",
        description="API del TP Integrador de Paradigmas de Programación V (FIE-UNDEF).",
        version="0.3.0",
        lifespan=lifespan,
    )
    aplicacion.include_router(RouterAvisos().router)
    emergencias = RouterEmergencias()
    aplicacion.include_router(emergencias.router)
    aplicacion.include_router(emergencias.misiones)
    aplicacion.include_router(RouterRecursos().router)
    aplicacion.add_api_route("/", estado_del_servicio, methods=["GET"], tags=["sistema"])
    registrar_manejadores(aplicacion)
    return aplicacion


def estado_del_servicio() -> dict[str, str]:
    return {"servicio": "crce", "estado": "en línea", "documentacion": "/docs"}


app = crear_aplicacion()
