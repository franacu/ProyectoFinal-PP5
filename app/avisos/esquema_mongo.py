"""Esquema de persistencia del aviso: documento de Mongo ⇄ Aviso.

Es el único lugar que sabe cómo se ve un aviso guardado. El dominio solo ofrece
`Aviso.restaurar`, que recibe objetos del dominio ya armados (Ubicacion, Nota,
Descarte, Registro); nunca recibe un documento.

Versión 1 del documento:

    {
      "_id": "…", "version": 1,
      "reportante_id": "…",
      "ubicacion": {"direccion": "…", "localidad": "…"},
      "tipo": "incendio", "gravedad_estimada": "alta",
      "descripcion": "…", "registrado_en": <fecha>,
      "estado": "pendiente",
      "notas": [{"autor_id": "…", "texto": "…", "fecha_hora": <fecha>}],
      "descarte": null | {"operador_id": "…", "justificacion": "…", "fecha_hora": <fecha>},
      "registros": [{"actor_id", "fecha_hora", "operacion", "recursos", "detalle"}]
    }

Para cambiar la forma: subir VERSION_ESQUEMA, escribir la migración de la versión
anterior en _MIGRACIONES y adaptar las dos funciones públicas. El dominio no se toca.
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
from dominio.aviso import Aviso, Descarte, EstadoAviso, Nota
from dominio.catalogos import Gravedad, TipoSituacion

VERSION_ESQUEMA = 1

# Privado: migraciones de una versión a la siguiente (todavía no hubo cambios de forma).
_MIGRACIONES: dict = {}


def a_documento(aviso: Aviso) -> dict:
    descarte = aviso.descarte
    return {
        "_id": aviso.id,
        "version": VERSION_ESQUEMA,
        "reportante_id": aviso.reportante_id,
        "ubicacion": ubicacion_a_documento(aviso.ubicacion),
        "tipo": aviso.tipo.value,
        "gravedad_estimada": aviso.gravedad_estimada.name.lower(),
        "descripcion": aviso.descripcion,
        "registrado_en": aviso.registrado_en,
        "estado": aviso.estado.value,
        "notas": [
            {"autor_id": n.autor_id, "texto": n.texto, "fecha_hora": n.fecha_hora}
            for n in aviso.notas
        ],
        "descarte": None if descarte is None else {
            "operador_id": descarte.operador_id,
            "justificacion": descarte.justificacion,
            "fecha_hora": descarte.fecha_hora,
        },
        "registros": [registro_a_documento(r) for r in aviso.registros],
    }


def desde_documento(documento: Mapping) -> Aviso:
    d = migrar(documento, VERSION_ESQUEMA, _MIGRACIONES, "avisos")
    descarte = d.get("descarte")
    return Aviso.restaurar(
        aviso_id=d["_id"],
        reportante_id=d["reportante_id"],
        ubicacion=ubicacion_desde_documento(d["ubicacion"]),
        tipo=TipoSituacion(d["tipo"]),
        gravedad_estimada=Gravedad[d["gravedad_estimada"].upper()],
        descripcion=d["descripcion"],
        registrado_en=fecha_desde_documento(d["registrado_en"]),
        estado=EstadoAviso(d["estado"]),
        notas=tuple(
            Nota(n["autor_id"], n["texto"], fecha_desde_documento(n["fecha_hora"]))
            for n in d.get("notas", [])
        ),
        descarte=None if descarte is None else Descarte(
            descarte["operador_id"], descarte["justificacion"], fecha_desde_documento(descarte["fecha_hora"])),
        registros=tuple(registro_desde_documento(r) for r in d.get("registros", [])),
    )
