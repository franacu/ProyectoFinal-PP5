"""Valores y validaciones compartidas por todo el dominio.

Ubicacion vive acá (y no en aviso.py) para que Aviso y Emergencia la usen
sin importarse entre sí. `dominio.aviso` la sigue exportando.
"""

from __future__ import annotations

import operator
from dataclasses import dataclass

from dominio.errores import DatoDeAvisoInvalido


def hay_texto(valor) -> bool:
    """Verdadero si hay texto con contenido (rechaza None, "" y solo espacios)."""
    return bool(valor) and not valor.isspace()


def es_entero_positivo(valor) -> bool:
    """Verdadero para 1, 2, 3... Rechaza 0, negativos, decimales, texto, None y True."""
    try:
        return operator.index(valor) > 0 and valor is not True
    except TypeError:
        return False


@dataclass(frozen=True, slots=True)
class Ubicacion:
    direccion: str
    localidad: str

    def __post_init__(self) -> None:
        if not hay_texto(self.direccion) or not hay_texto(self.localidad):
            raise DatoDeAvisoInvalido("La ubicación necesita dirección y localidad")
