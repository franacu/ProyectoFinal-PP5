"""Ejecución, rechazo, reasignación y cancelación de misiones (§2.3, §8.1, §8.3). PV11–PV15.

Las transiciones se prueban contra la tabla de estados: lo que no está permitido se rechaza.
"""

import pytest

from dominio.catalogos import ResultadoMision
from dominio.errores import (
    JustificacionVacia,
    MisionEnEstadoInvalido,
    MisionInvalida,
    NoEsJefeDeLaUnidad,
    ResultadoInvalido,
    UnidadOcupada,
    VehiculoIncompatible,
)
from dominio.mision import EstadoMision, Rescate
from tests.escenarios import emergencia, t, unidad_de_evacuacion, unidad_de_rescate


def mision_asignada(unidad=None):
    """Emergencia abierta con una misión de rescate asignada a una unidad (el 'jefe' es ur-jefe)."""
    emerg = emergencia()
    mision = Rescate("Rescatar familia aislada")
    unidad = unidad or unidad_de_rescate("ur")
    emerg.crear_mision(mision, "op-1", t())
    emerg.asignar_mision(mision.id, unidad, "op-1", t(1))
    return emerg, mision, unidad


def mision_en_ejecucion():
    emerg, mision, unidad = mision_asignada()
    emerg.iniciar_mision(mision.id, "ur-jefe", t(2))
    return emerg, mision, unidad


# ── PV11: ejecución ───────────────────────────────────────────

def test_pv11_el_jefe_inicia_registra_novedad_y_finaliza_liberando_la_unidad():
    emerg, mision, unidad = mision_asignada()
    assert mision.estado is EstadoMision.ASIGNADA

    emerg.iniciar_mision(mision.id, "ur-jefe", t(2))
    assert mision.estado is EstadoMision.EN_EJECUCION
    assert unidad.mision_comprometida_id == mision.id

    emerg.registrar_novedad(mision.id, "ur-jefe", "Acceso complicado por el agua", t(3))
    assert [n.texto for n in emerg.misiones[0].novedades] == ["Acceso complicado por el agua"]

    emerg.finalizar_mision(mision.id, "ur-jefe", ResultadoMision.SATISFACTORIO, "Rescatadas 3 personas", t(4))

    assert mision.estado is EstadoMision.FINALIZADA
    assert unidad.mision_comprometida_id is None
    assert emerg.misiones[0].resultado.satisfactorio is True
    assert emerg.misiones[0].resultado.tareas == "Rescatadas 3 personas"


def test_el_resultado_no_satisfactorio_tambien_finaliza_y_libera_la_unidad():
    emerg, mision, unidad = mision_en_ejecucion()

    emerg.finalizar_mision(mision.id, "ur-jefe", ResultadoMision.NO_SATISFACTORIO, "No se llegó al lugar", t(4))

    assert mision.estado is EstadoMision.FINALIZADA
    assert unidad.mision_comprometida_id is None
    assert emerg.misiones[0].resultado.satisfactorio is False


@pytest.mark.parametrize("resultado, tareas", [
    ("exitoso", "Tareas"),
    (ResultadoMision.SATISFACTORIO, ""),
    (ResultadoMision.SATISFACTORIO, "   "),
    (None, "Tareas"),
])
def test_finalizar_sin_resultado_valido_o_sin_tareas_se_rechaza_y_la_mision_sigue_en_ejecucion(resultado, tareas):
    emerg, mision, unidad = mision_en_ejecucion()

    with pytest.raises(ResultadoInvalido):
        emerg.finalizar_mision(mision.id, "ur-jefe", resultado, tareas, t(4))

    assert mision.estado is EstadoMision.EN_EJECUCION
    assert unidad.mision_comprometida_id == mision.id
    assert len(emerg.registros) == 4  # creada + mision creada + asignada + iniciada


def test_la_novedad_solo_se_registra_durante_la_ejecucion():
    emerg, mision, _ = mision_asignada()

    with pytest.raises(MisionEnEstadoInvalido):
        emerg.registrar_novedad(mision.id, "ur-jefe", "Todavía no empezó", t(2))

    assert emerg.misiones[0].novedades == ()


def test_una_novedad_vacia_se_rechaza():
    emerg, mision, _ = mision_en_ejecucion()

    with pytest.raises(MisionInvalida):
        emerg.registrar_novedad(mision.id, "ur-jefe", "  ", t(3))

    assert emerg.misiones[0].novedades == ()


# ── PV12: restricciones de responsabilidad (parte de dominio) ─

def test_pv12_un_jefe_no_puede_finalizar_una_mision_de_otra_unidad():
    emerg, mision, unidad = mision_en_ejecucion()

    with pytest.raises(NoEsJefeDeLaUnidad):
        emerg.finalizar_mision(mision.id, "otra-jefe", ResultadoMision.SATISFACTORIO, "Tareas", t(4))

    assert mision.estado is EstadoMision.EN_EJECUCION
    assert unidad.mision_comprometida_id == mision.id


@pytest.mark.parametrize("operacion", ["iniciar", "rechazar", "novedad"])
def test_pv12_un_jefe_ajeno_no_inicia_ni_rechaza_ni_registra_novedades(operacion):
    emerg, mision, _ = mision_asignada()
    if operacion == "novedad":
        emerg.iniciar_mision(mision.id, "ur-jefe", t(2))
    acciones = {
        "iniciar": lambda: emerg.iniciar_mision(mision.id, "intruso", t(3)),
        "rechazar": lambda: emerg.rechazar_mision(mision.id, "intruso", "no quiero", t(3)),
        "novedad": lambda: emerg.registrar_novedad(mision.id, "intruso", "hola", t(3)),
    }

    with pytest.raises(NoEsJefeDeLaUnidad):
        acciones[operacion]()


def test_pv12_el_jefe_de_una_misión_pendiente_no_existe_porque_no_tiene_unidad():
    emerg = emergencia()
    mision = Rescate("Rescatar")
    emerg.crear_mision(mision, "op-1", t())

    with pytest.raises(MisionEnEstadoInvalido):
        emerg.iniciar_mision(mision.id, "ur-jefe", t(1))


# ── PV13: rechazo y reasignación ──────────────────────────────

def test_pv13_el_jefe_rechaza_con_justificacion_la_mision_vuelve_a_pendiente_y_la_unidad_se_libera():
    emerg, mision, unidad = mision_asignada()

    emerg.rechazar_mision(mision.id, "ur-jefe", "Vehículo con falla mecánica", t(2))

    assert mision.estado is EstadoMision.PENDIENTE
    assert mision.unidad_id is None
    assert unidad.mision_comprometida_id is None


def test_pv13_tras_el_rechazo_el_operador_la_asigna_a_otra_unidad_apta():
    emerg, mision, _ = mision_asignada()
    emerg.rechazar_mision(mision.id, "ur-jefe", "Vehículo con falla mecánica", t(2))
    otra = unidad_de_rescate("ur2")

    emerg.asignar_mision(mision.id, otra, "op-1", t(3))

    assert mision.estado is EstadoMision.ASIGNADA
    assert mision.unidad_id == "ur2"


@pytest.mark.parametrize("justificacion", [None, "", "   "])
def test_pv13_rechazar_sin_justificacion_se_rechaza_y_la_asignacion_sigue(justificacion):
    emerg, mision, unidad = mision_asignada()

    with pytest.raises(JustificacionVacia):
        emerg.rechazar_mision(mision.id, "ur-jefe", justificacion, t(2))

    assert mision.estado is EstadoMision.ASIGNADA
    assert unidad.mision_comprometida_id == mision.id


def test_pv13_reasignacion_directa_libera_la_unidad_anterior_y_compromete_la_nueva():
    emerg, mision, anterior = mision_asignada()
    nueva = unidad_de_rescate("ur2")

    emerg.reasignar_mision(mision.id, nueva, "op-1", t(2))

    assert mision.estado is EstadoMision.ASIGNADA
    assert mision.unidad_id == "ur2"
    assert anterior.mision_comprometida_id is None
    assert nueva.mision_comprometida_id == mision.id


def test_pv13_no_se_rechaza_ni_se_reasigna_una_mision_en_ejecucion():
    emerg, mision, unidad = mision_en_ejecucion()

    with pytest.raises(MisionEnEstadoInvalido):
        emerg.rechazar_mision(mision.id, "ur-jefe", "ya no quiero", t(3))
    with pytest.raises(MisionEnEstadoInvalido):
        emerg.reasignar_mision(mision.id, unidad_de_rescate("ur2"), "op-1", t(3))

    assert mision.estado is EstadoMision.EN_EJECUCION
    assert mision.unidad_id == "ur"
    assert unidad.mision_comprometida_id == mision.id


def test_una_mision_pendiente_no_se_reasigna():
    emerg = emergencia()
    mision = Rescate("Rescatar")
    emerg.crear_mision(mision, "op-1", t())

    with pytest.raises(MisionEnEstadoInvalido):
        emerg.reasignar_mision(mision.id, unidad_de_rescate("ur"), "op-1", t(1))


def test_pv18_reasignar_a_una_unidad_que_no_cumple_conserva_la_asignacion_y_a_ambas_unidades():
    emerg, mision, anterior = mision_asignada()
    inapta = unidad_de_evacuacion("ue")
    registros_antes = emerg.registros

    with pytest.raises(VehiculoIncompatible):
        emerg.reasignar_mision(mision.id, inapta, "op-1", t(3))

    assert mision.unidad_id == "ur"
    assert anterior.mision_comprometida_id == mision.id
    assert inapta.mision_comprometida_id is None
    assert emerg.registros == registros_antes  # no se registra como realizada


def test_reasignar_a_una_unidad_ocupada_conserva_la_asignacion_original():
    emerg, mision, anterior = mision_asignada()
    ocupada = unidad_de_rescate("ur2")
    otra = Rescate("Otro rescate")
    emerg.crear_mision(otra, "op-1", t(2))
    emerg.asignar_mision(otra.id, ocupada, "op-1", t(3))

    with pytest.raises(UnidadOcupada):
        emerg.reasignar_mision(mision.id, ocupada, "op-1", t(4))

    assert mision.unidad_id == "ur"
    assert ocupada.mision_comprometida_id == otra.id
    assert anterior.mision_comprometida_id == mision.id


def test_reasignar_a_la_misma_unidad_se_rechaza():
    emerg, mision, unidad = mision_asignada()

    with pytest.raises(UnidadOcupada):
        emerg.reasignar_mision(mision.id, unidad, "op-1", t(2))

    assert unidad.mision_comprometida_id == mision.id


# ── PV15: cancelación ─────────────────────────────────────────

def test_pv15_cancelar_una_mision_asignada_libera_la_unidad_y_queda_cancelada():
    emerg, mision, unidad = mision_asignada()

    emerg.cancelar_mision(mision.id, "op-1", t(2))

    assert mision.estado is EstadoMision.CANCELADA
    assert mision.unidad_id is None
    assert unidad.mision_comprometida_id is None


def test_pv15_una_mision_cancelada_no_puede_iniciarse_ni_asignarse_ni_reabrirse():
    emerg, mision, unidad = mision_asignada()
    emerg.cancelar_mision(mision.id, "op-1", t(2))

    with pytest.raises(MisionEnEstadoInvalido):
        emerg.iniciar_mision(mision.id, "ur-jefe", t(3))
    with pytest.raises(MisionEnEstadoInvalido):
        emerg.asignar_mision(mision.id, unidad, "op-1", t(3))
    with pytest.raises(MisionEnEstadoInvalido):
        emerg.cancelar_mision(mision.id, "op-1", t(3))

    assert mision.estado is EstadoMision.CANCELADA


def test_se_puede_cancelar_una_mision_pendiente_sin_unidad():
    emerg = emergencia()
    mision = Rescate("Rescatar")
    emerg.crear_mision(mision, "op-1", t())

    emerg.cancelar_mision(mision.id, "op-1", t(1))

    assert mision.estado is EstadoMision.CANCELADA


def test_no_se_cancela_una_mision_en_ejecucion_ni_finalizada():
    emerg, mision, unidad = mision_en_ejecucion()

    with pytest.raises(MisionEnEstadoInvalido):
        emerg.cancelar_mision(mision.id, "op-1", t(3))
    assert mision.estado is EstadoMision.EN_EJECUCION

    emerg.finalizar_mision(mision.id, "ur-jefe", ResultadoMision.SATISFACTORIO, "Tareas", t(4))
    with pytest.raises(MisionEnEstadoInvalido):
        emerg.cancelar_mision(mision.id, "op-1", t(5))
    assert mision.estado is EstadoMision.FINALIZADA


def test_una_mision_finalizada_no_se_reabre():
    emerg, mision, _ = mision_en_ejecucion()
    emerg.finalizar_mision(mision.id, "ur-jefe", ResultadoMision.SATISFACTORIO, "Tareas", t(4))

    for operacion in (
        lambda: emerg.iniciar_mision(mision.id, "ur-jefe", t(5)),
        lambda: emerg.finalizar_mision(mision.id, "ur-jefe", ResultadoMision.SATISFACTORIO, "otra vez", t(5)),
        lambda: emerg.rechazar_mision(mision.id, "ur-jefe", "tarde", t(5)),
        lambda: emerg.registrar_novedad(mision.id, "ur-jefe", "tarde", t(5)),
    ):
        with pytest.raises(MisionEnEstadoInvalido):
            operacion()

    assert mision.estado is EstadoMision.FINALIZADA
