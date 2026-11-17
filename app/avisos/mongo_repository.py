"""Repositorio de avisos sobre MongoDB (colección `avisos`).

Solo habla con la base. La traducción documento ⇄ Aviso es del esquema.
"""

from pymongo.database import Database

from app.avisos.esquema_mongo import a_documento, desde_documento
from dominio.aviso import Aviso, EstadoAviso


class RepositorioAvisosMongo:
    def __init__(self, base: Database) -> None:
        self._coleccion = base["avisos"]

    def guardar(self, aviso: Aviso) -> None:
        self._coleccion.replace_one({"_id": aviso.id}, a_documento(aviso), upsert=True)

    def obtener(self, aviso_id: str) -> Aviso | None:
        documento = self._coleccion.find_one({"_id": aviso_id})
        return None if documento is None else desde_documento(documento)

    def listar(self, estado: EstadoAviso | None = None) -> list[Aviso]:
        filtro = {} if estado is None else {"estado": estado.value}
        return [desde_documento(d) for d in self._coleccion.find(filtro).sort("registrado_en", 1)]
