"""Asignación de misiones a unidades (§8.2). PV06–PV10.

Cada rechazo se mira desde tres lados: el motivo, la misión (sigue pendiente)
y la unidad (sigue libre).
"""

import pytest

from dominio.catalogos import CategoriaEquipo, CondicionOperativa, ResultadoMision
from dominio.equipamiento import Equipo
from dominio.errores import (
    EmergenciaCerrada,
    EquipamientoInsuficiente,
    MisionEnEstadoInvalido,
    MisionInvalida,
    PersonalInsuficiente,
    UnidadNoHabilitada,
    UnidadOcupada,
    VehiculoIncompatible,
)
from dominio.mision import AsistenciaSanitaria, EstadoMision, Evacuacion, Rescate
from dominio.unidad import Unidad
from dominio.vehiculos import Ambulancia, TransportePersonas, VehiculoRescate
from tests.escenarios import (
    CONDUCCION,
    EVACUACION,
    PRIMEROS_AUXILIOS,
    RESCATE,
    emergencia,
    flota_con,
    persona,
    t,
    unidad_de_evacuacion,
    unidad_de_rescate,
    unidad_sanitaria,
)


def con_mision(mision):
    emerg = emergencia()
    emerg.crear_mision(mision, "op-1", t())
    return emerg, mision


def asignar(emerg, mision, unidad):
    emerg.asignar_mision(mision.id, unidad, "op-1", t(10))


def assert_rechazada_sin_cambios(emerg, mision, unidad):
    vista = emerg.misiones[0]
    assert mision.estado is EstadoMision.PENDIENTE
    assert vista.unidad_id is None
    assert unidad.mision_comprometida_id is None


# ── PV06: capacidad de transporte ─────────────────────────────

def test_pv06_vehiculo_de_seis_plazas_no_alcanza_para_evacuar_ocho_personas():
    emerg, mision = con_mision(Evacuacion("Evacuar barrio costero", 8))
    unidad = unidad_de_evacuacion("ue", capacidad=6)

    with pytest.raises(VehiculoIncompatible, match="Capacidad insuficiente"):
        asignar(emerg, mision, unidad)

    assert_rechazada_sin_cambios(emerg, mision, unidad)


def test_pv06_unidad_con_capacidad_suficiente_y_personal_competente_se_acepta():
    emerg, mision = con_mision(Evacuacion("Evacuar barrio costero", 8))
    unidad = unidad_de_evacuacion("ue", capacidad=8)

    asignar(emerg, mision, unidad)

    assert mision.estado is EstadoMision.ASIGNADA
    assert mision.unidad_id == "ue"
    assert unidad.mision_comprometida_id == mision.id


def test_pv06_evacuacion_exige_conductor_y_otra_persona_con_evacuacion():
    emerg, mision = con_mision(Evacuacion("Evacuar", 2))
    solo_conductor = Unidad("u1", "base-1", persona("j", CONDUCCION),
                            TransportePersonas(id="v", capacidad_evacuados=10))

    with pytest.raises(PersonalInsuficiente):
        asignar(emerg, mision, solo_conductor)

    assert_rechazada_sin_cambios(emerg, mision, solo_conductor)


def test_pv06_el_conductor_no_puede_ser_tambien_el_evacuador():
    emerg, mision = con_mision(Evacuacion("Evacuar", 2))
    una_persona = Unidad("u1", "base-1", persona("j", CONDUCCION, EVACUACION),
                         TransportePersonas(id="v", capacidad_evacuados=10))

    with pytest.raises(PersonalInsuficiente):
        asignar(emerg, mision, una_persona)


def test_evacuacion_no_requiere_equipamiento_especializado():
    emerg, mision = con_mision(Evacuacion("Evacuar", 2))
    sin_equipo = unidad_de_evacuacion("ue")
    assert sin_equipo.equipamiento == ()

    asignar(emerg, mision, sin_equipo)

    assert mision.estado is EstadoMision.ASIGNADA


@pytest.mark.parametrize("cantidad", [0, -1, None, "8", 2.5])
def test_evacuacion_exige_una_cantidad_entera_positiva(cantidad):
    with pytest.raises(MisionInvalida):
        Evacuacion("Evacuar", cantidad)


# ── PV07: competencias y cantidad de integrantes ──────────────

def test_pv07_rescate_con_un_conductor_y_un_unico_rescatista_se_rechaza():
    emerg, mision = con_mision(Rescate("Rescatar atrapados"))
    unidad = Unidad("u1", "base-1", persona("j", CONDUCCION), VehiculoRescate(id="v"),
                    personal=(persona("r", RESCATE),),
                    equipamiento=(Equipo("e", CategoriaEquipo.EQUIPO_DE_RESCATE),))

    with pytest.raises(PersonalInsuficiente):
        asignar(emerg, mision, unidad)

    assert_rechazada_sin_cambios(emerg, mision, unidad)


def test_pv07_al_incorporar_un_segundo_rescatista_la_asignacion_se_acepta():
    emerg, mision = con_mision(Rescate("Rescatar atrapados"))
    unidad = Unidad("u1", "base-1", persona("j", CONDUCCION), VehiculoRescate(id="v"),
                    personal=(persona("r", RESCATE),),
                    equipamiento=(Equipo("e", CategoriaEquipo.EQUIPO_DE_RESCATE),))
    with pytest.raises(PersonalInsuficiente):
        asignar(emerg, mision, unidad)

    unidad.incorporar_personal(persona("r2", RESCATE), "resp-1", t(5))
    asignar(emerg, mision, unidad)

    assert mision.estado is EstadoMision.ASIGNADA


def test_pv07_ana_bruno_y_carla_cubren_un_rescate_aunque_ana_tenga_dos_competencias():
    emerg, mision = con_mision(Rescate("Rescatar atrapados"))
    unidad = Unidad("u1", "base-1", persona("ana", CONDUCCION, RESCATE), VehiculoRescate(id="v"),
                    personal=(persona("bruno", CONDUCCION), persona("carla", RESCATE)),
                    equipamiento=(Equipo("e", CategoriaEquipo.EQUIPO_DE_RESCATE),))

    asignar(emerg, mision, unidad)

    assert mision.estado is EstadoMision.ASIGNADA


# ── PV08: compatibilidad de vehículos ─────────────────────────

def test_pv08_asistencia_sanitaria_con_vehiculo_de_transporte_se_rechaza_aunque_haya_primeros_auxilios():
    emerg, mision = con_mision(AsistenciaSanitaria("Asistir heridos"))
    unidad = Unidad("u1", "base-1", persona("j", CONDUCCION), TransportePersonas(id="v", capacidad_evacuados=10),
                    personal=(persona("p", PRIMEROS_AUXILIOS),),
                    equipamiento=(Equipo("e", CategoriaEquipo.EQUIPO_SANITARIO),))

    with pytest.raises(VehiculoIncompatible):
        asignar(emerg, mision, unidad)

    assert_rechazada_sin_cambios(emerg, mision, unidad)


def test_pv08_rescate_con_ambulancia_se_rechaza():
    emerg, mision = con_mision(Rescate("Rescatar"))
    unidad = Unidad("u1", "base-1", persona("j", CONDUCCION), Ambulancia(id="v"),
                    personal=(persona("r1", RESCATE), persona("r2", RESCATE)),
                    equipamiento=(Equipo("e", CategoriaEquipo.EQUIPO_DE_RESCATE),))

    with pytest.raises(VehiculoIncompatible):
        asignar(emerg, mision, unidad)


def test_evacuacion_con_vehiculo_de_rescate_se_rechaza():
    emerg, mision = con_mision(Evacuacion("Evacuar", 2))
    unidad = Unidad("u1", "base-1", persona("j", CONDUCCION), VehiculoRescate(id="v"),
                    personal=(persona("e", EVACUACION),))

    with pytest.raises(VehiculoIncompatible):
        asignar(emerg, mision, unidad)


def test_vehiculo_fuera_de_servicio_no_puede_usarse_en_una_mision():
    emerg, mision = con_mision(AsistenciaSanitaria("Asistir"))
    unidad = unidad_sanitaria("us")
    unidad.cambiar_condicion_vehiculo(CondicionOperativa.FUERA_DE_SERVICIO, "resp-1", t(1))

    with pytest.raises(VehiculoIncompatible, match="fuera de servicio"):
        asignar(emerg, mision, unidad)

    assert_rechazada_sin_cambios(emerg, mision, unidad)


# ── PV09: equipamiento no operativo ───────────────────────────

def test_pv09_equipo_de_rescate_fuera_de_servicio_impide_la_asignacion_hasta_restablecerlo():
    emerg, mision = con_mision(Rescate("Rescatar"))
    unidad = unidad_de_rescate("ur")
    unidad.cambiar_condicion_equipo("ur-equipo", CondicionOperativa.FUERA_DE_SERVICIO, "resp-1", t(1))

    with pytest.raises(EquipamientoInsuficiente):
        asignar(emerg, mision, unidad)
    assert_rechazada_sin_cambios(emerg, mision, unidad)

    unidad.cambiar_condicion_equipo("ur-equipo", CondicionOperativa.OPERATIVO, "resp-1", t(2))
    asignar(emerg, mision, unidad)

    assert mision.estado is EstadoMision.ASIGNADA


def test_pv09_un_equipo_operativo_alcanza_aunque_haya_otro_fuera_de_servicio():
    emerg, mision = con_mision(Rescate("Rescatar"))
    unidad = unidad_de_rescate("ur")
    unidad.incorporar_equipo(Equipo("ur-roto", CategoriaEquipo.EQUIPO_DE_RESCATE,
                                    CondicionOperativa.FUERA_DE_SERVICIO), "resp-1", t(1))

    asignar(emerg, mision, unidad)

    assert mision.estado is EstadoMision.ASIGNADA


def test_equipo_de_otra_categoria_no_satisface_el_requisito_de_la_mision():
    emerg, mision = con_mision(AsistenciaSanitaria("Asistir"))
    unidad = Unidad("u1", "base-1", persona("j", CONDUCCION), Ambulancia(id="v"),
                    personal=(persona("p", PRIMEROS_AUXILIOS),),
                    equipamiento=(Equipo("e", CategoriaEquipo.EQUIPO_DE_RESCATE),))

    with pytest.raises(EquipamientoInsuficiente):
        asignar(emerg, mision, unidad)


# ── PV10: exclusividad ────────────────────────────────────────

def test_pv10_unidad_asignada_rechaza_una_segunda_mision_sin_alterar_la_primera():
    emerg = emergencia()
    primera, segunda = Rescate("Rescate 1"), Rescate("Rescate 2")
    emerg.crear_mision(primera, "op-1", t())
    emerg.crear_mision(segunda, "op-1", t())
    unidad = unidad_de_rescate("ur")
    emerg.asignar_mision(primera.id, unidad, "op-1", t(1))

    with pytest.raises(UnidadOcupada):
        emerg.asignar_mision(segunda.id, unidad, "op-1", t(2))

    assert primera.estado is EstadoMision.ASIGNADA and primera.unidad_id == "ur"
    assert segunda.estado is EstadoMision.PENDIENTE and segunda.unidad_id is None
    assert unidad.mision_comprometida_id == primera.id


def test_pv10_unidad_ejecutando_una_mision_tampoco_recibe_otra():
    emerg = emergencia()
    primera, segunda = Rescate("Rescate 1"), Rescate("Rescate 2")
    emerg.crear_mision(primera, "op-1", t())
    emerg.crear_mision(segunda, "op-1", t())
    unidad = unidad_de_rescate("ur")
    emerg.asignar_mision(primera.id, unidad, "op-1", t(1))
    emerg.iniciar_mision(primera.id, "ur-jefe", t(2))

    with pytest.raises(UnidadOcupada):
        emerg.asignar_mision(segunda.id, unidad, "op-1", t(3))

    assert unidad.mision_comprometida_id == primera.id


# ── §8.2 / §8.4: habilitación y estado de la misión ───────────

@pytest.mark.parametrize("declarar", ["declarar_en_mantenimiento", "declarar_fuera_de_servicio"])
def test_unidad_en_mantenimiento_o_fuera_de_servicio_no_recibe_misiones(declarar):
    emerg, mision = con_mision(Rescate("Rescatar"))
    unidad = unidad_de_rescate("ur")
    getattr(unidad, declarar)("resp-1", t(1))

    with pytest.raises(UnidadNoHabilitada):
        asignar(emerg, mision, unidad)

    assert_rechazada_sin_cambios(emerg, mision, unidad)


def test_una_mision_asignada_no_se_vuelve_a_asignar_se_reasigna():
    emerg, mision = con_mision(Rescate("Rescatar"))
    asignar(emerg, mision, unidad_de_rescate("ur"))

    with pytest.raises(MisionEnEstadoInvalido):
        asignar(emerg, mision, unidad_de_rescate("ur2"))


def test_no_se_asigna_en_una_emergencia_cerrada():
    cerrada = emergencia()
    mision = Rescate("Rescatar")
    cerrada.crear_mision(mision, "op-1", t())
    unidad = unidad_de_rescate("ur")
    cerrada.asignar_mision(mision.id, unidad, "op-1", t(1))
    cerrada.iniciar_mision(mision.id, "ur-jefe", t(2))
    cerrada.finalizar_mision(mision.id, "ur-jefe", ResultadoMision.SATISFACTORIO, "Rescatadas 3 personas", t(3))
    cerrada.cerrar("sup-1", t(4))
    otra = unidad_de_rescate("ur2")

    with pytest.raises(EmergenciaCerrada):
        cerrada.asignar_mision(mision.id, otra, "op-1", t(5))

    assert otra.mision_comprometida_id is None
