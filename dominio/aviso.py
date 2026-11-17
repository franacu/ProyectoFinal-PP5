"""Aviso y sus objetos valor (§2.1, §7.1).

Decisiones:
- Aviso es una ENTIDAD: tiene identidad y cambia de estado.
- Ubicacion, Nota y Descarte son OBJETOS VALOR: inmutables (frozen),
  se validan al nacer y no existen a medias.
- El comportamiento que depende del estado vive en el estado (patrón State):
  el aviso le delega y no pregunta "¿estás pendiente?".
- Las fechas entran como parámetro: el dominio nunca llama a datetime.now().
- Cada operación valida TODO antes de modificar algo (R6).
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from dominio.catalogos import Gravedad, TipoSituacion
from dominio.emergencia import Emergencia
from dominio.errores import (
    AvisoNoPendiente,
    DatoDeAvisoInvalido,
    DescarteInvalido,
    JustificacionVacia,
    NotaDeOtroAutor,
    NotaInvalida,
)
from dominio.historial import Operacion, Registro
from dominio.valores import Ubicacion, hay_texto  # Ubicacion se sigue exportando desde acá


# ── Valores ───────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class Nota:
    autor_id: str
    texto: str
    fecha_hora: datetime

    def __post_init__(self) -> None:
        if not hay_texto(self.autor_id):
            raise NotaInvalida("La nota necesita un autor")
        if not hay_texto(self.texto):
            raise NotaInvalida("La nota no puede estar vacía")
        if self.fecha_hora is None:
            raise NotaInvalida("La nota necesita fecha y hora")


@dataclass(frozen=True, slots=True)
class Descarte:
    operador_id: str
    justificacion: str
    fecha_hora: datetime

    def __post_init__(self) -> None:
        if not hay_texto(self.justificacion):
            raise JustificacionVacia("Descartar exige una justificación")
        if not hay_texto(self.operador_id):
            raise DescarteInvalido("El descarte necesita un operador")
        if self.fecha_hora is None:
            raise DescarteInvalido("El descarte necesita fecha y hora")


# ── Estados del aviso (State) ─────────────────────────────────

class EstadoAviso(Enum):
    """Nombre público y serializable del estado (para la API y para Mongo)."""

    PENDIENTE = "pendiente"
    ACEPTADO = "aceptado"
    DESCARTADO = "descartado"


class _Estado(ABC):
    """Cada estado decide qué operaciones admite. El Aviso solo le delega."""

    etiqueta: EstadoAviso

    @abstractmethod
    def permitir_nota(self) -> None:
        """No hace nada si admite notas; si no, lanza AvisoNoPendiente."""

    @abstractmethod
    def descartar(self) -> _Estado:
        """Devuelve el estado siguiente, o lanza AvisoNoPendiente."""

    @abstractmethod
    def aceptar(self) -> _Estado:
        """Devuelve el estado siguiente, o lanza AvisoNoPendiente."""

    @abstractmethod
    def validar_descarte(self, descarte: Descarte | None) -> None:
        """Coherencia estado/descarte al reconstruir un aviso."""


class _Pendiente(_Estado):
    etiqueta = EstadoAviso.PENDIENTE

    def permitir_nota(self) -> None:
        pass

    def descartar(self) -> _Estado:
        return _DESCARTADO

    def aceptar(self) -> _Estado:
        return _ACEPTADO

    def validar_descarte(self, descarte: Descarte | None) -> None:
        if descarte is not None:
            raise DatoDeAvisoInvalido("Un aviso pendiente no tiene descarte")


class _Aceptado(_Estado):
    etiqueta = EstadoAviso.ACEPTADO

    def permitir_nota(self) -> None:
        raise AvisoNoPendiente("Un aviso aceptado no puede agregar notas")

    def descartar(self) -> _Estado:
        raise AvisoNoPendiente("Un aviso aceptado no puede evaluarse")

    def aceptar(self) -> _Estado:
        raise AvisoNoPendiente("Un aviso aceptado ya originó su emergencia")

    def validar_descarte(self, descarte: Descarte | None) -> None:
        if descarte is not None:
            raise DatoDeAvisoInvalido("Un aviso aceptado no tiene descarte")


class _Descartado(_Estado):
    etiqueta = EstadoAviso.DESCARTADO

    def permitir_nota(self) -> None:
        raise AvisoNoPendiente("Un aviso descartado no puede agregar notas")

    def descartar(self) -> _Estado:
        raise AvisoNoPendiente("Un aviso descartado no puede evaluarse")

    def aceptar(self) -> _Estado:
        raise AvisoNoPendiente("Un aviso descartado no puede aceptarse")

    def validar_descarte(self, descarte: Descarte | None) -> None:
        if descarte is None:
            raise DatoDeAvisoInvalido("Un aviso descartado conserva su descarte")


_PENDIENTE, _ACEPTADO, _DESCARTADO = _Pendiente(), _Aceptado(), _Descartado()
_ESTADO_POR_ETIQUETA = {e.etiqueta: e for e in (_PENDIENTE, _ACEPTADO, _DESCARTADO)}


# ── Entidad ───────────────────────────────────────────────────

class Aviso:
    def __init__(
        self,
        reportante_id: str,
        ubicacion: Ubicacion,
        tipo: TipoSituacion,
        gravedad_estimada: Gravedad,
        descripcion: str,
        registrado_en: datetime,
        aviso_id: str | None = None,
    ) -> None:
        _validar_datos(reportante_id, ubicacion, tipo, gravedad_estimada, descripcion, registrado_en)
        self._id = aviso_id or str(uuid.uuid4())
        self._reportante_id = reportante_id
        self._ubicacion = ubicacion
        self._tipo = tipo
        self._gravedad_estimada = gravedad_estimada
        self._descripcion = descripcion.strip()
        self._registrado_en = registrado_en
        self._estado: _Estado = _PENDIENTE  # R1: todo aviso nace pendiente
        self._notas: list[Nota] = []
        self._descarte: Descarte | None = None
        self._registros: list[Registro] = [
            Registro.de(reportante_id, registrado_en, Operacion.AVISO_REGISTRADO, self._id,
                        tipo=tipo.value, gravedad=gravedad_estimada.name.lower())
        ]

    @classmethod
    def restaurar(
        cls,
        *,
        aviso_id: str,
        reportante_id: str,
        ubicacion: Ubicacion,
        tipo: TipoSituacion,
        gravedad_estimada: Gravedad,
        descripcion: str,
        registrado_en: datetime,
        estado: EstadoAviso,
        notas: tuple[Nota, ...] = (),
        descarte: Descarte | None = None,
        registros: tuple[Registro, ...] = (),
    ) -> Aviso:
        """Reconstruye un aviso guardado. Recibe solo objetos del dominio.

        La lectura de la base (versión del documento, nombres de campos) la resuelve
        el esquema de persistencia (app/avisos/esquema_mongo.py), no este método.

        También permite armar un aviso ACEPTADO sin implementar todavía
        la operación aceptar (escenario 9 del avance).
        """
        if estado not in _ESTADO_POR_ETIQUETA:
            raise DatoDeAvisoInvalido(f"Estado desconocido: {estado!r}")
        nuevo_estado = _ESTADO_POR_ETIQUETA[estado]
        nuevo_estado.validar_descarte(descarte)
        aviso = cls(reportante_id, ubicacion, tipo, gravedad_estimada, descripcion, registrado_en, aviso_id)
        aviso._estado = nuevo_estado
        aviso._notas = list(notas)
        aviso._descarte = descarte
        if registros:
            aviso._registros = list(registros)
        return aviso

    # ── Comportamiento ─────────────────────────────────────────

    def agregar_nota(self, autor_id: str, texto: str, fecha_hora: datetime) -> Nota:
        """R2, R3, R5, R6 y §2.1 (solo el reportante)."""
        self._estado.permitir_nota()
        if autor_id != self._reportante_id:
            raise NotaDeOtroAutor("Solo el reportante del aviso puede agregarle notas")
        nota = Nota(autor_id, texto, fecha_hora)  # valida antes de tocar la lista
        registro = Registro.de(autor_id, fecha_hora, Operacion.NOTA_AGREGADA, self._id)
        self._notas.append(nota)
        self._registros.append(registro)
        return nota

    def descartar(self, operador_id: str, justificacion: str, fecha_hora: datetime) -> None:
        """R4, R5, R6."""
        siguiente = self._estado.descartar()  # lanza si ya no está pendiente
        descarte = Descarte(operador_id, justificacion, fecha_hora)
        registro = Registro.de(operador_id, fecha_hora, Operacion.AVISO_DESCARTADO, self._id,
                               justificacion=descarte.justificacion)
        # recién acá cambia el objeto: todo lo que podía fallar ya pasó
        self._descarte = descarte
        self._estado = siguiente
        self._registros.append(registro)

    def aceptar(self, operador_id: str, tipo: TipoSituacion, gravedad: Gravedad,
                fecha_hora: datetime) -> Emergencia:
        """§2.2, §7.1: acepta el aviso, confirma o corrige tipo y gravedad y origina UNA emergencia.

        Los datos originales del aviso no se pisan: la emergencia guarda los confirmados.
        """
        siguiente = self._estado.aceptar()  # lanza si ya no está pendiente
        emergencia = Emergencia(self._id, self._reportante_id, self._ubicacion, tipo, gravedad,
                                fecha_hora, operador_id)  # valida todo antes de que cambie el aviso
        registro = Registro.de(operador_id, fecha_hora, Operacion.AVISO_ACEPTADO, self._id, emergencia.id,
                               tipo=tipo.value, gravedad=gravedad.name.lower())
        self._estado = siguiente
        self._registros.append(registro)
        return emergencia

    # ── Lectura (sin setters: nadie cambia el aviso desde afuera) ─

    @property
    def id(self) -> str:
        return self._id

    @property
    def reportante_id(self) -> str:
        return self._reportante_id

    @property
    def ubicacion(self) -> Ubicacion:
        return self._ubicacion

    @property
    def tipo(self) -> TipoSituacion:
        return self._tipo

    @property
    def gravedad_estimada(self) -> Gravedad:
        return self._gravedad_estimada

    @property
    def descripcion(self) -> str:
        return self._descripcion

    @property
    def registrado_en(self) -> datetime:
        return self._registrado_en

    @property
    def estado(self) -> EstadoAviso:
        """Solo el nombre del estado: el objeto estado no sale del aviso."""
        return self._estado.etiqueta

    @property
    def notas(self) -> tuple[Nota, ...]:
        """Tupla: aviso.notas.append(...) no existe, R2 no se puede saltear."""
        return tuple(self._notas)

    @property
    def descarte(self) -> Descarte | None:
        return self._descarte

    @property
    def registros(self) -> tuple[Registro, ...]:
        """Historial inmutable del aviso (§9)."""
        return tuple(self._registros)


def _validar_datos(reportante_id, ubicacion, tipo, gravedad, descripcion, registrado_en) -> None:
    if not hay_texto(reportante_id):
        raise DatoDeAvisoInvalido("El aviso necesita un reportante")
    if ubicacion is None:
        raise DatoDeAvisoInvalido("El aviso necesita una ubicación")
    if not TipoSituacion.contiene(tipo):
        raise DatoDeAvisoInvalido(f"Tipo de situación fuera de catálogo: {tipo!r}")
    if not Gravedad.contiene(gravedad):
        raise DatoDeAvisoInvalido(f"Gravedad fuera de catálogo: {gravedad!r}")
    if not hay_texto(descripcion):
        raise DatoDeAvisoInvalido("El aviso necesita una descripción")
    if registrado_en is None:
        raise DatoDeAvisoInvalido("El aviso necesita fecha y hora de registro")
