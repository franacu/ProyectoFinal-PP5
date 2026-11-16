"""Flota: bases operativas y unidades de respuesta (§5.1, §5.2).

Es la raíz de consistencia de los recursos porque la regla "una persona, vehículo o
equipo no puede estar en dos unidades" involucra a TODAS las unidades: ninguna unidad
puede garantizarla sola.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from dominio.equipamiento import Equipo
from dominio.errores import NoEncontrado, RecursoDuplicado, RecursoInvalido
from dominio.personal import Persona
from dominio.unidad import Unidad
from dominio.valores import Ubicacion, hay_texto
from dominio.vehiculos import Vehiculo


@dataclass(frozen=True, slots=True)
class BaseOperativa:
    id: str
    nombre: str
    ubicacion: Ubicacion

    def __post_init__(self) -> None:
        if not hay_texto(self.id) or not hay_texto(self.nombre) or self.ubicacion is None:
            raise RecursoInvalido("La base necesita identificación, nombre y ubicación")


class Flota:
    def __init__(self) -> None:
        self._bases: dict[str, BaseOperativa] = {}
        self._unidades: dict[str, Unidad] = {}

    # ── Consulta ───────────────────────────────────────────────

    @property
    def bases(self) -> tuple[BaseOperativa, ...]:
        return tuple(self._bases.values())

    @property
    def unidades(self) -> tuple[Unidad, ...]:
        return tuple(self._unidades.values())

    def unidad(self, unidad_id: str) -> Unidad:
        if unidad_id not in self._unidades:
            raise NoEncontrado(f"No existe la unidad {unidad_id}")
        return self._unidades[unidad_id]

    def unidades_de(self, base_id: str) -> tuple[Unidad, ...]:
        return tuple(u for u in self._unidades.values() if u.base_id == base_id)

    # ── Altas ──────────────────────────────────────────────────

    def registrar_base(self, base: BaseOperativa) -> None:
        if base.id in self._bases:
            raise RecursoDuplicado(f"Ya existe la base {base.id}")
        self._bases[base.id] = base

    def incorporar_unidad(self, unidad: Unidad, actor_id: str, fecha_hora: datetime) -> None:
        if unidad.base_id not in self._bases:
            raise NoEncontrado(f"No existe la base {unidad.base_id}")
        if unidad.id in self._unidades:
            raise RecursoDuplicado(f"Ya existe la unidad {unidad.id}")
        for persona in unidad.personal:
            self._exigir_persona_libre(persona.id, None)
        self._exigir_vehiculo_libre(unidad.vehiculo.id, None)
        for equipo in unidad.equipamiento:
            self._exigir_equipo_libre(equipo.id, None)
        unidad.registrar_alta(actor_id, fecha_hora)  # si falla, la flota no cambió
        self._unidades[unidad.id] = unidad

    # ── Cambios que necesitan mirar a las demás unidades ───────

    def incorporar_personal(self, unidad_id: str, persona: Persona, actor_id: str, fecha_hora: datetime) -> None:
        unidad = self.unidad(unidad_id)
        self._exigir_persona_libre(persona.id, unidad_id)
        unidad.incorporar_personal(persona, actor_id, fecha_hora)

    def cambiar_vehiculo(self, unidad_id: str, vehiculo: Vehiculo, actor_id: str, fecha_hora: datetime) -> None:
        unidad = self.unidad(unidad_id)
        self._exigir_vehiculo_libre(vehiculo.id, unidad_id)
        unidad.cambiar_vehiculo(vehiculo, actor_id, fecha_hora)

    def incorporar_equipo(self, unidad_id: str, equipo: Equipo, actor_id: str, fecha_hora: datetime) -> None:
        unidad = self.unidad(unidad_id)
        self._exigir_equipo_libre(equipo.id, unidad_id)
        unidad.incorporar_equipo(equipo, actor_id, fecha_hora)

    # ── Unicidad entre unidades (§5.2) ─────────────────────────

    def _exigir_persona_libre(self, persona_id: str, salvo_unidad_id: str | None) -> None:
        for u in self._unidades.values():
            if u.id != salvo_unidad_id and u.tiene_persona(persona_id):
                raise RecursoDuplicado(f"{persona_id} ya integra la unidad {u.id}")

    def _exigir_vehiculo_libre(self, vehiculo_id: str, salvo_unidad_id: str | None) -> None:
        for u in self._unidades.values():
            if u.id != salvo_unidad_id and u.usa_vehiculo(vehiculo_id):
                raise RecursoDuplicado(f"El vehículo {vehiculo_id} ya está en la unidad {u.id}")

    def _exigir_equipo_libre(self, equipo_id: str, salvo_unidad_id: str | None) -> None:
        for u in self._unidades.values():
            if u.id != salvo_unidad_id and u.tiene_equipo(equipo_id):
                raise RecursoDuplicado(f"El equipo {equipo_id} ya está en la unidad {u.id}")
