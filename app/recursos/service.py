"""Casos de uso del responsable de recursos (§2.4).

Igual que en avisos: cargar la flota, pedirle la operación al dominio y, si el
dominio la acepta, guardar lo que cambió. Las altas y los cambios que podrían
duplicar un recurso pasan por la Flota, que controla la unicidad entre unidades.
"""

from collections.abc import Callable

from app.internal.reloj import Reloj
from app.recursos.repository import RepositorioFlota
from dominio.catalogos import CondicionOperativa, CondicionServicio
from dominio.equipamiento import Equipo
from dominio.flota import BaseOperativa
from dominio.personal import Persona
from dominio.unidad import Unidad
from dominio.valores import Ubicacion
from dominio.vehiculos import Vehiculo

# Privado: qué operación del dominio corresponde a cada condición de servicio pedida.
_CAMBIO_DE_CONDICION: dict[CondicionServicio, Callable] = {
    CondicionServicio.HABILITADA: Unidad.restablecer_servicio,
    CondicionServicio.EN_MANTENIMIENTO: Unidad.declarar_en_mantenimiento,
    CondicionServicio.FUERA_DE_SERVICIO: Unidad.declarar_fuera_de_servicio,
}


class ServicioRecursos:
    def __init__(self, flota: RepositorioFlota, reloj: Reloj) -> None:
        self._flota = flota
        self._reloj = reloj

    # ── Consultas ──────────────────────────────────────────────

    def bases(self) -> tuple[BaseOperativa, ...]:
        return self._flota.cargar().bases

    def unidades(self) -> tuple[Unidad, ...]:
        return self._flota.cargar().unidades

    def unidad(self, unidad_id: str) -> Unidad:
        return self._flota.cargar().unidad(unidad_id)   # NoEncontrado → 404

    # ── Altas ──────────────────────────────────────────────────

    def registrar_base(self, base_id: str, nombre: str, ubicacion: Ubicacion) -> BaseOperativa:
        flota = self._flota.cargar()
        base = BaseOperativa(base_id, nombre, ubicacion)
        flota.registrar_base(base)
        self._flota.guardar_base(base)
        return base

    def registrar_unidad(self, actor_id: str, unidad_id: str, base_id: str, jefe: Persona, vehiculo: Vehiculo,
                         personal: tuple[Persona, ...], equipamiento: tuple[Equipo, ...]) -> Unidad:
        flota = self._flota.cargar()
        unidad = Unidad(unidad_id, base_id, jefe, vehiculo, personal, equipamiento)
        flota.incorporar_unidad(unidad, actor_id, self._reloj())
        self._flota.guardar_unidad(unidad)
        return unidad

    # ── Composición ────────────────────────────────────────────

    def incorporar_personal(self, actor_id: str, unidad_id: str, persona: Persona) -> Unidad:
        return self._operar(unidad_id, lambda flota, u, ahora:
                            flota.incorporar_personal(u.id, persona, actor_id, ahora))

    def retirar_personal(self, actor_id: str, unidad_id: str, persona_id: str) -> Unidad:
        return self._operar(unidad_id, lambda flota, u, ahora: u.retirar_personal(persona_id, actor_id, ahora))

    def cambiar_vehiculo(self, actor_id: str, unidad_id: str, vehiculo: Vehiculo) -> Unidad:
        return self._operar(unidad_id, lambda flota, u, ahora:
                            flota.cambiar_vehiculo(u.id, vehiculo, actor_id, ahora))

    def cambiar_condicion_vehiculo(self, actor_id: str, unidad_id: str, condicion: CondicionOperativa) -> Unidad:
        return self._operar(unidad_id, lambda flota, u, ahora:
                            u.cambiar_condicion_vehiculo(condicion, actor_id, ahora))

    def incorporar_equipo(self, actor_id: str, unidad_id: str, equipo: Equipo) -> Unidad:
        return self._operar(unidad_id, lambda flota, u, ahora:
                            flota.incorporar_equipo(u.id, equipo, actor_id, ahora))

    def retirar_equipo(self, actor_id: str, unidad_id: str, equipo_id: str) -> Unidad:
        return self._operar(unidad_id, lambda flota, u, ahora: u.retirar_equipo(equipo_id, actor_id, ahora))

    def cambiar_condicion_equipo(self, actor_id: str, unidad_id: str, equipo_id: str,
                                 condicion: CondicionOperativa) -> Unidad:
        return self._operar(unidad_id, lambda flota, u, ahora:
                            u.cambiar_condicion_equipo(equipo_id, condicion, actor_id, ahora))

    # ── Condición de servicio (§8.4) ───────────────────────────

    def cambiar_condicion(self, actor_id: str, unidad_id: str, condicion: CondicionServicio) -> Unidad:
        operacion = _CAMBIO_DE_CONDICION[condicion]
        return self._operar(unidad_id, lambda flota, u, ahora: operacion(u, actor_id, ahora))

    # ── Privado ────────────────────────────────────────────────

    def _operar(self, unidad_id: str, operacion: Callable) -> Unidad:
        """Privado: carga la flota, aplica la operación del dominio y guarda la unidad si no hubo error."""
        flota = self._flota.cargar()
        unidad = flota.unidad(unidad_id)
        operacion(flota, unidad, self._reloj())
        self._flota.guardar_unidad(unidad)
        return unidad
