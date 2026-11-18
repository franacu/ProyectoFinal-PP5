"""Endpoints de avisos: traducen HTTP ⇄ casos de uso. No contienen reglas de negocio.

| Método | Ruta                       | Perfiles                                   |
|--------|----------------------------|--------------------------------------------|
| POST   | /avisos                    | reportante                                 |
| GET    | /avisos?estado=pendiente   | operador, supervisor; reportante: los suyos |
| GET    | /avisos/{id}               | operador, supervisor; reportante: el suyo  |
| GET    | /avisos/{id}/emergencia    | operador, supervisor; reportante: la suya (resumen) |
| POST   | /avisos/{id}/notas         | reportante (el dominio exige que sea el autor) |
| POST   | /avisos/{id}/descarte      | operador                                   |
| POST   | /avisos/{id}/aceptacion    | operador                                   |
"""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.auth.dependencies import requiere
from app.auth.usuario import Perfil, Usuario
from app.avisos.schemas import (
    AceptacionCrear,
    AvisoCrear,
    AvisoDetalle,
    DescarteCrear,
    NotaCrear,
    NotaDetalle,
)
from app.avisos.service import ServicioAvisos
from app.dependencies import servicio_de_avisos, servicio_de_emergencias
from app.emergencias.schemas import EmergenciaDetalle, EmergenciaResumen
from app.emergencias.service import ServicioEmergencias
from dominio.aviso import EstadoAviso

Servicio = Annotated[ServicioAvisos, Depends(servicio_de_avisos)]
Emergencias = Annotated[ServicioEmergencias, Depends(servicio_de_emergencias)]
Reportante = Annotated[Usuario, Depends(requiere(Perfil.REPORTANTE))]
Operador = Annotated[Usuario, Depends(requiere(Perfil.OPERADOR))]
Lector = Annotated[Usuario, Depends(requiere(Perfil.REPORTANTE, Perfil.OPERADOR, Perfil.SUPERVISOR))]


class Router:
    def __init__(self) -> None:
        r = self.router = APIRouter(prefix="/avisos", tags=["avisos"])
        r.add_api_route("", self.registrar, methods=["POST"], status_code=status.HTTP_201_CREATED)
        r.add_api_route("", self.listar, methods=["GET"])
        r.add_api_route("/{aviso_id}", self.obtener, methods=["GET"])
        r.add_api_route("/{aviso_id}/emergencia", self.emergencia, methods=["GET"])
        r.add_api_route("/{aviso_id}/notas", self.agregar_nota, methods=["POST"], status_code=status.HTTP_201_CREATED)
        r.add_api_route("/{aviso_id}/descarte", self.descartar, methods=["POST"])
        r.add_api_route("/{aviso_id}/aceptacion", self.aceptar, methods=["POST"], status_code=status.HTTP_201_CREATED)

    def registrar(self, datos: AvisoCrear, servicio: Servicio, usuario: Reportante) -> AvisoDetalle:
        """El reportante es quien está autenticado: no se acepta en el cuerpo."""
        aviso = servicio.registrar(usuario.id, datos.ubicacion.a_dominio(), datos.tipo,
                                   datos.gravedad_estimada.a_dominio(), datos.descripcion)
        return AvisoDetalle.desde_dominio(aviso)

    def listar(self, servicio: Servicio, usuario: Lector, estado: EstadoAviso | None = None) -> list[AvisoDetalle]:
        reportante_id = usuario.id if usuario.es(Perfil.REPORTANTE) else None   # PV01: solo los propios
        return [AvisoDetalle.desde_dominio(a) for a in servicio.listar(estado, reportante_id)]

    def obtener(self, aviso_id: str, servicio: Servicio, usuario: Lector) -> AvisoDetalle:
        aviso = servicio.obtener(aviso_id)
        usuario.exigir_acceso_a(aviso.reportante_id)
        return AvisoDetalle.desde_dominio(aviso)

    def emergencia(self, aviso_id: str, servicio: Servicio, emergencias: Emergencias,
                   usuario: Lector) -> EmergenciaResumen | EmergenciaDetalle:
        """El reportante ve tipo, gravedad, ubicación y estado (§2.1); operador y supervisor, todo."""
        usuario.exigir_acceso_a(servicio.obtener(aviso_id).reportante_id)
        emergencia = emergencias.de_aviso(aviso_id)
        if usuario.es(Perfil.REPORTANTE):
            return EmergenciaResumen.desde_dominio(emergencia)
        return EmergenciaDetalle.desde_dominio(emergencia)

    def agregar_nota(self, aviso_id: str, datos: NotaCrear, servicio: Servicio, usuario: Reportante) -> NotaDetalle:
        return NotaDetalle.desde_dominio(servicio.agregar_nota(aviso_id, usuario.id, datos.texto))

    def descartar(self, aviso_id: str, datos: DescarteCrear, servicio: Servicio, usuario: Operador) -> AvisoDetalle:
        return AvisoDetalle.desde_dominio(servicio.descartar(aviso_id, usuario.id, datos.justificacion))

    def aceptar(self, aviso_id: str, datos: AceptacionCrear, servicio: Servicio,
                usuario: Operador) -> EmergenciaDetalle:
        emergencia = servicio.aceptar(aviso_id, usuario.id, datos.tipo, datos.gravedad.a_dominio())
        return EmergenciaDetalle.desde_dominio(emergencia)
