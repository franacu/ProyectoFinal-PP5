"""Configuración leída del entorno (o de un archivo .env en desarrollo)."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Configuracion:
    mongo_user: str = os.getenv("MONGO_USER", "root")
    mongo_password: str = os.getenv("MONGO_PASSWORD", "example")
    mongo_host: str = os.getenv("MONGO_HOST", "localhost")
    mongo_port: str = os.getenv("MONGO_PORT", "27017")
    mongo_db: str = os.getenv("MONGO_DB", "crce")

    @property
    def mongo_uri(self) -> str:
        return (
            f"mongodb://{self.mongo_user}:{self.mongo_password}"
            f"@{self.mongo_host}:{self.mongo_port}/"
        )


configuracion = Configuracion()
