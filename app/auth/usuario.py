"""El usuario autenticado y sus cinco perfiles posibles (§2, §9)."""

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum


class Perfil(Enum):
    """Coinciden con los roles del realm `crce` de Keycloak."""

    REPORTANTE = "reportante"
    OPERADOR = "operador"
    JEFE_UNIDAD = "jefe_unidad"
    RESPONSABLE_RECURSOS = "responsable_recursos"
    SUPERVISOR = "supervisor"


class SinPerfil(Exception):
    """El token es válido pero el usuario no tiene ninguno de los cinco perfiles."""


class AccesoDenegado(Exception):
    """El usuario no puede hacer esto: por su perfil o porque el recurso no es suyo (→ 403)."""


@dataclass(frozen=True)
class Usuario:
    id: str          # nombre de usuario en Keycloak; para un jefe, coincide con su id de persona
    perfil: Perfil

    @classmethod
    def desde_token(cls, datos: Mapping) -> "Usuario":
        """Arma el usuario con los datos (claims) de un token ya verificado."""
        roles = set(datos.get("realm_access", {}).get("roles", []))
        perfiles = [p for p in Perfil if p.value in roles]
        if len(perfiles) != 1:
            raise SinPerfil("El usuario debe tener exactamente uno de los cinco perfiles")
        return cls(datos["preferred_username"], perfiles[0])

    def es(self, *perfiles: Perfil) -> bool:
        return self.perfil in perfiles

    def exigir_acceso_a(self, reportante_id: str) -> None:
        """Un reportante solo accede a lo suyo (PV01). Los demás perfiles ya pasaron el control de la ruta."""
        if self.perfil is Perfil.REPORTANTE and reportante_id != self.id:
            raise AccesoDenegado("Solo se pueden consultar los avisos propios")
