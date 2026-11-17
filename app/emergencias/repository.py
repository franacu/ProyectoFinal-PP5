"""Contrato del repositorio de emergencias y su versión en memoria."""

from typing import Protocol

from dominio.emergencia import Emergencia


class RepositorioEmergencias(Protocol):
    def guardar(self, emergencia: Emergencia) -> None: ...

    def obtener(self, emergencia_id: str) -> Emergencia | None: ...

    def listar(self) -> list[Emergencia]: ...


class RepositorioEmergenciasEnMemoria:
    def __init__(self) -> None:
        self._emergencias: dict[str, Emergencia] = {}

    def guardar(self, emergencia: Emergencia) -> None:
        self._emergencias[emergencia.id] = emergencia

    def obtener(self, emergencia_id: str) -> Emergencia | None:
        return self._emergencias.get(emergencia_id)

    def listar(self) -> list[Emergencia]:
        return list(self._emergencias.values())
