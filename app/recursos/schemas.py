"""DTO de la API de recursos (lo que entra y sale como JSON)."""

from pydantic import BaseModel, Field

from app.internal.schemas import RegistroDetalle, UbicacionDTO
from app.recursos.fabricas import CLASE_DE_VEHICULO, datos_propios_del_vehiculo
from dominio.catalogos import (
    CategoriaEquipo,
    CategoriaVehiculo,
    Competencia,
    CondicionOperativa,
    CondicionServicio,
)
from dominio.equipamiento import Equipo
from dominio.flota import BaseOperativa
from dominio.personal import Persona
from dominio.unidad import Unidad
from dominio.vehiculos import Vehiculo


class PersonaDTO(BaseModel):
    id: str = Field(examples=["ana"])
    nombre: str = Field(examples=["Ana Pérez"])
    competencias: list[Competencia] = Field(examples=[["rescate"]])

    def a_dominio(self) -> Persona:
        return Persona(self.id, self.nombre, frozenset(self.competencias))

    @classmethod
    def desde_dominio(cls, persona: Persona) -> "PersonaDTO":
        competencias = sorted(persona.competencias, key=lambda c: c.value)
        return cls(id=persona.id, nombre=persona.nombre, competencias=competencias)


class VehiculoDTO(BaseModel):
    id: str = Field(examples=["VR-1"])
    categoria: CategoriaVehiculo = Field(examples=["vehiculo_de_rescate"])
    condicion: CondicionOperativa = CondicionOperativa.OPERATIVO
    capacidad_evacuados: int | None = Field(default=None, description="Solo para transporte de personas")

    def a_dominio(self) -> Vehiculo:
        extra = {} if self.capacidad_evacuados is None else {"capacidad_evacuados": self.capacidad_evacuados}
        return CLASE_DE_VEHICULO[self.categoria](id=self.id, condicion=self.condicion, **extra)

    @classmethod
    def desde_dominio(cls, vehiculo: Vehiculo) -> "VehiculoDTO":
        return cls(id=vehiculo.id, categoria=vehiculo.categoria, condicion=vehiculo.condicion,
                   **datos_propios_del_vehiculo(vehiculo))


class EquipoDTO(BaseModel):
    id: str = Field(examples=["ER-1"])
    categoria: CategoriaEquipo = Field(examples=["equipo_de_rescate"])
    condicion: CondicionOperativa = CondicionOperativa.OPERATIVO

    def a_dominio(self) -> Equipo:
        return Equipo(self.id, self.categoria, self.condicion)

    @classmethod
    def desde_dominio(cls, equipo: Equipo) -> "EquipoDTO":
        return cls(id=equipo.id, categoria=equipo.categoria, condicion=equipo.condicion)


class BaseDTO(BaseModel):
    id: str = Field(examples=["B-centro"])
    nombre: str = Field(examples=["Base Centro"])
    ubicacion: UbicacionDTO

    @classmethod
    def desde_dominio(cls, base: BaseOperativa) -> "BaseDTO":
        return cls(id=base.id, nombre=base.nombre, ubicacion=UbicacionDTO.desde_dominio(base.ubicacion))


class UnidadCrear(BaseModel):
    id: str = Field(examples=["U-rescate-1"])
    base_id: str = Field(examples=["B-centro"])
    jefe: PersonaDTO
    vehiculo: VehiculoDTO
    personal: list[PersonaDTO] = Field(default=[], description="Dotación sin contar al jefe")
    equipamiento: list[EquipoDTO] = []


class CondicionServicioCambio(BaseModel):
    condicion: CondicionServicio = Field(examples=["en_mantenimiento"])


class CondicionOperativaCambio(BaseModel):
    condicion: CondicionOperativa = Field(examples=["fuera_de_servicio"])


class UnidadDetalle(BaseModel):
    id: str
    base_id: str
    jefe_id: str
    personal: list[PersonaDTO]
    vehiculo: VehiculoDTO
    equipamiento: list[EquipoDTO]
    condicion: CondicionServicio
    mision_comprometida_id: str | None
    registros: list[RegistroDetalle]

    @classmethod
    def desde_dominio(cls, unidad: Unidad) -> "UnidadDetalle":
        return cls(
            id=unidad.id,
            base_id=unidad.base_id,
            jefe_id=unidad.jefe.id,
            personal=[PersonaDTO.desde_dominio(p) for p in unidad.personal],
            vehiculo=VehiculoDTO.desde_dominio(unidad.vehiculo),
            equipamiento=[EquipoDTO.desde_dominio(e) for e in unidad.equipamiento],
            condicion=unidad.condicion,
            mision_comprometida_id=unidad.mision_comprometida_id,
            registros=[RegistroDetalle.desde_dominio(r) for r in unidad.registros],
        )
