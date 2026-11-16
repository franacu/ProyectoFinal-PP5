"""Vehículos (§5.4).

Las tres categorías son clases: cada una sabe para qué misiones sirve. La misión
le pregunta "¿servís para evacuar N personas?" y el vehículo contesta (o rechaza)
sin que nadie compare categorías con if.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, replace

from dominio.catalogos import CategoriaVehiculo, CondicionOperativa
from dominio.errores import RecursoInvalido, VehiculoIncompatible
from dominio.valores import es_entero_positivo, hay_texto


@dataclass(frozen=True, kw_only=True)
class Vehiculo(ABC):
    id: str
    condicion: CondicionOperativa = CondicionOperativa.OPERATIVO

    def __post_init__(self) -> None:
        if not hay_texto(self.id):
            raise RecursoInvalido("El vehículo necesita identificación")
        if not CondicionOperativa.contiene(self.condicion):
            raise RecursoInvalido("Condición de vehículo fuera de catálogo")

    @property
    @abstractmethod
    def categoria(self) -> CategoriaVehiculo: ...

    @property
    def operativo(self) -> bool:
        return self.condicion is CondicionOperativa.OPERATIVO

    def con_condicion(self, condicion: CondicionOperativa) -> Vehiculo:
        return replace(self, condicion=condicion)

    def verificar_operativo(self) -> None:
        if not self.operativo:
            raise VehiculoIncompatible(f"El vehículo {self.id} está fuera de servicio")

    # Por defecto un vehículo NO sirve para nada: cada categoría habilita lo suyo.

    def verificar_evacuacion(self, cantidad: int) -> None:
        raise VehiculoIncompatible(f"Un vehículo de {self.categoria.value} no sirve para evacuar")

    def verificar_rescate(self) -> None:
        raise VehiculoIncompatible(f"Un vehículo de {self.categoria.value} no sirve para rescatar")

    def verificar_asistencia(self) -> None:
        raise VehiculoIncompatible(f"Un vehículo de {self.categoria.value} no sirve para asistencia sanitaria")


@dataclass(frozen=True, kw_only=True)
class TransportePersonas(Vehiculo):
    """Capacidad en personas evacuadas, sin contar a la dotación (§5.4)."""

    capacidad_evacuados: int

    def __post_init__(self) -> None:
        super().__post_init__()
        if not es_entero_positivo(self.capacidad_evacuados):
            raise RecursoInvalido("La capacidad de evacuados debe ser un entero positivo")

    @property
    def categoria(self) -> CategoriaVehiculo:
        return CategoriaVehiculo.TRANSPORTE_DE_PERSONAS

    def verificar_evacuacion(self, cantidad: int) -> None:
        if cantidad > self.capacidad_evacuados:
            raise VehiculoIncompatible(
                f"Capacidad insuficiente: se necesitan {cantidad} plazas y hay {self.capacidad_evacuados}")


@dataclass(frozen=True, kw_only=True)
class VehiculoRescate(Vehiculo):
    @property
    def categoria(self) -> CategoriaVehiculo:
        return CategoriaVehiculo.VEHICULO_DE_RESCATE

    def verificar_rescate(self) -> None:
        pass


@dataclass(frozen=True, kw_only=True)
class Ambulancia(Vehiculo):
    @property
    def categoria(self) -> CategoriaVehiculo:
        return CategoriaVehiculo.AMBULANCIA

    def verificar_asistencia(self) -> None:
        pass
