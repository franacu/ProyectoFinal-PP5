"""Armado de escenarios para los tests (no es dominio: son datos de ejemplo)."""

from datetime import datetime, timedelta

from dominio.aviso import Aviso
from dominio.catalogos import (
    CategoriaEquipo,
    Competencia,
    Gravedad,
    TipoSituacion,
)
from dominio.emergencia import Emergencia
from dominio.equipamiento import Equipo
from dominio.flota import BaseOperativa, Flota
from dominio.personal import Persona
from dominio.unidad import Unidad
from dominio.valores import Ubicacion
from dominio.vehiculos import Ambulancia, TransportePersonas, VehiculoRescate

CONDUCCION = Competencia.CONDUCCION
EVACUACION = Competencia.EVACUACION
RESCATE = Competencia.RESCATE
PRIMEROS_AUXILIOS = Competencia.PRIMEROS_AUXILIOS


def t(minutos: int = 0) -> datetime:
    """Instante de prueba: minutos después de las 10:00 del 20/11/2026."""
    return datetime(2026, 11, 20, 10, 0) + timedelta(minutes=minutos)


def persona(persona_id: str, *competencias: Competencia) -> Persona:
    return Persona(persona_id, persona_id.capitalize(), frozenset(competencias))


# ── Unidades aptas para cada tipo de misión ───────────────────

def unidad_de_evacuacion(uid: str = "ue", capacidad: int = 10, base: str = "base-1") -> Unidad:
    return Unidad(uid, base, jefe=persona(f"{uid}-jefe", CONDUCCION),
                  vehiculo=TransportePersonas(id=f"{uid}-veh", capacidad_evacuados=capacidad),
                  personal=(persona(f"{uid}-evac", EVACUACION),))


def unidad_de_rescate(uid: str = "ur", base: str = "base-1") -> Unidad:
    return Unidad(uid, base, jefe=persona(f"{uid}-jefe", CONDUCCION),
                  vehiculo=VehiculoRescate(id=f"{uid}-veh"),
                  personal=(persona(f"{uid}-r1", RESCATE), persona(f"{uid}-r2", RESCATE)),
                  equipamiento=(Equipo(f"{uid}-equipo", CategoriaEquipo.EQUIPO_DE_RESCATE),))


def unidad_sanitaria(uid: str = "us", base: str = "base-1") -> Unidad:
    return Unidad(uid, base, jefe=persona(f"{uid}-jefe", CONDUCCION),
                  vehiculo=Ambulancia(id=f"{uid}-veh"),
                  personal=(persona(f"{uid}-pa", PRIMEROS_AUXILIOS),),
                  equipamiento=(Equipo(f"{uid}-equipo", CategoriaEquipo.EQUIPO_SANITARIO),))


def flota_con(*unidades: Unidad, base: str = "base-1") -> Flota:
    flota = Flota()
    flota.registrar_base(BaseOperativa(base, "Base Norte", Ubicacion("Av. 1", "Río Grande")))
    for unidad in unidades:
        flota.incorporar_unidad(unidad, "resp-1", t(-60))
    return flota


# ── Avisos y emergencias ──────────────────────────────────────

def aviso(reportante: str = "rep-1", tipo: TipoSituacion = TipoSituacion.INUNDACION,
          gravedad: Gravedad = Gravedad.MEDIA, registrado: datetime | None = None) -> Aviso:
    return Aviso(reportante, Ubicacion("Ruta 3 km 12", "Río Grande"), tipo, gravedad,
                 "Agua ingresando a viviendas", registrado or t(0))


def emergencia(tipo: TipoSituacion = TipoSituacion.INUNDACION, gravedad: Gravedad = Gravedad.MEDIA,
               aceptada: datetime | None = None, reportante: str = "rep-1") -> Emergencia:
    """Una emergencia abierta, originada de verdad aceptando un aviso."""
    return aviso(reportante, tipo, gravedad).aceptar("op-1", tipo, gravedad, aceptada or t(5))
