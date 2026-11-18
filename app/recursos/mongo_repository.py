"""Repositorio de la flota sobre MongoDB (colecciones `bases` y `unidades`)."""

from pymongo.database import Database

from app.recursos.esquema_mongo import (
    base_a_documento,
    base_desde_documento,
    unidad_a_documento,
    unidad_desde_documento,
)
from dominio.flota import BaseOperativa, Flota
from dominio.unidad import Unidad


class RepositorioFlotaMongo:
    def __init__(self, base: Database) -> None:
        self._bases = base["bases"]
        self._unidades = base["unidades"]

    def cargar(self) -> Flota:
        bases = tuple(base_desde_documento(d) for d in self._bases.find().sort("_id", 1))
        unidades = tuple(unidad_desde_documento(d) for d in self._unidades.find().sort("_id", 1))
        return Flota.restaurar(bases, unidades)

    def guardar_base(self, base: BaseOperativa) -> None:
        self._bases.replace_one({"_id": base.id}, base_a_documento(base), upsert=True)

    def guardar_unidad(self, unidad: Unidad) -> None:
        self._unidades.replace_one({"_id": unidad.id}, unidad_a_documento(unidad), upsert=True)
