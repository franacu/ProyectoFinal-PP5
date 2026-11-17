"""Repositorio de emergencias sobre MongoDB (colección `emergencias`)."""

from pymongo.database import Database

from app.emergencias.esquema_mongo import a_documento, desde_documento
from dominio.emergencia import Emergencia


class RepositorioEmergenciasMongo:
    def __init__(self, base: Database) -> None:
        self._coleccion = base["emergencias"]

    def guardar(self, emergencia: Emergencia) -> None:
        self._coleccion.replace_one({"_id": emergencia.id}, a_documento(emergencia), upsert=True)

    def obtener(self, emergencia_id: str) -> Emergencia | None:
        documento = self._coleccion.find_one({"_id": emergencia_id})
        return None if documento is None else desde_documento(documento)

    def listar(self) -> list[Emergencia]:
        return [desde_documento(d) for d in self._coleccion.find()]
