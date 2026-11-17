"""Casos de uso de consulta de emergencias."""

from app.emergencias.repository import RepositorioEmergencias
from dominio.emergencia import Emergencia, abiertas_por_prioridad
from dominio.errores import NoEncontrado


class EmergenciaNoEncontrada(NoEncontrado):
    """No hay una emergencia con ese identificador."""


class ServicioEmergencias:
    def __init__(self, emergencias: RepositorioEmergencias) -> None:
        self._emergencias = emergencias

    def abiertas_por_prioridad(self) -> tuple[Emergencia, ...]:
        """PV03: Alta, Media, Baja y, a igual gravedad, la aceptada primero."""
        return abiertas_por_prioridad(self._emergencias.listar())

    def obtener(self, emergencia_id: str) -> Emergencia:
        emergencia = self._emergencias.obtener(emergencia_id)
        if emergencia is None:
            raise EmergenciaNoEncontrada(f"No existe la emergencia {emergencia_id}")
        return emergencia
