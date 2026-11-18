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
    keycloak_url: str = os.getenv("KEYCLOAK_URL", "http://localhost:8080")
    keycloak_realm: str = os.getenv("KEYCLOAK_REALM", "crce")
    keycloak_client_id: str = os.getenv("KEYCLOAK_CLIENT_ID", "crce-api")
    # Dirección de Keycloak vista desde el navegador (en Compose, la API usa `keycloak:8080`).
    keycloak_url_publica: str = os.getenv("KEYCLOAK_URL_PUBLICA", "http://localhost:8080")

    @property
    def mongo_uri(self) -> str:
        return (
            f"mongodb://{self.mongo_user}:{self.mongo_password}"
            f"@{self.mongo_host}:{self.mongo_port}/"
        )


configuracion = Configuracion()
