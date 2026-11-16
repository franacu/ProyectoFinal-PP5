"""Distribución de personas distintas sobre los puestos de una misión (§5.3, §8.2).

El sistema NO asigna nominalmente cada persona a un puesto: solo verifica que
EXISTA una forma de repartirlas sin repetir a nadie. Se busca con retroceso;
las unidades son chicas (pocas personas, pocos puestos) y el resultado es exacto.

Ejemplo (PV07): Ana (conducción+rescate), Bruno (conducción), Carla (rescate)
cubren [conducción, rescate, rescate]: Bruno conduce, Ana y Carla rescatan.
"""

from __future__ import annotations

from collections.abc import Sequence

from dominio.catalogos import Competencia
from dominio.personal import Persona


def existe_distribucion(puestos: Sequence[Competencia], personas: tuple[Persona, ...]) -> bool:
    """Verdadero si cada puesto puede ocuparlo una persona distinta con esa competencia."""
    if not puestos:
        return True
    primero, resto = puestos[0], puestos[1:]
    for indice, persona in enumerate(personas):
        if persona.tiene(primero) and existe_distribucion(resto, personas[:indice] + personas[indice + 1:]):
            return True
    return False
