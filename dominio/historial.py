"""Registros históricos inmutables (§9).

Cada registro dice quién hizo qué, cuándo y sobre qué recursos, con los
motivos y resultados propios de la operación. Los agregados (Aviso, Emergencia,
Unidad) solo exponen su historial como tupla: no existe forma de editar ni
borrar un registro.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from dominio.errores import RegistroInvalido
from dominio.valores import hay_texto


class Operacion(Enum):
    # avisos
    AVISO_REGISTRADO = "aviso_registrado"
    NOTA_AGREGADA = "nota_agregada"
    AVISO_DESCARTADO = "aviso_descartado"
    AVISO_ACEPTADO = "aviso_aceptado"
    # emergencias
    EMERGENCIA_CREADA = "emergencia_creada"
    EMERGENCIA_CERRADA = "emergencia_cerrada"
    # misiones
    MISION_CREADA = "mision_creada"
    MISION_ASIGNADA = "mision_asignada"
    MISION_REASIGNADA = "mision_reasignada"
    MISION_RECHAZADA = "mision_rechazada"
    MISION_INICIADA = "mision_iniciada"
    MISION_NOVEDAD = "mision_novedad"
    MISION_CANCELADA = "mision_cancelada"
    MISION_FINALIZADA = "mision_finalizada"
    # recursos
    UNIDAD_REGISTRADA = "unidad_registrada"
    PERSONAL_INCORPORADO = "personal_incorporado"
    PERSONAL_RETIRADO = "personal_retirado"
    VEHICULO_CAMBIADO = "vehiculo_cambiado"
    VEHICULO_CONDICION_CAMBIADA = "vehiculo_condicion_cambiada"
    EQUIPO_INCORPORADO = "equipo_incorporado"
    EQUIPO_RETIRADO = "equipo_retirado"
    EQUIPO_CONDICION_CAMBIADA = "equipo_condicion_cambiada"
    UNIDAD_CONDICION_CAMBIADA = "unidad_condicion_cambiada"


@dataclass(frozen=True, slots=True)
class Registro:
    actor_id: str
    fecha_hora: datetime
    operacion: Operacion
    recursos: tuple[str, ...]
    detalle: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        if not hay_texto(self.actor_id):
            raise RegistroInvalido("El registro necesita un actor")
        if self.fecha_hora is None:
            raise RegistroInvalido("El registro necesita fecha y hora")
        if self.operacion not in tuple(Operacion):
            raise RegistroInvalido(f"Operación desconocida: {self.operacion!r}")
        if not self.recursos:
            raise RegistroInvalido("El registro necesita los recursos afectados")

    @classmethod
    def de(cls, actor_id: str, fecha_hora: datetime, operacion: Operacion,
           *recursos: str, **detalle: str) -> Registro:
        """Atajo: los datos del detalle se guardan como pares (clave, texto)."""
        return cls(actor_id, fecha_hora, operacion, tuple(recursos),
                   tuple((clave, str(valor)) for clave, valor in detalle.items()))

    def dato(self, clave: str) -> str | None:
        """Valor del detalle para una clave (p. ej. 'unidad_anterior')."""
        return dict(self.detalle).get(clave)
