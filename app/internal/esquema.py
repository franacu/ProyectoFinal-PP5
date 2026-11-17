"""Piezas comunes de los esquemas de persistencia (documento de Mongo ⇄ dominio).

Por qué existe esta capa (consejo de la cátedra):
el dominio no conoce cómo se guarda. Si mañana cambia la base o cambia la forma
de un documento, se modifica el esquema y el dominio queda intacto.

Cada documento guarda el número de versión de su forma (`version`). Al leer:
1. si el documento es de una versión vieja, se lo migra paso a paso hasta la actual;
2. si es de una versión más nueva que la que este código conoce, se rechaza
   (`EsquemaIncompatible`) en lugar de interpretarlo mal.
"""

from collections.abc import Callable, Mapping
from datetime import UTC, datetime

from dominio.historial import Operacion, Registro
from dominio.valores import Ubicacion

Migracion = Callable[[dict], dict]


class EsquemaIncompatible(Exception):
    """El documento guardado no se puede leer con la versión actual del esquema."""


def migrar(documento: Mapping, version_actual: int, migraciones: Mapping[int, Migracion],
           coleccion: str) -> dict:
    """Lleva un documento de su versión a la actual.

    `migraciones[n]` transforma un documento de la versión n a la n + 1.
    """
    documento = dict(documento)
    version = documento.get("version", 1)
    if version > version_actual:
        raise EsquemaIncompatible(
            f"{coleccion}: el documento es de la versión {version} y este código lee hasta la {version_actual}")
    while version < version_actual:
        if version not in migraciones:
            raise EsquemaIncompatible(f"{coleccion}: falta la migración de la versión {version} a la {version + 1}")
        documento = migraciones[version](documento)
        version += 1
        documento["version"] = version
    return documento


# ── Conversores compartidos ──────────────────────────────────

def fecha_desde_documento(valor: datetime) -> datetime:
    """Mongo guarda en UTC. Si el cliente devuelve la fecha sin zona, se le asigna UTC."""
    return valor if valor.tzinfo is not None else valor.replace(tzinfo=UTC)


def ubicacion_a_documento(ubicacion: Ubicacion) -> dict:
    return {"direccion": ubicacion.direccion, "localidad": ubicacion.localidad}


def ubicacion_desde_documento(documento: Mapping) -> Ubicacion:
    return Ubicacion(documento["direccion"], documento["localidad"])


def registro_a_documento(registro: Registro) -> dict:
    return {
        "actor_id": registro.actor_id,
        "fecha_hora": registro.fecha_hora,
        "operacion": registro.operacion.value,
        "recursos": list(registro.recursos),
        "detalle": dict(registro.detalle),
    }


def registro_desde_documento(documento: Mapping) -> Registro:
    return Registro(
        documento["actor_id"],
        fecha_desde_documento(documento["fecha_hora"]),
        Operacion(documento["operacion"]),
        tuple(documento["recursos"]),
        tuple(documento.get("detalle", {}).items()),
    )
