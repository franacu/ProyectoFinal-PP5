"""Endpoints de emergencias y misiones. Traducen HTTP ⇄ casos de uso; no tienen reglas de negocio.

| Método | Ruta                                                | Actor        |
|--------|-----------------------------------------------------|--------------|
| GET    | /emergencias                                        | operador, supervisor (PV03) |
| GET    | /emergencias/{id}                                   | operador, supervisor |
| GET    | /emergencias/{id}/historial                         | operador, supervisor |
| POST   | /emergencias/{id}/misiones                          | operador     |
| POST   | /emergencias/{id}/misiones/{m}/asignacion           | operador     |
| PUT    | /emergencias/{id}/misiones/{m}/asignacion           | operador (reasignar) |
| POST   | /emergencias/{id}/misiones/{m}/cancelacion          | operador     |
| POST   | /emergencias/{id}/misiones/{m}/rechazo              | jefe de la unidad |
| POST   | /emergencias/{id}/misiones/{m}/inicio               | jefe de la unidad |
| POST   | /emergencias/{id}/misiones/{m}/novedades            | jefe de la unidad |
| POST   | /emergencias/{id}/misiones/{m}/finalizacion         | jefe de la unidad |
| POST   | /emergencias/{id}/cierre                            | supervisor   |
| GET    | /misiones/mias                                      | jefe de unidad |
"""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.dependencies import servicio_de_emergencias
from app.emergencias.schemas import (
    AsignacionCrear,
    EmergenciaDetalle,
    FinalizacionCrear,
    MisionCrear,
    MisionDelJefe,
    MisionDetalle,
    NovedadCrear,
    RechazoCrear,
)
from app.emergencias.service import ServicioEmergencias
from app.internal.identidad import usuario_actual
from app.internal.schemas import RegistroDetalle

Servicio = Annotated[ServicioEmergencias, Depends(servicio_de_emergencias)]
Usuario = Annotated[str, Depends(usuario_actual)]
_MISION = "/{emergencia_id}/misiones/{mision_id}"


class Router:
    def __init__(self) -> None:
        r = self.router = APIRouter(prefix="/emergencias", tags=["emergencias y misiones"])
        r.add_api_route("", self.abiertas_por_prioridad, methods=["GET"])
        r.add_api_route("/{emergencia_id}", self.obtener, methods=["GET"])
        r.add_api_route("/{emergencia_id}/historial", self.historial, methods=["GET"])
        r.add_api_route("/{emergencia_id}/misiones", self.crear_mision, methods=["POST"],
                        status_code=status.HTTP_201_CREATED)
        r.add_api_route(f"{_MISION}/asignacion", self.asignar, methods=["POST"])
        r.add_api_route(f"{_MISION}/asignacion", self.reasignar, methods=["PUT"])
        r.add_api_route(f"{_MISION}/cancelacion", self.cancelar, methods=["POST"])
        r.add_api_route(f"{_MISION}/rechazo", self.rechazar, methods=["POST"])
        r.add_api_route(f"{_MISION}/inicio", self.iniciar, methods=["POST"])
        r.add_api_route(f"{_MISION}/novedades", self.registrar_novedad, methods=["POST"],
                        status_code=status.HTTP_201_CREATED)
        r.add_api_route(f"{_MISION}/finalizacion", self.finalizar, methods=["POST"])
        r.add_api_route("/{emergencia_id}/cierre", self.cerrar, methods=["POST"])

        self.misiones = APIRouter(prefix="/misiones", tags=["emergencias y misiones"])
        self.misiones.add_api_route("/mias", self.misiones_del_jefe, methods=["GET"])

    # ── Consultas ──────────────────────────────────────────────

    def abiertas_por_prioridad(self, servicio: Servicio) -> list[EmergenciaDetalle]:
        return [EmergenciaDetalle.desde_dominio(e) for e in servicio.abiertas_por_prioridad()]

    def obtener(self, emergencia_id: str, servicio: Servicio) -> EmergenciaDetalle:
        return EmergenciaDetalle.desde_dominio(servicio.obtener(emergencia_id))

    def historial(self, emergencia_id: str, servicio: Servicio) -> list[RegistroDetalle]:
        return [RegistroDetalle.desde_dominio(r) for r in servicio.obtener(emergencia_id).registros]

    def misiones_del_jefe(self, servicio: Servicio, usuario: Usuario) -> list[MisionDelJefe]:
        return [MisionDelJefe.desde(e, m) for e, m in servicio.misiones_del_jefe(usuario)]

    # ── Operador ───────────────────────────────────────────────

    def crear_mision(self, emergencia_id: str, datos: MisionCrear, servicio: Servicio,
                     usuario: Usuario) -> MisionDetalle:
        return MisionDetalle.desde_dominio(
            servicio.crear_mision(emergencia_id, usuario, datos.tipo, datos.objetivo, datos.cantidad_personas))

    def asignar(self, emergencia_id: str, mision_id: str, datos: AsignacionCrear, servicio: Servicio,
                usuario: Usuario) -> MisionDetalle:
        return MisionDetalle.desde_dominio(servicio.asignar(emergencia_id, mision_id, datos.unidad_id, usuario))

    def reasignar(self, emergencia_id: str, mision_id: str, datos: AsignacionCrear, servicio: Servicio,
                  usuario: Usuario) -> MisionDetalle:
        return MisionDetalle.desde_dominio(servicio.reasignar(emergencia_id, mision_id, datos.unidad_id, usuario))

    def cancelar(self, emergencia_id: str, mision_id: str, servicio: Servicio, usuario: Usuario) -> MisionDetalle:
        return MisionDetalle.desde_dominio(servicio.cancelar(emergencia_id, mision_id, usuario))

    # ── Jefe de unidad ─────────────────────────────────────────

    def rechazar(self, emergencia_id: str, mision_id: str, datos: RechazoCrear, servicio: Servicio,
                 usuario: Usuario) -> MisionDetalle:
        return MisionDetalle.desde_dominio(servicio.rechazar(emergencia_id, mision_id, usuario, datos.justificacion))

    def iniciar(self, emergencia_id: str, mision_id: str, servicio: Servicio, usuario: Usuario) -> MisionDetalle:
        return MisionDetalle.desde_dominio(servicio.iniciar(emergencia_id, mision_id, usuario))

    def registrar_novedad(self, emergencia_id: str, mision_id: str, datos: NovedadCrear, servicio: Servicio,
                          usuario: Usuario) -> MisionDetalle:
        return MisionDetalle.desde_dominio(servicio.registrar_novedad(emergencia_id, mision_id, usuario, datos.texto))

    def finalizar(self, emergencia_id: str, mision_id: str, datos: FinalizacionCrear, servicio: Servicio,
                  usuario: Usuario) -> MisionDetalle:
        return MisionDetalle.desde_dominio(
            servicio.finalizar(emergencia_id, mision_id, usuario, datos.resultado, datos.tareas))

    # ── Supervisor ─────────────────────────────────────────────

    def cerrar(self, emergencia_id: str, servicio: Servicio, usuario: Usuario) -> EmergenciaDetalle:
        return EmergenciaDetalle.desde_dominio(servicio.cerrar(emergencia_id, usuario))
