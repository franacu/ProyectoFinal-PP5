"""Endpoints de emergencias (consulta). Las operaciones sobre misiones llegan en la próxima etapa.

| Método | Ruta               | Caso de uso                                   |
|--------|--------------------|-----------------------------------------------|
| GET    | /emergencias       | Abiertas por prioridad (PV03)                 |
| GET    | /emergencias/{id}  | Consultar una emergencia                      |
"""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies import servicio_de_emergencias
from app.emergencias.schemas import EmergenciaDetalle
from app.emergencias.service import ServicioEmergencias

Servicio = Annotated[ServicioEmergencias, Depends(servicio_de_emergencias)]


class Router:
    def __init__(self) -> None:
        self.router = APIRouter(prefix="/emergencias", tags=["emergencias"])
        self.router.add_api_route("", self.abiertas_por_prioridad, methods=["GET"])
        self.router.add_api_route("/{emergencia_id}", self.obtener, methods=["GET"])

    def abiertas_por_prioridad(self, servicio: Servicio) -> list[EmergenciaDetalle]:
        return [EmergenciaDetalle.desde_dominio(e) for e in servicio.abiertas_por_prioridad()]

    def obtener(self, emergencia_id: str, servicio: Servicio) -> EmergenciaDetalle:
        return EmergenciaDetalle.desde_dominio(servicio.obtener(emergencia_id))
