"""Esquemas de persistencia de bases y unidades: documento de Mongo ⇄ dominio.

Versión 1 de la unidad:

    {
      "_id": "U-1", "version": 1, "base_id": "B-1",
      "jefe": {"id", "nombre", "competencias": [...]},
      "personal": [ ...personas, sin el jefe... ],
      "vehiculo": {"id", "categoria", "condicion", "capacidad_evacuados"?},
      "equipamiento": [{"id", "categoria", "condicion"}],
      "condicion": "habilitada", "mision_comprometida_id": null | "…",
      "registros": [ … ]
    }
"""

from collections.abc import Mapping

from app.internal.esquema import (
    migrar,
    registro_a_documento,
    registro_desde_documento,
    ubicacion_a_documento,
    ubicacion_desde_documento,
)
from app.recursos.fabricas import CLASE_DE_VEHICULO, datos_propios_del_vehiculo
from dominio.catalogos import CategoriaEquipo, CategoriaVehiculo, Competencia, CondicionOperativa, CondicionServicio
from dominio.equipamiento import Equipo
from dominio.flota import BaseOperativa
from dominio.personal import Persona
from dominio.unidad import Unidad
from dominio.vehiculos import Vehiculo

VERSION_BASE = 1
VERSION_UNIDAD = 1
_MIGRACIONES_BASE: dict = {}    # privado
_MIGRACIONES_UNIDAD: dict = {}  # privado


# ── Piezas ────────────────────────────────────────────────────

def persona_a_documento(persona: Persona) -> dict:
    return {"id": persona.id, "nombre": persona.nombre,
            "competencias": sorted(c.value for c in persona.competencias)}


def persona_desde_documento(d: Mapping) -> Persona:
    return Persona(d["id"], d["nombre"], frozenset(Competencia(c) for c in d["competencias"]))


def vehiculo_a_documento(vehiculo: Vehiculo) -> dict:
    return {"id": vehiculo.id, "categoria": vehiculo.categoria.value, "condicion": vehiculo.condicion.value,
            **datos_propios_del_vehiculo(vehiculo)}


def vehiculo_desde_documento(d: Mapping) -> Vehiculo:
    clase = CLASE_DE_VEHICULO[CategoriaVehiculo(d["categoria"])]
    extra = {k: v for k, v in d.items() if k not in ("id", "categoria", "condicion")}
    return clase(id=d["id"], condicion=CondicionOperativa(d["condicion"]), **extra)


def equipo_a_documento(equipo: Equipo) -> dict:
    return {"id": equipo.id, "categoria": equipo.categoria.value, "condicion": equipo.condicion.value}


def equipo_desde_documento(d: Mapping) -> Equipo:
    return Equipo(d["id"], CategoriaEquipo(d["categoria"]), CondicionOperativa(d["condicion"]))


# ── Base operativa ────────────────────────────────────────────

def base_a_documento(base: BaseOperativa) -> dict:
    return {"_id": base.id, "version": VERSION_BASE, "nombre": base.nombre,
            "ubicacion": ubicacion_a_documento(base.ubicacion)}


def base_desde_documento(documento: Mapping) -> BaseOperativa:
    d = migrar(documento, VERSION_BASE, _MIGRACIONES_BASE, "bases")
    return BaseOperativa(d["_id"], d["nombre"], ubicacion_desde_documento(d["ubicacion"]))


# ── Unidad ────────────────────────────────────────────────────

def unidad_a_documento(unidad: Unidad) -> dict:
    return {
        "_id": unidad.id,
        "version": VERSION_UNIDAD,
        "base_id": unidad.base_id,
        "jefe": persona_a_documento(unidad.jefe),
        "personal": [persona_a_documento(p) for p in unidad.personal if p.id != unidad.jefe.id],
        "vehiculo": vehiculo_a_documento(unidad.vehiculo),
        "equipamiento": [equipo_a_documento(e) for e in unidad.equipamiento],
        "condicion": unidad.condicion.value,
        "mision_comprometida_id": unidad.mision_comprometida_id,
        "registros": [registro_a_documento(r) for r in unidad.registros],
    }


def unidad_desde_documento(documento: Mapping) -> Unidad:
    d = migrar(documento, VERSION_UNIDAD, _MIGRACIONES_UNIDAD, "unidades")
    return Unidad.restaurar(
        unidad_id=d["_id"],
        base_id=d["base_id"],
        jefe=persona_desde_documento(d["jefe"]),
        vehiculo=vehiculo_desde_documento(d["vehiculo"]),
        personal=tuple(persona_desde_documento(p) for p in d["personal"]),
        equipamiento=tuple(equipo_desde_documento(e) for e in d["equipamiento"]),
        condicion=CondicionServicio(d["condicion"]),
        mision_comprometida_id=d.get("mision_comprometida_id"),
        registros=tuple(registro_desde_documento(r) for r in d["registros"]),
    )
