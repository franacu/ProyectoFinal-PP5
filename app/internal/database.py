"""Conexión con MongoDB. Se abre al arrancar la aplicación y se cierra al apagarla."""

from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import PyMongoError

from app.config import configuracion


class ConexionMongo:
    def __init__(self) -> None:
        self._client: MongoClient | None = None

    def conectar(self) -> Database:
        # tz_aware: las fechas vuelven de Mongo con zona horaria (UTC), igual que se guardaron.
        self._client = MongoClient(configuracion.mongo_uri, serverSelectionTimeoutMS=3000, tz_aware=True)
        try:
            self._client.admin.command("ping")
        except PyMongoError as error:
            raise ConnectionError(
                "No se pudo conectar a MongoDB. "
                "Levantá la base con `docker compose up -d db` y revisá MONGO_HOST."
            ) from error
        return self._client[configuracion.mongo_db]

    def cerrar(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None
