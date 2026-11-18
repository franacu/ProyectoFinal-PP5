"""Repositorio de emergencias sobre MongoDB (colección `emergencias`)."""

from pymongo.database import Database

from app.emergencias.esquema_mongo import a_documento, desde_documento
from dominio.emergencia import Emergencia
from dominio.flota import Flota


def _unidades_de(flota: Flota | None) -> dict:
    """Privada: unidades de la flota por id."""
    return {} if flota is None else {u.id: u for u in flota.unidades}


class RepositorioEmergenciasMongo:
    def __init__(self, base: Database) -> None:
        self._coleccion = base["emergencias"]

    def guardar(self, emergencia: Emergencia) -> None:
        self._coleccion.replace_one({"_id": emergencia.id}, a_documento(emergencia), upsert=True)

    def obtener(self, emergencia_id: str, flota: Flota | None = None) -> Emergencia | None:
        documento = self._coleccion.find_one({"_id": emergencia_id})
        return None if documento is None else desde_documento(documento, _unidades_de(flota))

    def listar(self, flota: Flota | None = None) -> list[Emergencia]:
        unidades = _unidades_de(flota)
        return [desde_documento(d, unidades) for d in self._coleccion.find()]
