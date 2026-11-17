"""Endpoints de avisos: traducen HTTP ⇄ casos de uso. No contienen reglas de negocio.

| Método | Ruta                       | Caso de uso                         |
|--------|----------------------------|-------------------------------------|
| POST   | /avisos                    | Registrar un aviso (reportante)     |
| GET    | /avisos?estado=pendiente   | Listar avisos (filtro opcional)     |
| GET    | /avisos/{id}               | Consultar un aviso                  |
| POST   | /avisos/{id}/notas         | Agregar una nota (solo reportante)  |
| POST   | /avisos/{id}/descarte      | Descartar con justificación         |
| POST   | /avisos/{id}/aceptacion    | Aceptar: origina una emergencia     |
"""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.avisos.schemas import (
    AceptacionCrear,
    AvisoCrear,
    AvisoDetalle,
    DescarteCrear,
    NotaCrear,
    NotaDetalle,
)
from app.avisos.service import ServicioAvisos
from app.dependencies import servicio_de_avisos
from app.emergencias.schemas import EmergenciaDetalle
from app.internal.identidad import usuario_actual
from dominio.aviso import EstadoAviso

Servicio = Annotated[ServicioAvisos, Depends(servicio_de_avisos)]
Usuario = Annotated[str, Depends(usuario_actual)]


class Router:
    def __init__(self) -> None:
        self.router = APIRouter(prefix="/avisos", tags=["avisos"])
        self.router.add_api_route("", self.registrar, methods=["POST"], status_code=status.HTTP_201_CREATED)
        self.router.add_api_route("", self.listar, methods=["GET"])
        self.router.add_api_route("/{aviso_id}", self.obtener, methods=["GET"])
        self.router.add_api_route("/{aviso_id}/notas", self.agregar_nota, methods=["POST"],
                                  status_code=status.HTTP_201_CREATED)
        self.router.add_api_route("/{aviso_id}/descarte", self.descartar, methods=["POST"])
        self.router.add_api_route("/{aviso_id}/aceptacion", self.aceptar, methods=["POST"],
                                  status_code=status.HTTP_201_CREATED)

    def registrar(self, datos: AvisoCrear, servicio: Servicio, usuario: Usuario) -> AvisoDetalle:
        """El reportante es quien hace el pedido: no se acepta en el cuerpo."""
        aviso = servicio.registrar(usuario, datos.ubicacion.a_dominio(), datos.tipo,
                                   datos.gravedad_estimada.a_dominio(), datos.descripcion)
        return AvisoDetalle.desde_dominio(aviso)

    def listar(self, servicio: Servicio, estado: EstadoAviso | None = None) -> list[AvisoDetalle]:
        return [AvisoDetalle.desde_dominio(a) for a in servicio.listar(estado)]

    def obtener(self, aviso_id: str, servicio: Servicio) -> AvisoDetalle:
        return AvisoDetalle.desde_dominio(servicio.obtener(aviso_id))

    def agregar_nota(self, aviso_id: str, datos: NotaCrear, servicio: Servicio, usuario: Usuario) -> NotaDetalle:
        return NotaDetalle.desde_dominio(servicio.agregar_nota(aviso_id, usuario, datos.texto))

    def descartar(self, aviso_id: str, datos: DescarteCrear, servicio: Servicio, usuario: Usuario) -> AvisoDetalle:
        return AvisoDetalle.desde_dominio(servicio.descartar(aviso_id, usuario, datos.justificacion))

    def aceptar(self, aviso_id: str, datos: AceptacionCrear, servicio: Servicio,
                usuario: Usuario) -> EmergenciaDetalle:
        emergencia = servicio.aceptar(aviso_id, usuario, datos.tipo, datos.gravedad.a_dominio())
        return EmergenciaDetalle.desde_dominio(emergencia)
