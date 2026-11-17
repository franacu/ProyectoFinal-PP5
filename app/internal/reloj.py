"""Reloj de la aplicación.

El dominio nunca consulta la hora del sistema: la recibe. Quien la toma es la capa
de servicios, a través de un reloj inyectable. En los tests se reemplaza por un reloj
fijo y los resultados no dependen del momento en que se ejecutan.
"""

from collections.abc import Callable
from datetime import UTC, datetime

Reloj = Callable[[], datetime]


def reloj_del_sistema() -> datetime:
    return datetime.now(UTC)
