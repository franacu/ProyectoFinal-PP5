"""Emergencia (§7.2, §4, §8).

Es la raíz de agregado de sus misiones: toda operación sobre una misión pasa por
la emergencia, que (1) exige estar abierta, (2) delega en la misión, y (3) recién
cuando la misión aceptó la operación deja el registro histórico. Una operación
rechazada no deja cambios ni registros (PV18).

Las misiones salen de la emergencia como VistaMision (foto de solo lectura): nadie
puede saltearse la emergencia llamando a mision.cancelar() desde afuera.
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from collections.abc import Iterable
from datetime import datetime
from enum import Enum

from dominio.catalogos import Gravedad, ResultadoMision, TipoSituacion
from dominio.errores import (
    AceptacionInvalida,
    EmergenciaCerrada,
    NoEncontrado,
    SinMisionExitosa,
)
from dominio.historial import Operacion, Registro
from dominio.mision import Mision, VistaMision
from dominio.unidad import Unidad
from dominio.valores import Ubicacion, hay_texto


class EstadoEmergencia(Enum):
    ABIERTA = "abierta"
    CERRADA = "cerrada"


class _Estado(ABC):
    etiqueta: EstadoEmergencia

    @abstractmethod
    def permitir_modificaciones(self) -> None:
        """No hace nada si está abierta; si no, lanza EmergenciaCerrada."""

    @abstractmethod
    def cerrar(self, misiones: Iterable[Mision]) -> _Estado:
        """Devuelve el estado siguiente o lanza el motivo por el que no puede cerrarse."""


class _Abierta(_Estado):
    etiqueta = EstadoEmergencia.ABIERTA

    def permitir_modificaciones(self) -> None:
        pass

    def cerrar(self, misiones: Iterable[Mision]) -> _Estado:
        misiones = tuple(misiones)
        for mision in misiones:
            mision.verificar_concluida()          # pendiente/asignada/en ejecución impiden cerrar
        if not any(m.es_exitosa() for m in misiones):  # sin misiones también cae acá
            raise SinMisionExitosa("Se necesita al menos una misión finalizada con resultado satisfactorio")
        return _CERRADA


class _Cerrada(_Estado):
    etiqueta = EstadoEmergencia.CERRADA

    def permitir_modificaciones(self) -> None:
        raise EmergenciaCerrada("Una emergencia cerrada no admite misiones ni modificaciones operativas")

    def cerrar(self, misiones: Iterable[Mision]) -> _Estado:
        raise EmergenciaCerrada("La emergencia ya está cerrada")


_ABIERTA, _CERRADA = _Abierta(), _Cerrada()


class Emergencia:
    def __init__(
        self,
        aviso_id: str,
        reportante_id: str,
        ubicacion: Ubicacion,
        tipo: TipoSituacion,
        gravedad: Gravedad,
        creada_en: datetime,
        operador_id: str,
        emergencia_id: str | None = None,
    ) -> None:
        if not hay_texto(aviso_id) or not hay_texto(reportante_id) or ubicacion is None:
            raise AceptacionInvalida("La emergencia necesita aviso de origen, reportante y ubicación")
        if not TipoSituacion.contiene(tipo) or not Gravedad.contiene(gravedad):
            raise AceptacionInvalida("Tipo de situación o gravedad fuera de catálogo")
        if not hay_texto(operador_id) or creada_en is None:
            raise AceptacionInvalida("La emergencia necesita operador y fecha de aceptación")
        self._id = emergencia_id or str(uuid.uuid4())
        self._aviso_id = aviso_id
        self._reportante_id = reportante_id
        self._ubicacion = ubicacion
        self._tipo = tipo
        self._gravedad = gravedad
        self._creada_en = creada_en
        self._estado: _Estado = _ABIERTA
        self._misiones: dict[str, Mision] = {}
        self._registros: list[Registro] = [
            Registro.de(operador_id, creada_en, Operacion.EMERGENCIA_CREADA, self._id, aviso_id,
                        tipo=tipo.value, gravedad=gravedad.name.lower())
        ]

    # ── Misiones: operador (§2.2) ──────────────────────────────

    def crear_mision(self, mision: Mision, operador_id: str, fecha_hora: datetime) -> None:
        self._estado.permitir_modificaciones()
        mision.verificar_situacion(self._tipo)               # §6.4
        registro = Registro.de(operador_id, fecha_hora, Operacion.MISION_CREADA, self._id, mision.id,
                               tipo=mision.tipo.value)
        self._misiones[mision.id] = mision
        self._registros.append(registro)

    def asignar_mision(self, mision_id: str, unidad: Unidad, operador_id: str, fecha_hora: datetime) -> None:
        self._estado.permitir_modificaciones()                # 1. emergencia abierta
        mision = self._mision(mision_id)
        registro = Registro.de(operador_id, fecha_hora, Operacion.MISION_ASIGNADA, self._id, mision_id,
                               unidad.id)
        mision.asignar(unidad)                               # 2–7. estado, unidad, vehículo, personal, equipo
        self._registros.append(registro)

    def reasignar_mision(self, mision_id: str, unidad_nueva: Unidad, operador_id: str,
                         fecha_hora: datetime) -> None:
        self._estado.permitir_modificaciones()
        mision = self._mision(mision_id)
        anterior = mision.unidad_id
        mision.reasignar(unidad_nueva)
        self._registros.append(Registro.de(
            operador_id, fecha_hora, Operacion.MISION_REASIGNADA, self._id, mision_id,
            unidad_anterior=str(anterior), unidad_nueva=unidad_nueva.id))

    def cancelar_mision(self, mision_id: str, operador_id: str, fecha_hora: datetime) -> None:
        self._estado.permitir_modificaciones()
        mision = self._mision(mision_id)
        unidad = mision.unidad_id
        registro = Registro.de(operador_id, fecha_hora, Operacion.MISION_CANCELADA, self._id, mision_id,
                               unidad_liberada=str(unidad))
        mision.cancelar()
        self._registros.append(registro)

    # ── Misiones: jefe de unidad (§2.3) ────────────────────────

    def rechazar_mision(self, mision_id: str, jefe_id: str, justificacion: str, fecha_hora: datetime) -> None:
        self._estado.permitir_modificaciones()
        mision = self._mision(mision_id)
        unidad = mision.unidad_id
        registro = Registro.de(jefe_id, fecha_hora, Operacion.MISION_RECHAZADA, self._id, mision_id,
                               str(unidad), justificacion=justificacion)
        mision.rechazar(jefe_id, justificacion)
        self._registros.append(registro)

    def iniciar_mision(self, mision_id: str, jefe_id: str, fecha_hora: datetime) -> None:
        self._estado.permitir_modificaciones()
        mision = self._mision(mision_id)
        registro = Registro.de(jefe_id, fecha_hora, Operacion.MISION_INICIADA, self._id, mision_id,
                               str(mision.unidad_id))
        mision.iniciar(jefe_id)
        self._registros.append(registro)

    def registrar_novedad(self, mision_id: str, jefe_id: str, texto: str, fecha_hora: datetime) -> None:
        self._estado.permitir_modificaciones()
        mision = self._mision(mision_id)
        mision.registrar_novedad(jefe_id, texto, fecha_hora)
        self._registros.append(Registro.de(jefe_id, fecha_hora, Operacion.MISION_NOVEDAD, self._id,
                                           mision_id, novedad=texto))

    def finalizar_mision(self, mision_id: str, jefe_id: str, resultado: ResultadoMision, tareas: str,
                         fecha_hora: datetime) -> None:
        self._estado.permitir_modificaciones()
        mision = self._mision(mision_id)
        unidad = mision.unidad_id
        mision.finalizar(jefe_id, resultado, tareas, fecha_hora)
        self._registros.append(Registro.de(jefe_id, fecha_hora, Operacion.MISION_FINALIZADA, self._id,
                                           mision_id, str(unidad), resultado=resultado.value,
                                           tareas=tareas))

    # ── Cierre: supervisor (§7.2) ──────────────────────────────

    def cerrar(self, supervisor_id: str, fecha_hora: datetime) -> None:
        siguiente = self._estado.cerrar(self._misiones.values())
        registro = Registro.de(supervisor_id, fecha_hora, Operacion.EMERGENCIA_CERRADA, self._id)
        self._estado = siguiente
        self._registros.append(registro)

    # ── Lectura ────────────────────────────────────────────────

    @property
    def id(self) -> str:
        return self._id

    @property
    def aviso_id(self) -> str:
        return self._aviso_id

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
    def gravedad(self) -> Gravedad:
        """Gravedad CONFIRMADA por el operador al aceptar el aviso."""
        return self._gravedad

    @property
    def creada_en(self) -> datetime:
        """Momento de aceptación del aviso (desempata la prioridad, §4)."""
        return self._creada_en

    @property
    def estado(self) -> EstadoEmergencia:
        return self._estado.etiqueta

    @property
    def misiones(self) -> tuple[VistaMision, ...]:
        return tuple(m.vista() for m in self._misiones.values())

    @property
    def registros(self) -> tuple[Registro, ...]:
        return tuple(self._registros)

    @property
    def clave_de_prioridad(self) -> tuple[int, datetime]:
        """Menor clave = más urgente: gravedad Alta primero y, a igual gravedad, la más antigua."""
        return (-self._gravedad.value, self._creada_en)

    def _mision(self, mision_id: str) -> Mision:
        if mision_id not in self._misiones:
            raise NoEncontrado(f"La emergencia no tiene la misión {mision_id}")
        return self._misiones[mision_id]


def abiertas_por_prioridad(emergencias: Iterable[Emergencia]) -> tuple[Emergencia, ...]:
    """Emergencias abiertas ordenadas Alta, Media, Baja y, dentro de cada nivel, por aceptación (PV03)."""
    abiertas = (e for e in emergencias if e.estado is EstadoEmergencia.ABIERTA)
    return tuple(sorted(abiertas, key=lambda e: e.clave_de_prioridad))
