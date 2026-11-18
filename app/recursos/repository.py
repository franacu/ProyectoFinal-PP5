"""Contrato del repositorio de la flota y su versión en memoria.

La flota es la raíz de los recursos: la regla "una persona, vehículo o equipo no
integra dos unidades" mira a todas las unidades a la vez. Por eso se carga entera
y se guardan por separado la base o la unidad que cambió.
"""

from typing import Protocol

from dominio.flota import BaseOperativa, Flota
from dominio.unidad import Unidad


class RepositorioFlota(Protocol):
    def cargar(self) -> Flota: ...

    def guardar_base(self, base: BaseOperativa) -> None: ...

    def guardar_unidad(self, unidad: Unidad) -> None: ...


class RepositorioFlotaEnMemoria:
    def __init__(self, flota: Flota | None = None) -> None:
        self._flota = flota or Flota()

    def cargar(self) -> Flota:
        return self._flota

    def guardar_base(self, base: BaseOperativa) -> None:
        pass  # la flota en memoria ya la contiene

    def guardar_unidad(self, unidad: Unidad) -> None:
        pass
