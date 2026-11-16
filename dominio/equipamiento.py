"""Equipamiento especializado (§5.5)."""

from __future__ import annotations

from dataclasses import dataclass, replace

from dominio.catalogos import CategoriaEquipo, CondicionOperativa
from dominio.errores import RecursoInvalido
from dominio.valores import hay_texto


@dataclass(frozen=True, slots=True)
class Equipo:
    id: str
    categoria: CategoriaEquipo
    condicion: CondicionOperativa = CondicionOperativa.OPERATIVO

    def __post_init__(self) -> None:
        if not hay_texto(self.id):
            raise RecursoInvalido("El equipo necesita identificación")
        if not CategoriaEquipo.contiene(self.categoria):
            raise RecursoInvalido("Categoría de equipo fuera de catálogo")
        if not CondicionOperativa.contiene(self.condicion):
            raise RecursoInvalido("Condición de equipo fuera de catálogo")

    @property
    def operativo(self) -> bool:
        return self.condicion is CondicionOperativa.OPERATIVO

    def con_condicion(self, condicion: CondicionOperativa) -> Equipo:
        return replace(self, condicion=condicion)
