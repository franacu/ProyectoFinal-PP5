"""Catálogos cerrados del enunciado (§3 y §4).

Son Enum: un valor fuera del catálogo no se puede construir, así que
nunca llega a un aviso.
"""

from enum import Enum


class TipoSituacion(Enum):
    INUNDACION = "inundacion"
    INCENDIO = "incendio"
    ACCIDENTE_VIAL = "accidente_vial"


class Gravedad(Enum):
    """El orden (ALTA > MEDIA > BAJA) se usa después para priorizar emergencias (§4)."""

    BAJA = 1
    MEDIA = 2
    ALTA = 3
