"""Esquema de persistencia de la emergencia: documento de Mongo ⇄ Emergencia.

Versión 1: datos de la emergencia y su historial. Las misiones se agregarán en la
versión 2 del documento; los documentos de versión 1 se migrarán con una lista de
misiones vacía, sin tocar el dominio.

    {
      "_id": "…", "version": 1,
      "aviso_id": "…", "reportante_id": "…",
      "ubicacion": {"direccion": "…", "localidad": "…"},
      "tipo": "incendio", "gravedad": "alta",
      "creada_en": <fecha>, "estado": "abierta",
      "registros": [ … ]
    }
"""

from collections.abc import Mapping

from app.internal.esquema import (
    fecha_desde_documento,
    migrar,
    registro_a_documento,
    registro_desde_documento,
    ubicacion_a_documento,
    ubicacion_desde_documento,
)
from dominio.catalogos import Gravedad, TipoSituacion
from dominio.emergencia import Emergencia, EstadoEmergencia

VERSION_ESQUEMA = 1

_MIGRACIONES: dict = {}  # privado


def a_documento(emergencia: Emergencia) -> dict:
    return {
        "_id": emergencia.id,
        "version": VERSION_ESQUEMA,
        "aviso_id": emergencia.aviso_id,
        "reportante_id": emergencia.reportante_id,
        "ubicacion": ubicacion_a_documento(emergencia.ubicacion),
        "tipo": emergencia.tipo.value,
        "gravedad": emergencia.gravedad.name.lower(),
        "creada_en": emergencia.creada_en,
        "estado": emergencia.estado.value,
        "registros": [registro_a_documento(r) for r in emergencia.registros],
    }


def desde_documento(documento: Mapping) -> Emergencia:
    d = migrar(documento, VERSION_ESQUEMA, _MIGRACIONES, "emergencias")
    return Emergencia.restaurar(
        emergencia_id=d["_id"],
        aviso_id=d["aviso_id"],
        reportante_id=d["reportante_id"],
        ubicacion=ubicacion_desde_documento(d["ubicacion"]),
        tipo=TipoSituacion(d["tipo"]),
        gravedad=Gravedad[d["gravedad"].upper()],
        creada_en=fecha_desde_documento(d["creada_en"]),
        estado=EstadoEmergencia(d["estado"]),
        registros=tuple(registro_desde_documento(r) for r in d["registros"]),
    )
