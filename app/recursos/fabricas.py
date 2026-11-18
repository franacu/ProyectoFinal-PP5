"""Construcción de vehículos y misiones a partir de su nombre de catálogo.

La API y la base guardan el tipo como texto ("ambulancia", "rescate"). Acá se
traduce ese texto a la clase del dominio con una tabla, sin cadenas de if. Agregar
un tipo nuevo es agregar una línea.
"""

from dominio.catalogos import CategoriaVehiculo, TipoMision
from dominio.mision import AsistenciaSanitaria, Evacuacion, Mision, Rescate
from dominio.vehiculos import Ambulancia, TransportePersonas, Vehiculo, VehiculoRescate

CLASE_DE_VEHICULO: dict[CategoriaVehiculo, type[Vehiculo]] = {
    CategoriaVehiculo.TRANSPORTE_DE_PERSONAS: TransportePersonas,
    CategoriaVehiculo.VEHICULO_DE_RESCATE: VehiculoRescate,
    CategoriaVehiculo.AMBULANCIA: Ambulancia,
}

CLASE_DE_MISION: dict[TipoMision, type[Mision]] = {
    TipoMision.EVACUACION: Evacuacion,
    TipoMision.RESCATE: Rescate,
    TipoMision.ASISTENCIA_SANITARIA: AsistenciaSanitaria,
}


# Privado: cómo se crea una misión nueva de cada tipo. Solo la evacuación usa la cantidad
# de personas; si falta o no es válida, el dominio la rechaza (MisionInvalida → 422).
_NUEVA_MISION = {
    TipoMision.EVACUACION: lambda objetivo, cantidad: Evacuacion(objetivo, cantidad),
    TipoMision.RESCATE: lambda objetivo, cantidad: Rescate(objetivo),
    TipoMision.ASISTENCIA_SANITARIA: lambda objetivo, cantidad: AsistenciaSanitaria(objetivo),
}


def nueva_mision(tipo: TipoMision, objetivo: str, cantidad_personas: int | None) -> Mision:
    return _NUEVA_MISION[tipo](objetivo, cantidad_personas)


def datos_propios_del_vehiculo(vehiculo: Vehiculo) -> dict:
    """Atributos que solo tienen algunas categorías (hoy, la capacidad del transporte)."""
    capacidad = getattr(vehiculo, "capacidad_evacuados", None)
    return {} if capacidad is None else {"capacidad_evacuados": capacidad}
