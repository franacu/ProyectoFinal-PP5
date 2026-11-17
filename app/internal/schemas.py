"""DTO de la API compartidos (Pydantic).

Los DTO definen la forma del JSON que entra y sale por HTTP. Son distintos de los
esquemas de Mongo: la API y la base pueden cambiar cada una por su lado.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from dominio.catalogos import Gravedad
from dominio.historial import Registro
from dominio.valores import Ubicacion


class GravedadDTO(str, Enum):
    """En la API la gravedad viaja como texto ("alta"), no como el número interno."""

    BAJA = "baja"
    MEDIA = "media"
    ALTA = "alta"

    def a_dominio(self) -> Gravedad:
        return Gravedad[self.name]

    @classmethod
    def desde_dominio(cls, gravedad: Gravedad) -> "GravedadDTO":
        return cls[gravedad.name]


class UbicacionDTO(BaseModel):
    direccion: str = Field(examples=["Av. San Martín 450"])
    localidad: str = Field(examples=["Ushuaia"])

    def a_dominio(self) -> Ubicacion:
        return Ubicacion(self.direccion, self.localidad)

    @classmethod
    def desde_dominio(cls, ubicacion: Ubicacion) -> "UbicacionDTO":
        return cls(direccion=ubicacion.direccion, localidad=ubicacion.localidad)


class RegistroDetalle(BaseModel):
    actor_id: str
    fecha_hora: datetime
    operacion: str
    recursos: list[str]
    detalle: dict[str, str]

    @classmethod
    def desde_dominio(cls, registro: Registro) -> "RegistroDetalle":
        return cls(
            actor_id=registro.actor_id,
            fecha_hora=registro.fecha_hora,
            operacion=registro.operacion.value,
            recursos=list(registro.recursos),
            detalle=dict(registro.detalle),
        )
