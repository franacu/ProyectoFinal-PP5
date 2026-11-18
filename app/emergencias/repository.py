"""Contrato del repositorio de emergencias y su versión en memoria.

Las misiones de una emergencia apuntan a unidades de la flota. Por eso, al leer, el
repositorio recibe la flota ya cargada: la misión y la flota comparten la misma unidad
y un cambio hecho por una lo ve la otra.
"""

from typing import Protocol

from dominio.emergencia import Emergencia
from dominio.flota import Flota


class RepositorioEmergencias(Protocol):
    def guardar(self, emergencia: Emergencia) -> None: ...

    def obtener(self, emergencia_id: str, flota: Flota | None = None) -> Emergencia | None: ...

    def listar(self, flota: Flota | None = None) -> list[Emergencia]: ...


class RepositorioEmergenciasEnMemoria:
    """En memoria las misiones ya apuntan a las unidades de la flota en memoria: `flota` no se usa."""

    def __init__(self) -> None:
        self._emergencias: dict[str, Emergencia] = {}

    def guardar(self, emergencia: Emergencia) -> None:
        self._emergencias[emergencia.id] = emergencia

    def obtener(self, emergencia_id: str, flota: Flota | None = None) -> Emergencia | None:
        return self._emergencias.get(emergencia_id)

    def listar(self, flota: Flota | None = None) -> list[Emergencia]:
        return list(self._emergencias.values())
