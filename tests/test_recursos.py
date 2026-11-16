"""Recursos (§5): personal, vehículos, equipos, unidades y flota. PV06–PV09 de fondo, PV07 y PV14 acá."""

import pytest

from dominio.catalogos import CategoriaEquipo, CondicionOperativa, CondicionServicio, Competencia
from dominio.distribucion import existe_distribucion
from dominio.equipamiento import Equipo
from dominio.errores import (
    NoEncontrado,
    RecursoDuplicado,
    RecursoInvalido,
    UnidadComprometida,
)
from dominio.flota import BaseOperativa, Flota
from dominio.mision import Rescate
from dominio.personal import Persona
from dominio.unidad import Unidad
from dominio.valores import Ubicacion
from dominio.vehiculos import Ambulancia, TransportePersonas, VehiculoRescate
from tests.escenarios import (
    CONDUCCION,
    EVACUACION,
    RESCATE,
    emergencia,
    flota_con,
    persona,
    t,
    unidad_de_evacuacion,
    unidad_de_rescate,
    unidad_sanitaria,
)

PUESTOS_RESCATE = (CONDUCCION, RESCATE, RESCATE)


# ── §5.3 / PV07: personas distintas, sin contar a nadie dos veces ──

def test_pv07_conductor_y_un_unico_rescatista_no_cubren_un_rescate():
    personas = (persona("bruno", CONDUCCION), persona("carla", RESCATE))

    assert existe_distribucion(PUESTOS_RESCATE, personas) is False


def test_pv07_una_persona_con_conduccion_y_rescate_no_cuenta_como_dos_integrantes():
    ana = persona("ana", CONDUCCION, RESCATE)
    carla = persona("carla", RESCATE)

    assert existe_distribucion(PUESTOS_RESCATE, (ana, carla)) is False


def test_pv07_ana_conduccion_y_rescate_bruno_conduccion_carla_rescate_si_cubren():
    ana = persona("ana", CONDUCCION, RESCATE)
    bruno = persona("bruno", CONDUCCION)
    carla = persona("carla", RESCATE)

    assert existe_distribucion(PUESTOS_RESCATE, (ana, bruno, carla)) is True


def test_distribucion_no_depende_del_orden_en_que_se_listan_las_personas():
    ana = persona("ana", CONDUCCION, RESCATE)
    bruno = persona("bruno", CONDUCCION)
    carla = persona("carla", RESCATE)

    assert existe_distribucion(PUESTOS_RESCATE, (carla, ana, bruno)) is True
    assert existe_distribucion(PUESTOS_RESCATE, (bruno, carla, ana)) is True


def test_pv07_el_jefe_integra_la_dotacion_y_se_cuenta_una_sola_vez():
    unidad = unidad_de_rescate()

    assert [p.id for p in unidad.personal].count(unidad.jefe.id) == 1
    assert len(unidad.personal) == 3


# ── Datos válidos ─────────────────────────────────────────────

def test_persona_sin_competencias_se_rechaza():
    with pytest.raises(RecursoInvalido):
        Persona("p1", "Pepe", frozenset())


def test_persona_con_competencia_fuera_de_catalogo_se_rechaza():
    with pytest.raises(RecursoInvalido):
        Persona("p1", "Pepe", frozenset({"volar"}))


@pytest.mark.parametrize("capacidad", [0, -3, None, "8", 2.5, True])
def test_vehiculo_de_transporte_exige_capacidad_entera_positiva(capacidad):
    with pytest.raises(RecursoInvalido):
        TransportePersonas(id="v1", capacidad_evacuados=capacidad)


@pytest.mark.parametrize("vehiculo_id", [None, "", "  "])
def test_vehiculo_sin_identificacion_se_rechaza(vehiculo_id):
    with pytest.raises(RecursoInvalido):
        Ambulancia(id=vehiculo_id)


def test_equipo_con_categoria_fuera_de_catalogo_se_rechaza():
    with pytest.raises(RecursoInvalido):
        Equipo("e1", "grua")


def test_unidad_no_acepta_dos_veces_a_la_misma_persona():
    jefe = persona("j", CONDUCCION)

    with pytest.raises(RecursoDuplicado):
        Unidad("u1", "base-1", jefe, VehiculoRescate(id="v"), personal=(jefe,))


# ── PV14: administración de recursos ──────────────────────────

def test_pv14_incorporar_personal_a_unidad_disponible_cambia_sus_capacidades():
    flota = flota_con(unidad_de_rescate("ur"))
    unidad = flota.unidad("ur")
    antes = len(unidad.personal)

    flota.incorporar_personal("ur", persona("nuevo", RESCATE), "resp-1", t())

    assert len(unidad.personal) == antes + 1
    assert unidad.tiene_persona("nuevo")


def test_pv14_incorporar_equipo_a_unidad_disponible_cambia_sus_capacidades():
    flota = flota_con(unidad_sanitaria("us"))
    unidad = flota.unidad("us")

    flota.incorporar_equipo("us", Equipo("us-extra", CategoriaEquipo.EQUIPO_DE_RESCATE), "resp-1", t())

    assert unidad.tiene_equipo_operativo(CategoriaEquipo.EQUIPO_DE_RESCATE)


def comprometer(flota: Flota, unidad_id: str):
    """Deja la unidad reservada por una misión de rescate de una emergencia abierta."""
    emerg = emergencia()
    mision = Rescate("Rescatar familia aislada")
    emerg.crear_mision(mision, "op-1", t())
    emerg.asignar_mision(mision.id, flota.unidad(unidad_id), "op-1", t(1))
    return emerg, mision


def test_pv14_unidad_asignada_a_una_mision_rechaza_todo_cambio_administrativo():
    flota = flota_con(unidad_de_rescate("ur"))
    comprometer(flota, "ur")
    unidad = flota.unidad("ur")
    cambios = [
        lambda: flota.incorporar_personal("ur", persona("nuevo", RESCATE), "resp-1", t(2)),
        lambda: unidad.retirar_personal("ur-r1", "resp-1", t(2)),
        lambda: flota.cambiar_vehiculo("ur", VehiculoRescate(id="otro"), "resp-1", t(2)),
        lambda: flota.incorporar_equipo("ur", Equipo("nuevo-eq", CategoriaEquipo.EQUIPO_DE_RESCATE), "resp-1", t(2)),
        lambda: unidad.retirar_equipo("ur-equipo", "resp-1", t(2)),
        lambda: unidad.cambiar_condicion_equipo("ur-equipo", CondicionOperativa.FUERA_DE_SERVICIO, "resp-1", t(2)),
        lambda: unidad.cambiar_condicion_vehiculo(CondicionOperativa.FUERA_DE_SERVICIO, "resp-1", t(2)),
        lambda: unidad.declarar_en_mantenimiento("resp-1", t(2)),
        lambda: unidad.declarar_fuera_de_servicio("resp-1", t(2)),
    ]

    for cambio in cambios:
        with pytest.raises(UnidadComprometida):
            cambio()

    assert len(unidad.personal) == 3
    assert unidad.condicion is CondicionServicio.HABILITADA
    assert len(unidad.registros) == 1  # solo el alta: los rechazos no dejaron registro


def test_el_jefe_no_se_retira_porque_la_unidad_siempre_necesita_jefe():
    flota = flota_con(unidad_de_rescate("ur"))

    with pytest.raises(RecursoInvalido):
        flota.unidad("ur").retirar_personal("ur-jefe", "resp-1", t())


def test_retirar_personal_que_no_integra_la_unidad_se_rechaza():
    flota = flota_con(unidad_de_rescate("ur"))

    with pytest.raises(NoEncontrado):
        flota.unidad("ur").retirar_personal("fantasma", "resp-1", t())


# ── §8.4: condición de servicio ───────────────────────────────

def test_unidad_en_mantenimiento_puede_modificarse_y_restablecerse_si_no_esta_comprometida():
    flota = flota_con(unidad_de_rescate("ur"))
    unidad = flota.unidad("ur")

    unidad.declarar_en_mantenimiento("resp-1", t())
    assert unidad.condicion is CondicionServicio.EN_MANTENIMIENTO
    flota.incorporar_personal("ur", persona("nuevo", RESCATE), "resp-1", t(1))
    unidad.restablecer_servicio("resp-1", t(2))

    assert unidad.condicion is CondicionServicio.HABILITADA


# ── §5.2: nada está en dos unidades ───────────────────────────

def test_una_persona_no_puede_formar_parte_de_dos_unidades():
    flota = flota_con(unidad_de_rescate("ur"), unidad_sanitaria("us"))

    with pytest.raises(RecursoDuplicado):
        flota.incorporar_personal("us", persona("ur-r1", RESCATE), "resp-1", t())

    assert not flota.unidad("us").tiene_persona("ur-r1")


def test_un_vehiculo_no_puede_estar_en_dos_unidades():
    flota = flota_con(unidad_de_rescate("ur"), unidad_sanitaria("us"))

    with pytest.raises(RecursoDuplicado):
        flota.cambiar_vehiculo("us", VehiculoRescate(id="ur-veh"), "resp-1", t())

    assert flota.unidad("us").vehiculo.id == "us-veh"


def test_un_equipo_no_puede_estar_en_dos_unidades():
    flota = flota_con(unidad_de_rescate("ur"), unidad_sanitaria("us"))

    with pytest.raises(RecursoDuplicado):
        flota.incorporar_equipo("us", Equipo("ur-equipo", CategoriaEquipo.EQUIPO_DE_RESCATE), "resp-1", t())


def test_incorporar_una_unidad_con_recursos_ya_usados_se_rechaza_y_la_flota_no_cambia():
    flota = flota_con(unidad_de_rescate("ur"))
    repetida = Unidad("u2", "base-1", jefe=persona("ur-jefe", CONDUCCION), vehiculo=Ambulancia(id="otra"))

    with pytest.raises(RecursoDuplicado):
        flota.incorporar_unidad(repetida, "resp-1", t())

    assert [u.id for u in flota.unidades] == ["ur"]


def test_cada_unidad_pertenece_a_una_base_que_existe():
    flota = flota_con(unidad_de_rescate("ur"))

    with pytest.raises(NoEncontrado):
        flota.incorporar_unidad(unidad_sanitaria("us", base="base-fantasma"), "resp-1", t())


def test_la_base_puede_alojar_varias_unidades_y_no_se_repite():
    flota = flota_con(unidad_de_rescate("ur"), unidad_sanitaria("us"))

    assert {u.id for u in flota.unidades_de("base-1")} == {"ur", "us"}
    with pytest.raises(RecursoDuplicado):
        flota.registrar_base(BaseOperativa("base-1", "Otra", Ubicacion("x", "y")))


def test_la_unidad_se_construye_con_los_recursos_pedidos_sin_aliasing_de_listas():
    jefe = persona("j", CONDUCCION)
    otros = [persona("k", EVACUACION)]
    unidad = Unidad("u1", "base-1", jefe, TransportePersonas(id="v", capacidad_evacuados=4), tuple(otros))

    otros.append(persona("intruso", EVACUACION))

    assert not unidad.tiene_persona("intruso")
    assert isinstance(unidad.personal, tuple)
