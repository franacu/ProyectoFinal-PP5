"""Catálogos cerrados del enunciado (§3 y §4).

Son Enum: un valor fuera del catálogo no se puede construir, así que
nunca llega a un aviso.
"""

from enum import Enum


class Catalogo(Enum):
    """Base de los catálogos: pregunta pertenencia sin comparar clases."""

    @classmethod
    def contiene(cls, valor) -> bool:
        # `valor in cls` aceptaría también el texto "inundacion" (Python 3.12+),
        # por eso se compara contra los miembros reales.
        return valor in tuple(cls)


class TipoSituacion(Catalogo):
    INUNDACION = "inundacion"
    INCENDIO = "incendio"
    ACCIDENTE_VIAL = "accidente_vial"


class Gravedad(Catalogo):
    """El orden (ALTA > MEDIA > BAJA) se usa después para priorizar emergencias (§4)."""

    BAJA = 1
    MEDIA = 2
    ALTA = 3


class Competencia(Catalogo):
    """Competencias del personal (§5.3)."""

    CONDUCCION = "conduccion"
    EVACUACION = "evacuacion"
    RESCATE = "rescate"
    PRIMEROS_AUXILIOS = "primeros_auxilios"


class CategoriaVehiculo(Catalogo):
    """Categorías de vehículo (§5.4)."""

    TRANSPORTE_DE_PERSONAS = "transporte_de_personas"
    VEHICULO_DE_RESCATE = "vehiculo_de_rescate"
    AMBULANCIA = "ambulancia"


class CategoriaEquipo(Catalogo):
    """Categorías de equipamiento especializado (§5.5)."""

    EQUIPO_DE_RESCATE = "equipo_de_rescate"
    EQUIPO_SANITARIO = "equipo_sanitario"


class CondicionOperativa(Catalogo):
    """Condición de un vehículo o de un elemento de equipamiento (§5.4, §5.5)."""

    OPERATIVO = "operativo"
    FUERA_DE_SERVICIO = "fuera_de_servicio"


class CondicionServicio(Catalogo):
    """Condición de servicio de una unidad (§8.4). No es lo mismo que estar comprometida."""

    HABILITADA = "habilitada"
    EN_MANTENIMIENTO = "en_mantenimiento"
    FUERA_DE_SERVICIO = "fuera_de_servicio"


class TipoMision(Catalogo):
    """Nombre público del tipo de misión (§6). El comportamiento vive en cada clase de misión."""

    EVACUACION = "evacuacion"
    RESCATE = "rescate"
    ASISTENCIA_SANITARIA = "asistencia_sanitaria"


class ResultadoMision(Catalogo):
    """Resultado que declara el jefe al finalizar (§2.3, §8.1)."""

    SATISFACTORIO = "satisfactorio"
    NO_SATISFACTORIO = "no_satisfactorio"
