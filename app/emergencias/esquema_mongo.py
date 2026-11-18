"""Esquema de persistencia de la emergencia: documento de Mongo ⇄ Emergencia.

Historia de versiones del documento:
- Versión 1: datos de la emergencia y su historial.
- Versión 2: agrega "misiones". Un documento de versión 1 se migra al leerlo con una
  lista de misiones vacía (_de_v1_a_v2). El dominio no cambió por esto.

    {
      "_id": "…", "version": 2,
      "aviso_id": "…", "reportante_id": "…",
      "ubicacion": {"direccion": "…", "localidad": "…"},
      "tipo": "incendio", "gravedad": "alta",
      "creada_en": <fecha>, "estado": "abierta",
      "misiones": [{"_id", "tipo", "objetivo", "estado", "unidad_id",
                    "datos_del_tipo": {"cantidad_personas": 30}?,
                    "novedades": [...], "resultado": null | {...}}],
      "registros": [ … ]
    }

Una misión guarda solo el identificador de su unidad. Al leer, la unidad se busca en
la flota ya cargada, para que la misión y la flota compartan el mismo objeto.
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
from app.recursos.fabricas import CLASE_DE_MISION
from dominio.catalogos import Gravedad, ResultadoMision, TipoMision, TipoSituacion
from dominio.emergencia import Emergencia, EstadoEmergencia
from dominio.errores import NoEncontrado
from dominio.mision import EstadoMision, Mision, Novedad, Resultado, VistaMision
from dominio.unidad import Unidad

VERSION_ESQUEMA = 2


def _de_v1_a_v2(documento: dict) -> dict:
    """Privada: la versión 1 no tenía misiones."""
    return documento | {"misiones": []}


_MIGRACIONES = {1: _de_v1_a_v2}  # privado


def _mision_a_documento(m: VistaMision) -> dict:
    """Privada."""
    return {
        "_id": m.id,
        "tipo": m.tipo.value,
        "objetivo": m.objetivo,
        "estado": m.estado.value,
        "unidad_id": m.unidad_id,
        "datos_del_tipo": dict(m.datos_del_tipo),
        "novedades": [{"jefe_id": n.jefe_id, "texto": n.texto, "fecha_hora": n.fecha_hora} for n in m.novedades],
        "resultado": None if m.resultado is None else {
            "resultado": m.resultado.resultado.value, "tareas": m.resultado.tareas,
            "fecha_hora": m.resultado.fecha_hora},
    }


def _mision_desde_documento(d: Mapping, unidades: Mapping[str, Unidad]) -> Mision:
    """Privada."""
    unidad = None
    if d.get("unidad_id") is not None:
        if d["unidad_id"] not in unidades:
            raise NoEncontrado(f"La misión {d['_id']} referencia la unidad inexistente {d['unidad_id']}")
        unidad = unidades[d["unidad_id"]]
    r = d.get("resultado")
    return CLASE_DE_MISION[TipoMision(d["tipo"])].restaurar(
        mision_id=d["_id"],
        objetivo=d["objetivo"],
        estado=EstadoMision(d["estado"]),
        unidad=unidad,
        novedades=tuple(Novedad(n["jefe_id"], n["texto"], fecha_desde_documento(n["fecha_hora"]))
                        for n in d.get("novedades", [])),
        resultado=None if r is None else Resultado(ResultadoMision(r["resultado"]), r["tareas"],
                                                   fecha_desde_documento(r["fecha_hora"])),
        **d.get("datos_del_tipo", {}),
    )


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
        "misiones": [_mision_a_documento(m) for m in emergencia.misiones],
        "registros": [registro_a_documento(r) for r in emergencia.registros],
    }


def desde_documento(documento: Mapping, unidades: Mapping[str, Unidad] | None = None) -> Emergencia:
    """`unidades`: las unidades de la flota cargada, por id (necesarias si hay misiones asignadas)."""
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
        misiones=tuple(_mision_desde_documento(m, unidades or {}) for m in d["misiones"]),
    )
