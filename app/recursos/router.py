"""Endpoints de recursos (responsable de recursos; consultas también para operador y supervisor).

| Método | Ruta                                              | Caso de uso                      |
|--------|---------------------------------------------------|----------------------------------|
| GET    | /bases · POST /bases                              | Consultar y registrar bases      |
| GET    | /unidades · GET /unidades/{u} · POST /unidades    | Consultar y registrar unidades   |
| POST   | /unidades/{u}/personal                            | Incorporar personal              |
| DELETE | /unidades/{u}/personal/{p}                        | Retirar personal                 |
| PUT    | /unidades/{u}/vehiculo                            | Cambiar el vehículo              |
| PUT    | /unidades/{u}/vehiculo/condicion                  | Condición del vehículo           |
| POST   | /unidades/{u}/equipamiento                        | Incorporar equipo                |
| DELETE | /unidades/{u}/equipamiento/{e}                    | Retirar equipo                   |
| PUT    | /unidades/{u}/equipamiento/{e}/condicion          | Condición de un equipo           |
| PUT    | /unidades/{u}/condicion                           | Condición de servicio (§8.4)     |
"""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.dependencies import servicio_de_recursos
from app.internal.identidad import usuario_actual
from app.recursos.schemas import (
    BaseDTO,
    CondicionOperativaCambio,
    CondicionServicioCambio,
    EquipoDTO,
    PersonaDTO,
    UnidadCrear,
    UnidadDetalle,
    VehiculoDTO,
)
from app.recursos.service import ServicioRecursos

Servicio = Annotated[ServicioRecursos, Depends(servicio_de_recursos)]
Usuario = Annotated[str, Depends(usuario_actual)]
_CREADO = status.HTTP_201_CREATED


class Router:
    def __init__(self) -> None:
        r = self.router = APIRouter(tags=["recursos"])
        r.add_api_route("/bases", self.bases, methods=["GET"])
        r.add_api_route("/bases", self.registrar_base, methods=["POST"], status_code=_CREADO)
        r.add_api_route("/unidades", self.unidades, methods=["GET"])
        r.add_api_route("/unidades", self.registrar_unidad, methods=["POST"], status_code=_CREADO)
        r.add_api_route("/unidades/{unidad_id}", self.unidad, methods=["GET"])
        r.add_api_route("/unidades/{unidad_id}/personal", self.incorporar_personal, methods=["POST"])
        r.add_api_route("/unidades/{unidad_id}/personal/{persona_id}", self.retirar_personal, methods=["DELETE"])
        r.add_api_route("/unidades/{unidad_id}/vehiculo", self.cambiar_vehiculo, methods=["PUT"])
        r.add_api_route("/unidades/{unidad_id}/vehiculo/condicion", self.condicion_vehiculo, methods=["PUT"])
        r.add_api_route("/unidades/{unidad_id}/equipamiento", self.incorporar_equipo, methods=["POST"])
        r.add_api_route("/unidades/{unidad_id}/equipamiento/{equipo_id}", self.retirar_equipo, methods=["DELETE"])
        r.add_api_route("/unidades/{unidad_id}/equipamiento/{equipo_id}/condicion", self.condicion_equipo,
                        methods=["PUT"])
        r.add_api_route("/unidades/{unidad_id}/condicion", self.cambiar_condicion, methods=["PUT"])

    # ── Consultas ──────────────────────────────────────────────

    def bases(self, servicio: Servicio) -> list[BaseDTO]:
        return [BaseDTO.desde_dominio(b) for b in servicio.bases()]

    def unidades(self, servicio: Servicio) -> list[UnidadDetalle]:
        return [UnidadDetalle.desde_dominio(u) for u in servicio.unidades()]

    def unidad(self, unidad_id: str, servicio: Servicio) -> UnidadDetalle:
        return UnidadDetalle.desde_dominio(servicio.unidad(unidad_id))

    # ── Altas ──────────────────────────────────────────────────

    def registrar_base(self, datos: BaseDTO, servicio: Servicio, usuario: Usuario) -> BaseDTO:
        return BaseDTO.desde_dominio(servicio.registrar_base(datos.id, datos.nombre, datos.ubicacion.a_dominio()))

    def registrar_unidad(self, datos: UnidadCrear, servicio: Servicio, usuario: Usuario) -> UnidadDetalle:
        unidad = servicio.registrar_unidad(
            usuario, datos.id, datos.base_id, datos.jefe.a_dominio(), datos.vehiculo.a_dominio(),
            tuple(p.a_dominio() for p in datos.personal), tuple(e.a_dominio() for e in datos.equipamiento))
        return UnidadDetalle.desde_dominio(unidad)

    # ── Composición y condición ────────────────────────────────

    def incorporar_personal(self, unidad_id: str, datos: PersonaDTO, servicio: Servicio,
                            usuario: Usuario) -> UnidadDetalle:
        return UnidadDetalle.desde_dominio(servicio.incorporar_personal(usuario, unidad_id, datos.a_dominio()))

    def retirar_personal(self, unidad_id: str, persona_id: str, servicio: Servicio,
                         usuario: Usuario) -> UnidadDetalle:
        return UnidadDetalle.desde_dominio(servicio.retirar_personal(usuario, unidad_id, persona_id))

    def cambiar_vehiculo(self, unidad_id: str, datos: VehiculoDTO, servicio: Servicio,
                         usuario: Usuario) -> UnidadDetalle:
        return UnidadDetalle.desde_dominio(servicio.cambiar_vehiculo(usuario, unidad_id, datos.a_dominio()))

    def condicion_vehiculo(self, unidad_id: str, datos: CondicionOperativaCambio, servicio: Servicio,
                           usuario: Usuario) -> UnidadDetalle:
        return UnidadDetalle.desde_dominio(servicio.cambiar_condicion_vehiculo(usuario, unidad_id, datos.condicion))

    def incorporar_equipo(self, unidad_id: str, datos: EquipoDTO, servicio: Servicio,
                          usuario: Usuario) -> UnidadDetalle:
        return UnidadDetalle.desde_dominio(servicio.incorporar_equipo(usuario, unidad_id, datos.a_dominio()))

    def retirar_equipo(self, unidad_id: str, equipo_id: str, servicio: Servicio, usuario: Usuario) -> UnidadDetalle:
        return UnidadDetalle.desde_dominio(servicio.retirar_equipo(usuario, unidad_id, equipo_id))

    def condicion_equipo(self, unidad_id: str, equipo_id: str, datos: CondicionOperativaCambio,
                         servicio: Servicio, usuario: Usuario) -> UnidadDetalle:
        return UnidadDetalle.desde_dominio(
            servicio.cambiar_condicion_equipo(usuario, unidad_id, equipo_id, datos.condicion))

    def cambiar_condicion(self, unidad_id: str, datos: CondicionServicioCambio, servicio: Servicio,
                          usuario: Usuario) -> UnidadDetalle:
        return UnidadDetalle.desde_dominio(servicio.cambiar_condicion(usuario, unidad_id, datos.condicion))
