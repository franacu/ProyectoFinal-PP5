"""Dependencias de FastAPI para autenticar y autorizar.

Dos niveles de autorización (§9):
1. Perfil: cada endpoint declara qué perfiles lo pueden usar con `requiere(...)`.
   Si no corresponde → 403 (PV12).
2. Relación con el recurso: la verifica el servicio o el dominio (el reportante con su
   aviso, el jefe con su unidad). Si no corresponde → 403 aunque el perfil sea correcto.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError, PyJWKClientError

from app.auth.keycloak import verificador
from app.auth.usuario import Perfil, SinPerfil, Usuario

_bearer = HTTPBearer(auto_error=False)


def usuario_actual(credenciales: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> Usuario:
    if credenciales is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Falta el token", headers={"WWW-Authenticate": "Bearer"})
    try:
        return Usuario.desde_token(verificador.verificar(credenciales.credentials))
    except InvalidTokenError as error:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token inválido o vencido",
                            headers={"WWW-Authenticate": "Bearer"}) from error
    except PyJWKClientError as error:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE,
                            "No se pudo validar el token contra Keycloak") from error
    except SinPerfil as error:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(error)) from error


def requiere(*perfiles: Perfil):
    """Dependencia que deja pasar solo a los perfiles indicados."""
    nombres = ", ".join(p.value for p in perfiles)

    def verificar(usuario: Usuario = Depends(usuario_actual)) -> Usuario:
        if not usuario.es(*perfiles):
            raise HTTPException(status.HTTP_403_FORBIDDEN,
                                f"Operación permitida solo para: {nombres} (perfil actual: {usuario.perfil.value})")
        return usuario

    return verificar
