"""Catálogos cerrados del enunciado (§3 y §4).

Son Enum: un valor fuera del catálogo no se puede construir, así que
nunca llega a un aviso.
"""

from enum import Enum


class Catalogo(Enum):
    """Base de los catálogos: pregunta pertenencia sin comparar clases."""

    @classmethod
    def contiene(cls, valor) -> bool:
        # `valor in cls` aceptaría también el texto "inundacion" (Python 3.12+),
        # por eso se compara contra los miembros reales.
        return valor in tuple(cls)


class TipoSituacion(Catalogo):
    INUNDACION = "inundacion"
    INCENDIO = "incendio"
    ACCIDENTE_VIAL = "accidente_vial"


class Gravedad(Catalogo):
    """El orden (ALTA > MEDIA > BAJA) se usa después para priorizar emergencias (§4)."""

    BAJA = 1
    MEDIA = 2
    ALTA = 3