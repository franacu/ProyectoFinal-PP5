"""Misiones (§6, §8).

Dos ejes de polimorfismo, cada uno resuelto SIN preguntar por tipo ni por estado:

1. TIPO de misión (Evacuacion, Rescate, AsistenciaSanitaria): cada clase sabe en qué
   situaciones se admite, qué puestos de personal pide, qué vehículo y qué equipo.
   La unidad le pregunta a la misión y el vehículo responde (doble despacho).
2. ESTADO de la misión (State): cada estado decide qué operaciones admite y a qué
   estado pasa. Lo que no admite se rechaza por defecto en la clase base.

La unidad asignada se guarda con Null Object (_SinUnidad / _ConUnidad): liberar la
unidad de una misión pendiente es "no hacer nada", sin un if.

Cada operación verifica TODO antes de modificar algo (§9, PV18).
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from dominio.catalogos import Competencia, CategoriaEquipo, ResultadoMision, TipoMision, TipoSituacion
from dominio.distribucion import existe_distribucion
from dominio.errores import (
    EquipamientoInsuficiente,
    JustificacionVacia,
    MisionEnEstadoInvalido,
    MisionIncompatible,
    MisionInvalida,
    MisionSinConcluir,
    NoEsJefeDeLaUnidad,
    PersonalInsuficiente,
    ResultadoInvalido,
)
from dominio.personal import Persona
from dominio.unidad import Unidad
from dominio.valores import es_entero_positivo, hay_texto
from dominio.vehiculos import Vehiculo


# ── Valores ───────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class Novedad:
    jefe_id: str
    texto: str
    fecha_hora: datetime

    def __post_init__(self) -> None:
        if not hay_texto(self.texto) or not hay_texto(self.jefe_id) or self.fecha_hora is None:
            raise MisionInvalida("La novedad necesita autor, texto y fecha")


@dataclass(frozen=True, slots=True)
class Resultado:
    """Lo que registra el jefe al finalizar (§2.3): resultado y tareas realizadas."""

    resultado: ResultadoMision
    tareas: str
    fecha_hora: datetime

    def __post_init__(self) -> None:
        if not ResultadoMision.contiene(self.resultado):
            raise ResultadoInvalido("Resultado fuera de catálogo")
        if not hay_texto(self.tareas):
            raise ResultadoInvalido("Finalizar exige describir las tareas realizadas")
        if self.fecha_hora is None:
            raise ResultadoInvalido("El resultado necesita fecha y hora")

    @property
    def satisfactorio(self) -> bool:
        return self.resultado is ResultadoMision.SATISFACTORIO


@dataclass(frozen=True, slots=True)
class VistaMision:
    """Foto de solo lectura de una misión: es lo que sale de la emergencia."""

    id: str
    tipo: TipoMision
    objetivo: str
    estado: EstadoMision
    unidad_id: str | None
    novedades: tuple[Novedad, ...]
    resultado: Resultado | None


# ── Estados (State) ───────────────────────────────────────────

class EstadoMision(Enum):
    """Nombre público y serializable del estado (§8.1)."""

    PENDIENTE = "pendiente"
    ASIGNADA = "asignada"
    EN_EJECUCION = "en_ejecucion"
    FINALIZADA = "finalizada"
    CANCELADA = "cancelada"


class _Estado(ABC):
    """Cada operación devuelve el estado siguiente. Lo que no se sobrescribe se rechaza."""

    etiqueta: EstadoMision

    def _no_admite(self, operacion: str) -> MisionEnEstadoInvalido:
        return MisionEnEstadoInvalido(f"Una misión {self.etiqueta.value} no puede {operacion}")

    def asignar(self) -> _Estado:
        raise self._no_admite("asignarse")

    def reasignar(self) -> _Estado:
        raise self._no_admite("reasignarse")

    def rechazar(self) -> _Estado:
        raise self._no_admite("rechazarse")

    def iniciar(self) -> _Estado:
        raise self._no_admite("iniciarse")

    def permitir_novedad(self) -> None:
        raise self._no_admite("registrar novedades")

    def finalizar(self) -> _Estado:
        raise self._no_admite("finalizarse")

    def cancelar(self) -> _Estado:
        raise self._no_admite("cancelarse")

    def verificar_concluida(self) -> None:
        raise MisionSinConcluir(f"Hay una misión {self.etiqueta.value}: debe finalizar o cancelarse")

    def exito(self, resultado: Resultado | None) -> bool:
        return False


class _Pendiente(_Estado):
    etiqueta = EstadoMision.PENDIENTE

    def asignar(self) -> _Estado:
        return _ASIGNADA

    def cancelar(self) -> _Estado:
        return _CANCELADA


class _Asignada(_Estado):
    etiqueta = EstadoMision.ASIGNADA

    def reasignar(self) -> _Estado:
        return _ASIGNADA

    def rechazar(self) -> _Estado:
        return _PENDIENTE

    def iniciar(self) -> _Estado:
        return _EN_EJECUCION

    def cancelar(self) -> _Estado:
        return _CANCELADA


class _EnEjecucion(_Estado):
    etiqueta = EstadoMision.EN_EJECUCION

    def permitir_novedad(self) -> None:
        pass

    def finalizar(self) -> _Estado:
        return _FINALIZADA


class _Finalizada(_Estado):
    etiqueta = EstadoMision.FINALIZADA

    def verificar_concluida(self) -> None:
        pass

    def exito(self, resultado: Resultado | None) -> bool:
        return resultado is not None and resultado.satisfactorio


class _Cancelada(_Estado):
    etiqueta = EstadoMision.CANCELADA

    def verificar_concluida(self) -> None:
        pass


_PENDIENTE, _ASIGNADA, _EN_EJECUCION = _Pendiente(), _Asignada(), _EnEjecucion()
_FINALIZADA, _CANCELADA = _Finalizada(), _Cancelada()


# ── Unidad asignada (Null Object) ─────────────────────────────

class _Asignacion(ABC):
    unidad_id: str | None

    @abstractmethod
    def liberar(self, mision_id: str) -> None: ...

    @abstractmethod
    def exigir_jefe(self, persona_id: str) -> None: ...


class _SinUnidad(_Asignacion):
    unidad_id = None

    def liberar(self, mision_id: str) -> None:
        pass

    def exigir_jefe(self, persona_id: str) -> None:
        raise NoEsJefeDeLaUnidad("La misión no tiene una unidad asignada")


class _ConUnidad(_Asignacion):
    def __init__(self, unidad: Unidad) -> None:
        self._unidad = unidad
        self.unidad_id = unidad.id

    def liberar(self, mision_id: str) -> None:
        self._unidad.liberar(mision_id)

    def exigir_jefe(self, persona_id: str) -> None:
        self._unidad.exigir_jefe(persona_id)


_SIN_UNIDAD = _SinUnidad()


# ── Misión (abstracta) ────────────────────────────────────────

class Mision(ABC):
    tipo: TipoMision
    situaciones_admitidas: frozenset[TipoSituacion]  # §6.4
    puestos: tuple[Competencia, ...]                # §6.1–6.3: un puesto = una persona distinta

    def __init__(self, objetivo: str, mision_id: str | None = None) -> None:
        if not hay_texto(objetivo):
            raise MisionInvalida("La misión necesita un objetivo")
        self._id = mision_id or str(uuid.uuid4())
        self._objetivo = objetivo.strip()
        self._estado: _Estado = _PENDIENTE
        self._asignacion: _Asignacion = _SIN_UNIDAD
        self._novedades: list[Novedad] = []
        self._resultado: Resultado | None = None

    # ── Lo que cada tipo de misión define ──────────────────────

    @abstractmethod
    def verificar_vehiculo(self, vehiculo: Vehiculo) -> None:
        """Doble despacho: el vehículo decide si sirve (o lanza VehiculoIncompatible)."""

    @abstractmethod
    def verificar_equipamiento(self, unidad: Unidad) -> None:
        """Lanza EquipamientoInsuficiente si falta un elemento operativo requerido."""

    def verificar_personal(self, personal: Sequence[Persona]) -> None:
        if not existe_distribucion(self.puestos, tuple(personal)):
            raise PersonalInsuficiente(
                f"No hay personas distintas que cubran: {', '.join(c.value for c in self.puestos)}")

    def verificar_situacion(self, situacion: TipoSituacion) -> None:
        if situacion not in self.situaciones_admitidas:
            raise MisionIncompatible(
                f"Una misión de {self.tipo.value} no está contemplada para {situacion.value}")

    def _exigir_equipo(self, unidad: Unidad, categoria: CategoriaEquipo) -> None:
        if not unidad.tiene_equipo_operativo(categoria):
            raise EquipamientoInsuficiente(f"Falta un {categoria.value} operativo")

    # ── Operaciones del operador (§2.2) ────────────────────────

    def asignar(self, unidad: Unidad) -> None:
        siguiente = self._estado.asignar()
        unidad.comprometer(self)          # verifica todo; si falla no cambió nada
        self._asignacion = _ConUnidad(unidad)
        self._estado = siguiente

    def reasignar(self, unidad_nueva: Unidad) -> None:
        siguiente = self._estado.reasignar()
        anterior = self._asignacion
        unidad_nueva.comprometer(self)    # si falla, la anterior sigue asignada y reservada
        anterior.liberar(self._id)
        self._asignacion = _ConUnidad(unidad_nueva)
        self._estado = siguiente

    def cancelar(self) -> None:
        siguiente = self._estado.cancelar()
        self._asignacion.liberar(self._id)
        self._asignacion = _SIN_UNIDAD
        self._estado = siguiente

    # ── Operaciones del jefe de la unidad (§2.3) ───────────────

    def rechazar(self, jefe_id: str, justificacion: str) -> None:
        siguiente = self._estado.rechazar()
        self._asignacion.exigir_jefe(jefe_id)
        if not hay_texto(justificacion):
            raise JustificacionVacia("Rechazar una misión exige una justificación")
        self._asignacion.liberar(self._id)
        self._asignacion = _SIN_UNIDAD
        self._estado = siguiente

    def iniciar(self, jefe_id: str) -> None:
        siguiente = self._estado.iniciar()
        self._asignacion.exigir_jefe(jefe_id)
        self._estado = siguiente

    def registrar_novedad(self, jefe_id: str, texto: str, fecha_hora: datetime) -> None:
        self._estado.permitir_novedad()
        self._asignacion.exigir_jefe(jefe_id)
        self._novedades.append(Novedad(jefe_id, texto, fecha_hora))

    def finalizar(self, jefe_id: str, resultado: ResultadoMision, tareas: str, fecha_hora: datetime) -> None:
        siguiente = self._estado.finalizar()
        self._asignacion.exigir_jefe(jefe_id)
        nuevo = Resultado(resultado, tareas, fecha_hora)   # se valida antes de liberar la unidad
        self._asignacion.liberar(self._id)
        self._resultado = nuevo
        self._estado = siguiente

    # ── Para la emergencia ─────────────────────────────────────

    def verificar_concluida(self) -> None:
        self._estado.verificar_concluida()

    def es_exitosa(self) -> bool:
        return self._estado.exito(self._resultado)

    # ── Lectura ────────────────────────────────────────────────

    @property
    def id(self) -> str:
        return self._id

    @property
    def estado(self) -> EstadoMision:
        return self._estado.etiqueta

    @property
    def unidad_id(self) -> str | None:
        return self._asignacion.unidad_id

    def vista(self) -> VistaMision:
        return VistaMision(self._id, self.tipo, self._objetivo, self.estado, self.unidad_id,
                           tuple(self._novedades), self._resultado)


# ── Los tres tipos de misión ──────────────────────────────────

class Evacuacion(Mision):
    """§6.1: traslada una cantidad de personas. Sin equipamiento especializado."""

    tipo = TipoMision.EVACUACION
    situaciones_admitidas = frozenset({TipoSituacion.INUNDACION, TipoSituacion.INCENDIO})
    puestos = (Competencia.CONDUCCION, Competencia.EVACUACION)

    def __init__(self, objetivo: str, cantidad_personas: int, mision_id: str | None = None) -> None:
        if not es_entero_positivo(cantidad_personas):
            raise MisionInvalida("La cantidad de personas a evacuar debe ser un entero positivo")
        super().__init__(objetivo, mision_id)
        self._cantidad = cantidad_personas

    @property
    def cantidad_personas(self) -> int:
        return self._cantidad

    def verificar_vehiculo(self, vehiculo: Vehiculo) -> None:
        vehiculo.verificar_evacuacion(self._cantidad)

    def verificar_equipamiento(self, unidad: Unidad) -> None:
        pass  # las evacuaciones no requieren equipamiento especializado (§5.5)


class Rescate(Mision):
    """§6.2: conductor + dos rescatistas distintos entre sí y un equipo de rescate operativo."""

    tipo = TipoMision.RESCATE
    situaciones_admitidas = frozenset(TipoSituacion)
    puestos = (Competencia.CONDUCCION, Competencia.RESCATE, Competencia.RESCATE)

    def verificar_vehiculo(self, vehiculo: Vehiculo) -> None:
        vehiculo.verificar_rescate()

    def verificar_equipamiento(self, unidad: Unidad) -> None:
        self._exigir_equipo(unidad, CategoriaEquipo.EQUIPO_DE_RESCATE)


class AsistenciaSanitaria(Mision):
    """§6.3: ambulancia, conductor, un integrante con primeros auxilios y un equipo sanitario."""

    tipo = TipoMision.ASISTENCIA_SANITARIA
    situaciones_admitidas = frozenset(TipoSituacion)
    puestos = (Competencia.CONDUCCION, Competencia.PRIMEROS_AUXILIOS)

    def verificar_vehiculo(self, vehiculo: Vehiculo) -> None:
        vehiculo.verificar_asistencia()

    def verificar_equipamiento(self, unidad: Unidad) -> None:
        self._exigir_equipo(unidad, CategoriaEquipo.EQUIPO_SANITARIO)
