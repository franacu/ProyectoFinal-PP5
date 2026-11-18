"""Verificación de tokens emitidos por Keycloak (mismo criterio que el repositorio de la cátedra).

La firma se valida con las claves públicas del realm (JWKS). El emisor del token usa el
host desde el que se pidió (normalmente localhost); la API, dentro de Compose, busca las
claves en `keycloak`. Por eso se compara el realm del emisor y no el host.
"""

import jwt
from jwt import PyJWKClient

from app.config import configuracion


class VerificadorKeycloak:
    def __init__(self) -> None:
        self._jwks: PyJWKClient | None = None

    def verificar(self, token: str) -> dict:
        clave = self._cliente_jwks().get_signing_key_from_jwt(token)
        datos = jwt.decode(token, clave.key, algorithms=["RS256"],
                           options={"verify_aud": False, "verify_iss": False})
        emisor = str(datos.get("iss", ""))
        if not emisor.endswith(f"/realms/{configuracion.keycloak_realm}"):
            raise jwt.InvalidTokenError("El token no pertenece al realm esperado")
        return datos

    def _cliente_jwks(self) -> PyJWKClient:
        """Privado: el cliente de claves públicas se crea la primera vez que se lo necesita."""
        if self._jwks is None:
            base = configuracion.keycloak_url.rstrip("/")
            self._jwks = PyJWKClient(f"{base}/realms/{configuracion.keycloak_realm}/protocol/openid-connect/certs")
        return self._jwks


verificador = VerificadorKeycloak()
