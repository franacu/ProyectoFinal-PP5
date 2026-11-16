"""Aviso y sus objetos valor (§2.1, §7.1).

Decisiones:
- Aviso es una ENTIDAD: tiene identidad y cambia de estado.
- Ubicacion, Nota y Descarte son OBJETOS VALOR: inmutables (frozen),
  se validan al nacer y no existen a medias.
- El estado es un único atributo (EstadoAviso), no tres booleanos.
- Las fechas entran como parámetro: el dominio nunca llama a datetime.now().
- Cada operación valida TODO antes de modificar algo (R6).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from dominio.catalogos import Gravedad, TipoSituacion
from dominio.errores import (
    AvisoNoPendiente,
    DatoDeAvisoInvalido,
    JustificacionVacia,
    NotaInvalida,
)


class EstadoAviso(Enum):
    PENDIENTE = "pendiente"
    ACEPTADO = "aceptado"
    DESCARTADO = "descartado"


@dataclass(frozen=True, slots=True)
class Ubicacion:
    direccion: str
    localidad: str

    def __post_init__(self) -> None:
        if not self.direccion.strip() or not self.localidad.strip():
            raise DatoDeAvisoInvalido("La ubicación necesita dirección y localidad")


@dataclass(frozen=True, slots=True)
class Nota:
    autor_id: str
    texto: str
    fecha_hora: datetime

    def __post_init__(self) -> None:
        if not self.autor_id.strip():
            raise NotaInvalida("La nota necesita un autor")
        if not self.texto.strip():
            raise NotaInvalida("La nota no puede estar vacía")


@dataclass(frozen=True, slots=True)
class Descarte:
    operador_id: str
    justificacion: str
    fecha_hora: datetime

    def __post_init__(self) -> None:
        if not self.justificacion.strip():
            raise JustificacionVacia("Descartar exige una justificación")


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
        self._estado = EstadoAviso.PENDIENTE  # R1: todo aviso nace pendiente
        self._notas: list[Nota] = []
        self._descarte: Descarte | None = None

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
    ) -> Aviso:
        """Reconstruye un aviso ya existente (lo usará el repositorio Mongo).

        También permite armar un aviso ACEPTADO sin implementar todavía
        la operación aceptar (escenario 9 del avance).
        """
        if (estado is EstadoAviso.DESCARTADO) != (descarte is not None):
            raise DatoDeAvisoInvalido("Un aviso tiene descarte si y solo si está descartado")
        aviso = cls(reportante_id, ubicacion, tipo, gravedad_estimada, descripcion, registrado_en, aviso_id)
        aviso._estado = estado
        aviso._notas = list(notas)
        aviso._descarte = descarte
        return aviso

    # ── Comportamiento ─────────────────────────────────────────

    def agregar_nota(self, autor_id: str, texto: str, fecha_hora: datetime) -> Nota:
        """R2, R3, R5, R6."""
        self._exigir_pendiente("agregar notas")
        nota = Nota(autor_id, texto, fecha_hora)  # valida antes de tocar la lista
        self._notas.append(nota)
        return nota

    def descartar(self, operador_id: str, justificacion: str, fecha_hora: datetime) -> None:
        """R4, R5, R6."""
        self._exigir_pendiente("evaluarse")
        descarte = Descarte(operador_id, justificacion, fecha_hora)
        # recién acá cambia el objeto: todo lo que podía fallar ya pasó
        self._descarte = descarte
        self._estado = EstadoAviso.DESCARTADO

    def esta_pendiente(self) -> bool:
        return self._estado is EstadoAviso.PENDIENTE

    def _exigir_pendiente(self, operacion: str) -> None:
        if not self.esta_pendiente():
            raise AvisoNoPendiente(
                f"Un aviso {self._estado.value} no puede {operacion}"
            )

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
        return self._estado

    @property
    def notas(self) -> tuple[Nota, ...]:
        """Tupla: aviso.notas.append(...) no existe, R2 no se puede saltear."""
        return tuple(self._notas)

    @property
    def descarte(self) -> Descarte | None:
        return self._descarte


def _validar_datos(reportante_id, ubicacion, tipo, gravedad, descripcion, registrado_en) -> None:
    if not isinstance(reportante_id, str) or not reportante_id.strip():
        raise DatoDeAvisoInvalido("El aviso necesita un reportante")
    if not isinstance(ubicacion, Ubicacion):
        raise DatoDeAvisoInvalido("Ubicación inválida")
    if not isinstance(tipo, TipoSituacion):
        raise DatoDeAvisoInvalido(f"Tipo de situación fuera de catálogo: {tipo!r}")
    if not isinstance(gravedad, Gravedad):
        raise DatoDeAvisoInvalido(f"Gravedad fuera de catálogo: {gravedad!r}")
    if not isinstance(descripcion, str) or not descripcion.strip():
        raise DatoDeAvisoInvalido("El aviso necesita una descripción")
    if not isinstance(registrado_en, datetime):
        raise DatoDeAvisoInvalido("El aviso necesita fecha y hora de registro")
