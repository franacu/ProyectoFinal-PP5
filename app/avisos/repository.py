"""Contrato del repositorio de avisos y su versión en memoria (para tests y demos)."""

from typing import Protocol

from dominio.aviso import Aviso, EstadoAviso


class RepositorioAvisos(Protocol):
    def guardar(self, aviso: Aviso) -> None: ...

    def obtener(self, aviso_id: str) -> Aviso | None: ...

    def listar(self, estado: EstadoAviso | None = None) -> list[Aviso]: ...


class RepositorioAvisosEnMemoria:
    def __init__(self) -> None:
        self._avisos: dict[str, Aviso] = {}

    def guardar(self, aviso: Aviso) -> None:
        self._avisos[aviso.id] = aviso

    def obtener(self, aviso_id: str) -> Aviso | None:
        return self._avisos.get(aviso_id)

    def listar(self, estado: EstadoAviso | None = None) -> list[Aviso]:
        avisos = (a for a in self._avisos.values() if estado is None or a.estado is estado)
        return sorted(avisos, key=lambda a: a.registrado_en)
