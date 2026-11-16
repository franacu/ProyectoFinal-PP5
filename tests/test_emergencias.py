"""Emergencias (§4, §7.2): prioridad, misiones, cierre e historial. PV03–PV05, PV16–PV18."""

import pytest

from dominio.catalogos import Gravedad, ResultadoMision, TipoSituacion
from dominio.emergencia import EstadoEmergencia, abiertas_por_prioridad
from dominio.errores import (
    EmergenciaCerrada,
    MisionEnEstadoInvalido,
    MisionIncompatible,
    MisionInvalida,
    MisionSinConcluir,
    NoEncontrado,
    NoEsJefeDeLaUnidad,
    SinMisionExitosa,
    VehiculoIncompatible,
)
from dominio.historial import Operacion
from dominio.mision import AsistenciaSanitaria, EstadoMision, Evacuacion, Rescate
from tests.escenarios import (
    RESCATE,
    aviso,
    emergencia,
    flota_con,
    persona,
    t,
    unidad_de_evacuacion,
    unidad_de_rescate,
    unidad_sanitaria,
)


# ── PV03: prioridad ───────────────────────────────────────────

def test_pv03_las_abiertas_salen_ordenadas_alta_media_baja():
    baja = emergencia(gravedad=Gravedad.BAJA, aceptada=t(1))
    alta = emergencia(gravedad=Gravedad.ALTA, aceptada=t(2))
    media = emergencia(gravedad=Gravedad.MEDIA, aceptada=t(3))

    orden = abiertas_por_prioridad([baja, alta, media])

    assert [e.gravedad for e in orden] == [Gravedad.ALTA, Gravedad.MEDIA, Gravedad.BAJA]


def test_pv03_a_igual_gravedad_va_primero_la_aceptada_antes_aunque_el_aviso_se_registrara_despues():
    # el aviso A se registra a las 10:00 y se acepta tarde; el B se registra a las 10:30 y se acepta antes
    aviso_a = aviso("rep-1", gravedad=Gravedad.ALTA, registrado=t(0))
    aviso_b = aviso("rep-2", gravedad=Gravedad.ALTA, registrado=t(30))
    emerg_a = aviso_a.aceptar("op-1", TipoSituacion.INUNDACION, Gravedad.ALTA, t(50))
    emerg_b = aviso_b.aceptar("op-1", TipoSituacion.INUNDACION, Gravedad.ALTA, t(40))

    orden = abiertas_por_prioridad([emerg_a, emerg_b])

    assert orden == (emerg_b, emerg_a)


def test_pv03_la_prioridad_usa_la_gravedad_confirmada_no_la_estimada():
    estimada_baja = aviso("rep-1", gravedad=Gravedad.BAJA)
    confirmada_alta = estimada_baja.aceptar("op-1", TipoSituacion.INUNDACION, Gravedad.ALTA, t(5))
    media = emergencia(gravedad=Gravedad.MEDIA, aceptada=t(1))

    assert abiertas_por_prioridad([media, confirmada_alta])[0] is confirmada_alta


def test_pv03_las_cerradas_no_aparecen_en_la_lista_de_abiertas():
    cerrada = emergencia(gravedad=Gravedad.ALTA)
    unidad = unidad_de_rescate("ur")
    mision = Rescate("Rescatar")
    cerrada.crear_mision(mision, "op-1", t())
    cerrada.asignar_mision(mision.id, unidad, "op-1", t(1))
    cerrada.iniciar_mision(mision.id, "ur-jefe", t(2))
    cerrada.finalizar_mision(mision.id, "ur-jefe", ResultadoMision.SATISFACTORIO, "Hecho", t(3))
    cerrada.cerrar("sup-1", t(4))
    abierta = emergencia(gravedad=Gravedad.BAJA)

    assert abiertas_por_prioridad([cerrada, abierta]) == (abierta,)


# ── PV04: varias misiones por emergencia ──────────────────────

def test_pv04_una_inundacion_admite_evacuacion_rescate_y_asistencia_cada_una_con_su_estado():
    emerg = emergencia(TipoSituacion.INUNDACION)
    evacuacion = Evacuacion("Evacuar ocho personas", 8)
    rescate = Rescate("Rescatar familia en techo")
    asistencia = AsistenciaSanitaria("Asistir heridos")
    for m in (evacuacion, rescate, asistencia):
        emerg.crear_mision(m, "op-1", t())

    emerg.asignar_mision(rescate.id, unidad_de_rescate("ur"), "op-1", t(1))

    estados = {v.tipo.value: v.estado for v in emerg.misiones}
    assert estados == {"evacuacion": EstadoMision.PENDIENTE,
                       "rescate": EstadoMision.ASIGNADA,
                       "asistencia_sanitaria": EstadoMision.PENDIENTE}


def test_pv04_se_pueden_crear_varias_misiones_del_mismo_tipo_en_una_emergencia():
    emerg = emergencia()

    emerg.crear_mision(Rescate("Rescate en zona norte"), "op-1", t())
    emerg.crear_mision(Rescate("Rescate en zona sur"), "op-1", t())

    assert len(emerg.misiones) == 2


def test_registrar_una_emergencia_no_genera_misiones_automaticamente():
    assert emergencia().misiones == ()


# ── PV05: compatibilidad situación–misión (§6.4) ──────────────

def test_pv05_evacuacion_en_accidente_vial_se_rechaza_y_no_se_agrega():
    emerg = emergencia(TipoSituacion.ACCIDENTE_VIAL)

    with pytest.raises(MisionIncompatible):
        emerg.crear_mision(Evacuacion("Evacuar", 4), "op-1", t())

    assert emerg.misiones == ()
    assert len(emerg.registros) == 1  # solo la creación de la emergencia


def test_pv05_despues_se_crean_rescate_y_asistencia_para_el_accidente_vial():
    emerg = emergencia(TipoSituacion.ACCIDENTE_VIAL)
    with pytest.raises(MisionIncompatible):
        emerg.crear_mision(Evacuacion("Evacuar", 4), "op-1", t())

    emerg.crear_mision(Rescate("Rescatar atrapados"), "op-1", t(1))
    emerg.crear_mision(AsistenciaSanitaria("Asistir lesionados"), "op-1", t(2))

    assert len(emerg.misiones) == 2


@pytest.mark.parametrize("situacion", [TipoSituacion.INUNDACION, TipoSituacion.INCENDIO])
@pytest.mark.parametrize("mision", [lambda: Evacuacion("x", 2), lambda: Rescate("x"),
                                    lambda: AsistenciaSanitaria("x")])
def test_la_tabla_de_compatibilidad_admite_todo_para_inundacion_e_incendio(situacion, mision):
    emerg = emergencia(situacion)

    emerg.crear_mision(mision(), "op-1", t())

    assert len(emerg.misiones) == 1


@pytest.mark.parametrize("objetivo", [None, "", "   "])
def test_una_mision_sin_objetivo_se_rechaza(objetivo):
    with pytest.raises(MisionInvalida):
        Rescate(objetivo)


def test_operar_sobre_una_mision_inexistente_se_rechaza():
    emerg = emergencia()

    with pytest.raises(NoEncontrado):
        emerg.cancelar_mision("no-existe", "op-1", t())


def test_las_misiones_salen_como_vistas_de_solo_lectura():
    emerg = emergencia()
    mision = Rescate("Rescatar")
    emerg.crear_mision(mision, "op-1", t())

    vista = emerg.misiones[0]

    assert not hasattr(vista, "cancelar")
    with pytest.raises(AttributeError):
        vista.estado = EstadoMision.CANCELADA  # type: ignore[misc]


# ── PV16: cierre ──────────────────────────────────────────────

def emergencia_con_mision_en(estado: str):
    """Emergencia con una misión llevada hasta el estado pedido."""
    emerg = emergencia()
    mision = Rescate("Rescatar")
    emerg.crear_mision(mision, "op-1", t())
    if estado == "pendiente":
        return emerg
    unidad = unidad_de_rescate("ur")
    emerg.asignar_mision(mision.id, unidad, "op-1", t(1))
    if estado == "asignada":
        return emerg
    emerg.iniciar_mision(mision.id, "ur-jefe", t(2))
    if estado == "en_ejecucion":
        return emerg
    resultado = (ResultadoMision.SATISFACTORIO if estado == "finalizada_ok"
                 else ResultadoMision.NO_SATISFACTORIO)
    emerg.finalizar_mision(mision.id, "ur-jefe", resultado, "Tareas realizadas", t(3))
    return emerg


@pytest.mark.parametrize("estado", ["pendiente", "asignada", "en_ejecucion"])
def test_pv16_no_se_cierra_con_misiones_pendientes_asignadas_o_en_ejecucion(estado):
    emerg = emergencia_con_mision_en(estado)

    with pytest.raises(MisionSinConcluir):
        emerg.cerrar("sup-1", t(9))

    assert emerg.estado is EstadoEmergencia.ABIERTA
    assert emerg.registros[-1].operacion is not Operacion.EMERGENCIA_CERRADA


def test_pv16_no_se_cierra_una_emergencia_sin_misiones_y_sigue_admitiendo_nuevas():
    emerg = emergencia()

    with pytest.raises(SinMisionExitosa):
        emerg.cerrar("sup-1", t(9))
    emerg.crear_mision(Rescate("Rescatar"), "op-1", t(10))

    assert emerg.estado is EstadoEmergencia.ABIERTA
    assert len(emerg.misiones) == 1


def test_pv16_no_se_cierra_si_todas_estan_canceladas():
    emerg = emergencia()
    mision = Rescate("Rescatar")
    emerg.crear_mision(mision, "op-1", t())
    emerg.cancelar_mision(mision.id, "op-1", t(1))

    with pytest.raises(SinMisionExitosa):
        emerg.cerrar("sup-1", t(9))

    assert emerg.estado is EstadoEmergencia.ABIERTA


def test_pv16_no_se_cierra_si_la_unica_finalizada_no_fue_satisfactoria_y_admite_nuevas_misiones():
    emerg = emergencia_con_mision_en("finalizada_mal")

    with pytest.raises(SinMisionExitosa):
        emerg.cerrar("sup-1", t(9))
    emerg.crear_mision(Rescate("Reintentar el rescate"), "op-1", t(10))

    assert emerg.estado is EstadoEmergencia.ABIERTA
    assert len(emerg.misiones) == 2


def test_pv16_se_cierra_con_todas_concluidas_y_al_menos_una_satisfactoria():
    emerg = emergencia_con_mision_en("finalizada_ok")
    cancelada = Rescate("Otro rescate")
    emerg.crear_mision(cancelada, "op-1", t(4))
    emerg.cancelar_mision(cancelada.id, "op-1", t(5))

    emerg.cerrar("sup-1", t(9))

    assert emerg.estado is EstadoEmergencia.CERRADA


def test_pv16_una_pendiente_junto_a_una_satisfactoria_impide_el_cierre():
    emerg = emergencia_con_mision_en("finalizada_ok")
    emerg.crear_mision(Rescate("Todavía sin resolver"), "op-1", t(4))

    with pytest.raises(MisionSinConcluir):
        emerg.cerrar("sup-1", t(9))


def test_pv16_cerrada_no_admite_nuevas_misiones_ni_operaciones_ni_otro_cierre():
    emerg = emergencia_con_mision_en("finalizada_ok")
    emerg.cerrar("sup-1", t(9))
    cantidad = len(emerg.misiones)
    registros = emerg.registros

    for operacion in (
        lambda: emerg.crear_mision(Rescate("Nueva"), "op-1", t(10)),
        lambda: emerg.cerrar("sup-1", t(10)),
        lambda: emerg.registrar_novedad(emerg.misiones[0].id, "ur-jefe", "tarde", t(10)),
        lambda: emerg.cancelar_mision(emerg.misiones[0].id, "op-1", t(10)),
    ):
        with pytest.raises(EmergenciaCerrada):
            operacion()

    assert len(emerg.misiones) == cantidad
    assert emerg.registros == registros


# ── PV17: historial ───────────────────────────────────────────

def emergencia_con_reasignacion():
    emerg = emergencia()
    mision = Rescate("Rescatar")
    emerg.crear_mision(mision, "op-1", t(1))
    flota = flota_con(unidad_de_rescate("ur"), unidad_de_rescate("ur2"))
    emerg.asignar_mision(mision.id, flota.unidad("ur"), "op-2", t(2))
    emerg.reasignar_mision(mision.id, flota.unidad("ur2"), "op-3", t(3))
    emerg.iniciar_mision(mision.id, "ur2-jefe", t(4))
    emerg.finalizar_mision(mision.id, "ur2-jefe", ResultadoMision.SATISFACTORIO, "Rescatadas 2 personas", t(5))
    return emerg, mision, flota


def test_pv17_cada_registro_identifica_actor_fecha_operacion_y_recursos():
    emerg, mision, _ = emergencia_con_reasignacion()

    operaciones = [r.operacion for r in emerg.registros]

    assert operaciones == [
        Operacion.EMERGENCIA_CREADA, Operacion.MISION_CREADA, Operacion.MISION_ASIGNADA,
        Operacion.MISION_REASIGNADA, Operacion.MISION_INICIADA, Operacion.MISION_FINALIZADA,
    ]
    asignada = emerg.registros[2]
    assert (asignada.actor_id, asignada.fecha_hora) == ("op-2", t(2))
    assert mision.id in asignada.recursos and "ur" in asignada.recursos


def test_pv17_la_reasignacion_identifica_la_unidad_anterior_y_la_nueva():
    emerg, _, _ = emergencia_con_reasignacion()

    reasignacion = emerg.registros[3]

    assert reasignacion.dato("unidad_anterior") == "ur"
    assert reasignacion.dato("unidad_nueva") == "ur2"


def test_pv17_la_finalizacion_conserva_resultado_y_tareas():
    emerg, _, _ = emergencia_con_reasignacion()

    finalizacion = emerg.registros[-1]

    assert finalizacion.dato("resultado") == "satisfactorio"
    assert finalizacion.dato("tareas") == "Rescatadas 2 personas"


def test_pv17_modificar_una_unidad_despues_no_cambia_el_historial_de_la_emergencia():
    emerg, _, flota = emergencia_con_reasignacion()
    antes = emerg.registros

    flota.incorporar_personal("ur", persona("nueva", RESCATE), "resp-1", t(20))
    flota.unidad("ur").retirar_personal("ur-r1", "resp-1", t(21))

    assert emerg.registros == antes


def test_pv17_el_historial_no_se_puede_modificar_desde_afuera():
    emerg, _, _ = emergencia_con_reasignacion()

    assert not hasattr(emerg.registros, "append")  # es una tupla: no se agrega ni se borra
    with pytest.raises(AttributeError):
        emerg.registros[0].actor_id = "otro"  # type: ignore[misc]  # el registro es inmutable


def test_pv17_los_cambios_en_las_unidades_quedan_registrados_en_la_unidad():
    flota = flota_con(unidad_de_rescate("ur"))
    unidad = flota.unidad("ur")

    unidad.declarar_en_mantenimiento("resp-1", t(1))
    unidad.restablecer_servicio("resp-1", t(2))

    operaciones = [r.operacion for r in unidad.registros]
    assert operaciones == [Operacion.UNIDAD_REGISTRADA, Operacion.UNIDAD_CONDICION_CAMBIADA,
                           Operacion.UNIDAD_CONDICION_CAMBIADA]
    assert unidad.registros[1].dato("anterior") == "habilitada"
    assert unidad.registros[1].dato("nueva") == "en_mantenimiento"


# ── PV18: consistencia ante errores ───────────────────────────

def test_pv18_una_asignacion_rechazada_no_deja_registro_ni_cambios():
    emerg = emergencia()
    mision = Evacuacion("Evacuar ocho", 8)
    emerg.crear_mision(mision, "op-1", t())
    chica = unidad_de_evacuacion("ue", capacidad=6)
    registros = emerg.registros

    with pytest.raises(VehiculoIncompatible):
        emerg.asignar_mision(mision.id, chica, "op-1", t(1))

    assert emerg.registros == registros
    assert mision.estado is EstadoMision.PENDIENTE
    assert chica.mision_comprometida_id is None


def test_pv18_ninguna_operacion_invalida_en_cadena_deja_registros_de_mas():
    emerg = emergencia()
    mision = Rescate("Rescatar")
    emerg.crear_mision(mision, "op-1", t())
    unidad = unidad_de_rescate("ur")
    emerg.asignar_mision(mision.id, unidad, "op-1", t(1))
    esperados = len(emerg.registros)

    intentos = (
        (MisionEnEstadoInvalido, lambda: emerg.asignar_mision(mision.id, unidad, "op-1", t(2))),
        (MisionEnEstadoInvalido, lambda: emerg.registrar_novedad(mision.id, "ur-jefe", "no empezó", t(2))),
        (MisionEnEstadoInvalido,
         lambda: emerg.finalizar_mision(mision.id, "ur-jefe", ResultadoMision.SATISFACTORIO, "x", t(2))),
        (MisionSinConcluir, lambda: emerg.cerrar("sup-1", t(2))),
        (NoEsJefeDeLaUnidad, lambda: emerg.iniciar_mision(mision.id, "intruso", t(2))),
    )
    for error, intento in intentos:
        with pytest.raises(error):
            intento()

    assert len(emerg.registros) == esperados
    assert mision.estado is EstadoMision.ASIGNADA
    assert unidad.mision_comprometida_id == mision.id
