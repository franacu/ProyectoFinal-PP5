"""Personal operativo (§5.3)."""

from __future__ import annotations

from dataclasses import dataclass

from dominio.catalogos import Competencia
from dominio.errores import RecursoInvalido
from dominio.valores import hay_texto


@dataclass(frozen=True, slots=True)
class Persona:
    """Valor con identificación: una o varias competencias, sin niveles ni vencimientos."""

    id: str
    nombre: str
    competencias: frozenset[Competencia]

    def __post_init__(self) -> None:
        if not hay_texto(self.id) or not hay_texto(self.nombre):
            raise RecursoInvalido("La persona necesita identificación y nombre")
        # acepta cualquier colección y la deja inmutable
        object.__setattr__(self, "competencias", frozenset(self.competencias))
        if not self.competencias:
            raise RecursoInvalido("La persona necesita al menos una competencia")
        if not all(Competencia.contiene(c) for c in self.competencias):
            raise RecursoInvalido("Competencia fuera de catálogo")

    def tiene(self, competencia: Competencia) -> bool:
        return competencia in self.competencias
