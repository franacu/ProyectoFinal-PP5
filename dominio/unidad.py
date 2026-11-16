"""Unidad de respuesta (§5.2, §8.4).

Decisiones:
- La CONDICIÓN DE SERVICIO (habilitada / en mantenimiento / fuera de servicio) es un
  State: cada condición decide si la unidad puede recibir una misión.
- El COMPROMISO con una misión es otra cosa (§8.4): se guarda aparte y se consulta
  con operaciones, no con un booleano expuesto.
- Una unidad comprometida no se modifica administrativamente: todos los mutadores
  empiezan por `_exigir_modificable()` (falla antes de tocar nada).
- La asignación se verifica acá, delegando en la misión: la misión sabe qué pide
  (vehículo, puestos, equipo) y la unidad sabe qué tiene.
- Las altas y cambios de recursos deben pasar por Flota, que es quien garantiza que
  ninguna persona, vehículo o equipo esté en dos unidades (§5.2).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import TYPE_CHECKING

from dominio.catalogos import CondicionOperativa, CondicionServicio
from dominio.equipamiento import Equipo
from dominio.errores import (
    NoEncontrado,
    NoEsJefeDeLaUnidad,
    RecursoDuplicado,
    RecursoInvalido,
    UnidadComprometida,
    UnidadNoHabilitada,
    UnidadOcupada,
)
from dominio.historial import Operacion, Registro
from dominio.personal import Persona
from dominio.vehiculos import Vehiculo
from dominio.valores import hay_texto

if TYPE_CHECKING:
    from dominio.mision import Mision


# ── Condición de servicio (State) ─────────────────────────────

class _Condicion(ABC):
    etiqueta: CondicionServicio

    @abstractmethod
    def verificar_habilitada(self) -> None:
        """No hace nada si la unidad puede recibir misiones; si no, lanza UnidadNoHabilitada."""


class _Habilitada(_Condicion):
    etiqueta = CondicionServicio.HABILITADA

    def verificar_habilitada(self) -> None:
        pass


class _EnMantenimiento(_Condicion):
    etiqueta = CondicionServicio.EN_MANTENIMIENTO

    def verificar_habilitada(self) -> None:
        raise UnidadNoHabilitada("La unidad está en mantenimiento")


class _FueraDeServicio(_Condicion):
    etiqueta = CondicionServicio.FUERA_DE_SERVICIO

    def verificar_habilitada(self) -> None:
        raise UnidadNoHabilitada("La unidad está fuera de servicio")


_HABILITADA, _EN_MANTENIMIENTO, _FUERA_DE_SERVICIO = _Habilitada(), _EnMantenimiento(), _FueraDeServicio()


# ── Entidad ───────────────────────────────────────────────────

class Unidad:
    def __init__(
        self,
        unidad_id: str,
        base_id: str,
        jefe: Persona,
        vehiculo: Vehiculo,
        personal: tuple[Persona, ...] = (),
        equipamiento: tuple[Equipo, ...] = (),
    ) -> None:
        if not hay_texto(unidad_id) or not hay_texto(base_id):
            raise RecursoInvalido("La unidad necesita identificación y base operativa")
        if jefe is None or vehiculo is None:
            raise RecursoInvalido("La unidad necesita un jefe y un vehículo")
        dotacion = (jefe, *personal)
        if len({p.id for p in dotacion}) != len(dotacion):
            raise RecursoDuplicado("Una persona no puede figurar dos veces en la unidad")
        if len({e.id for e in equipamiento}) != len(equipamiento):
            raise RecursoDuplicado("Un equipo no puede figurar dos veces en la unidad")
        self._id = unidad_id
        self._base_id = base_id
        self._jefe_id = jefe.id
        self._personal: dict[str, Persona] = {p.id: p for p in dotacion}  # el jefe integra la dotación
        self._vehiculo = vehiculo
        self._equipamiento: dict[str, Equipo] = {e.id: e for e in equipamiento}
        self._condicion: _Condicion = _HABILITADA
        self._mision_id: str | None = None
        self._registros: list[Registro] = []

    # ── Lectura ────────────────────────────────────────────────

    @property
    def id(self) -> str:
        return self._id

    @property
    def base_id(self) -> str:
        return self._base_id

    @property
    def jefe(self) -> Persona:
        return self._personal[self._jefe_id]

    @property
    def personal(self) -> tuple[Persona, ...]:
        """Toda la dotación, jefe incluido (se cuenta una sola vez)."""
        return tuple(self._personal.values())

    @property
    def vehiculo(self) -> Vehiculo:
        return self._vehiculo

    @property
    def equipamiento(self) -> tuple[Equipo, ...]:
        return tuple(self._equipamiento.values())

    @property
    def condicion(self) -> CondicionServicio:
        return self._condicion.etiqueta

    @property
    def mision_comprometida_id(self) -> str | None:
        """Id de la misión que la reserva o la ejecuta; None si está libre."""
        return self._mision_id

    @property
    def registros(self) -> tuple[Registro, ...]:
        return tuple(self._registros)

    def tiene_persona(self, persona_id: str) -> bool:
        return persona_id in self._personal

    def usa_vehiculo(self, vehiculo_id: str) -> bool:
        return self._vehiculo.id == vehiculo_id

    def tiene_equipo(self, equipo_id: str) -> bool:
        return equipo_id in self._equipamiento

    def tiene_equipo_operativo(self, categoria) -> bool:
        return any(e.categoria is categoria and e.operativo for e in self._equipamiento.values())

    # ── Compromiso con misiones (§8.2, §8.3) ───────────────────

    def comprometer(self, mision: Mision) -> None:
        """Verifica TODAS las condiciones (§8.2, en orden) y recién después se reserva.

        Si algo falla se lanza el motivo y la unidad queda exactamente como estaba.
        """
        self._condicion.verificar_habilitada()
        if self._mision_id is not None:
            raise UnidadOcupada(f"La unidad {self._id} ya tiene la misión {self._mision_id}")
        self._vehiculo.verificar_operativo()
        mision.verificar_vehiculo(self._vehiculo)
        mision.verificar_personal(self.personal)
        mision.verificar_equipamiento(self)
        self._mision_id = mision.id

    def liberar(self, mision_id: str) -> None:
        """Recupera la disponibilidad (misión finalizada, cancelada, rechazada o reasignada)."""
        if self._mision_id != mision_id:
            raise UnidadComprometida(f"La unidad {self._id} no está comprometida con la misión {mision_id}")
        self._mision_id = None

    def exigir_jefe(self, persona_id: str) -> None:
        if persona_id != self._jefe_id:
            raise NoEsJefeDeLaUnidad(f"El usuario no es el jefe de la unidad {self._id}")

    # ── Administración de recursos (§2.4) ──────────────────────

    def incorporar_personal(self, persona: Persona, actor_id: str, fecha_hora: datetime) -> None:
        self._exigir_modificable()
        if persona.id in self._personal:
            raise RecursoDuplicado(f"{persona.id} ya integra la unidad")
        registro = Registro.de(actor_id, fecha_hora, Operacion.PERSONAL_INCORPORADO, self._id, persona.id)
        self._personal[persona.id] = persona
        self._registros.append(registro)

    def retirar_personal(self, persona_id: str, actor_id: str, fecha_hora: datetime) -> None:
        self._exigir_modificable()
        if persona_id not in self._personal:
            raise NoEncontrado(f"{persona_id} no integra la unidad")
        if persona_id == self._jefe_id:
            raise RecursoInvalido("El jefe no se retira: la unidad siempre necesita jefe")
        registro = Registro.de(actor_id, fecha_hora, Operacion.PERSONAL_RETIRADO, self._id, persona_id)
        del self._personal[persona_id]
        self._registros.append(registro)

    def cambiar_vehiculo(self, vehiculo: Vehiculo, actor_id: str, fecha_hora: datetime) -> None:
        self._exigir_modificable()
        registro = Registro.de(actor_id, fecha_hora, Operacion.VEHICULO_CAMBIADO, self._id, vehiculo.id,
                               vehiculo_anterior=self._vehiculo.id)
        self._vehiculo = vehiculo
        self._registros.append(registro)

    def cambiar_condicion_vehiculo(self, condicion: CondicionOperativa, actor_id: str,
                                   fecha_hora: datetime) -> None:
        self._exigir_modificable()
        nuevo = self._vehiculo.con_condicion(condicion)  # valida la condición antes de tocar
        registro = Registro.de(actor_id, fecha_hora, Operacion.VEHICULO_CONDICION_CAMBIADA, self._id,
                               nuevo.id, condicion=condicion.value)
        self._vehiculo = nuevo
        self._registros.append(registro)

    def incorporar_equipo(self, equipo: Equipo, actor_id: str, fecha_hora: datetime) -> None:
        self._exigir_modificable()
        if equipo.id in self._equipamiento:
            raise RecursoDuplicado(f"{equipo.id} ya integra la unidad")
        registro = Registro.de(actor_id, fecha_hora, Operacion.EQUIPO_INCORPORADO, self._id, equipo.id)
        self._equipamiento[equipo.id] = equipo
        self._registros.append(registro)

    def retirar_equipo(self, equipo_id: str, actor_id: str, fecha_hora: datetime) -> None:
        self._exigir_modificable()
        if equipo_id not in self._equipamiento:
            raise NoEncontrado(f"{equipo_id} no integra la unidad")
        registro = Registro.de(actor_id, fecha_hora, Operacion.EQUIPO_RETIRADO, self._id, equipo_id)
        del self._equipamiento[equipo_id]
        self._registros.append(registro)

    def cambiar_condicion_equipo(self, equipo_id: str, condicion: CondicionOperativa, actor_id: str,
                                 fecha_hora: datetime) -> None:
        self._exigir_modificable()
        if equipo_id not in self._equipamiento:
            raise NoEncontrado(f"{equipo_id} no integra la unidad")
        nuevo = self._equipamiento[equipo_id].con_condicion(condicion)
        registro = Registro.de(actor_id, fecha_hora, Operacion.EQUIPO_CONDICION_CAMBIADA, self._id,
                               equipo_id, condicion=condicion.value)
        self._equipamiento[equipo_id] = nuevo
        self._registros.append(registro)

    def declarar_en_mantenimiento(self, actor_id: str, fecha_hora: datetime) -> None:
        self._cambiar_condicion(_EN_MANTENIMIENTO, actor_id, fecha_hora)

    def declarar_fuera_de_servicio(self, actor_id: str, fecha_hora: datetime) -> None:
        self._cambiar_condicion(_FUERA_DE_SERVICIO, actor_id, fecha_hora)

    def restablecer_servicio(self, actor_id: str, fecha_hora: datetime) -> None:
        self._cambiar_condicion(_HABILITADA, actor_id, fecha_hora)

    def registrar_alta(self, actor_id: str, fecha_hora: datetime) -> None:
        """La flota la llama al incorporar la unidad: deja el primer registro de su historial."""
        self._registros.append(Registro.de(actor_id, fecha_hora, Operacion.UNIDAD_REGISTRADA, self._id,
                                           base=self._base_id))

    # ── Internos ───────────────────────────────────────────────

    def _cambiar_condicion(self, nueva: _Condicion, actor_id: str, fecha_hora: datetime) -> None:
        self._exigir_modificable()
        registro = Registro.de(actor_id, fecha_hora, Operacion.UNIDAD_CONDICION_CAMBIADA, self._id,
                               anterior=self._condicion.etiqueta.value, nueva=nueva.etiqueta.value)
        self._condicion = nueva
        self._registros.append(registro)

    def _exigir_modificable(self) -> None:
        if self._mision_id is not None:
            raise UnidadComprometida(
                f"La unidad {self._id} está comprometida con la misión {self._mision_id}: no se modifica")
