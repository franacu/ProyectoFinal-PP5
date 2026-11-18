"""Carga inicial reproducible para la demostración (§9: cuentas y vínculos).

Las cuentas y sus perfiles están en Keycloak (keycloak/crce-realm.json). Acá se cargan los
recursos y los vínculos jefe ↔ unidad: el id de persona del jefe coincide con su usuario de
Keycloak (por ejemplo, la jefa de U-rescate-1 es `ana`).

Se puede ejecutar varias veces: lo que ya existe no se vuelve a cargar.

    uv run python -m app.semilla
"""

from app.internal.reloj import reloj_del_sistema
from app.recursos.repository import RepositorioFlota
from app.recursos.service import ServicioRecursos
from dominio.catalogos import CategoriaEquipo, Competencia
from dominio.equipamiento import Equipo
from dominio.personal import Persona
from dominio.valores import Ubicacion
from dominio.vehiculos import Ambulancia, TransportePersonas, VehiculoRescate

C = Competencia
BASES = [
    ("B-centro", "Base Centro", Ubicacion("Maipú 100", "Ushuaia")),
    ("B-norte", "Base Norte", Ubicacion("Av. Perito Moreno 2500", "Ushuaia")),
]
UNIDADES = [
    # (id, base, jefe, vehículo, resto de la dotación, equipamiento)
    ("U-rescate-1", "B-centro", Persona("ana", "Ana Rescate", {C.RESCATE}), VehiculoRescate(id="VR-1"),
     (Persona("bruno", "Bruno Díaz", {C.CONDUCCION}), Persona("carla", "Carla Gómez", {C.RESCATE})),
     (Equipo("ER-1", CategoriaEquipo.EQUIPO_DE_RESCATE),)),
    ("U-rescate-2", "B-norte", Persona("diego", "Diego Rescate", {C.RESCATE}), VehiculoRescate(id="VR-2"),
     (Persona("eva", "Eva Luna", {C.CONDUCCION}), Persona("fede", "Federico Paz", {C.RESCATE})),
     (Equipo("ER-2", CategoriaEquipo.EQUIPO_DE_RESCATE),)),
    ("U-ambulancia-1", "B-centro", Persona("gabi", "Gabriela Sanitaria", {C.CONDUCCION}), Ambulancia(id="AMB-1"),
     (Persona("hugo", "Hugo Médico", {C.PRIMEROS_AUXILIOS}),),
     (Equipo("ES-1", CategoriaEquipo.EQUIPO_SANITARIO),)),
    ("U-transporte-1", "B-norte", Persona("ines", "Inés Transporte", {C.CONDUCCION}),
     TransportePersonas(id="TP-1", capacidad_evacuados=20),
     (Persona("juan", "Juan Evacuador", {C.EVACUACION}),), ()),
]
RESPONSABLE = "recursos1"


def cargar(flota: RepositorioFlota) -> list[str]:
    """Carga lo que falte y devuelve qué se cargó."""
    servicio = ServicioRecursos(flota, reloj_del_sistema)
    existentes_bases = {b.id for b in servicio.bases()}
    existentes_unidades = {u.id for u in servicio.unidades()}
    cargado = []
    for base_id, nombre, ubicacion in BASES:
        if base_id not in existentes_bases:
            servicio.registrar_base(base_id, nombre, ubicacion)
            cargado.append(base_id)
    for unidad_id, base_id, jefe, vehiculo, personal, equipamiento in UNIDADES:
        if unidad_id not in existentes_unidades:
            servicio.registrar_unidad(RESPONSABLE, unidad_id, base_id, jefe, vehiculo, personal, equipamiento)
            cargado.append(unidad_id)
    return cargado


def _principal() -> None:
    """Privada: punto de entrada por consola. Conecta con MongoDB según la configuración."""
    from app.internal.database import ConexionMongo
    from app.recursos.mongo_repository import RepositorioFlotaMongo

    conexion = ConexionMongo()
    try:
        cargado = cargar(RepositorioFlotaMongo(conexion.conectar()))
    finally:
        conexion.cerrar()
    print("Carga inicial:", ", ".join(cargado) if cargado else "ya estaba completa")


if __name__ == "__main__":
    _principal()
