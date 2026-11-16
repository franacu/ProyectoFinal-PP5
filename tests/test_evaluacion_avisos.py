"""Evaluación de avisos (§2.2, §7.1): aceptar origina una única emergencia. PV01 y PV02 en el dominio.

La visibilidad entre reportantes (PV01/PV12) es de la capa de aplicación; acá se prueba
lo que el dominio garantiza: a quién pertenece cada aviso y cada emergencia.
"""

from datetime import datetime

import pytest

from dominio.aviso import EstadoAviso
from dominio.catalogos import Gravedad, TipoSituacion
from dominio.emergencia import EstadoEmergencia
from dominio.errores import (
    AceptacionInvalida,
    AvisoNoPendiente,
)
from dominio.historial import Operacion
from tests.escenarios import aviso, t


def aceptar(a, tipo=TipoSituacion.INUNDACION, gravedad=Gravedad.ALTA, fecha=None):
    return a.aceptar("op-1", tipo, gravedad, fecha or t(5))


# ── PV02: aceptar ─────────────────────────────────────────────

def test_pv02_aceptar_origina_una_emergencia_abierta_con_los_datos_confirmados():
    a = aviso("rep-1", TipoSituacion.INUNDACION, Gravedad.MEDIA, registrado=t(0))

    emerg = aceptar(a, TipoSituacion.INUNDACION, Gravedad.ALTA, t(7))

    assert a.estado is EstadoAviso.ACEPTADO
    assert emerg.estado is EstadoEmergencia.ABIERTA
    assert (emerg.tipo, emerg.gravedad) == (TipoSituacion.INUNDACION, Gravedad.ALTA)
    assert emerg.ubicacion == a.ubicacion
    assert emerg.aviso_id == a.id
    assert emerg.reportante_id == "rep-1"
    assert emerg.creada_en == t(7)  # momento de ACEPTACIÓN, no de registro del aviso


def test_pv02_el_operador_puede_corregir_tipo_y_gravedad_sin_pisar_los_datos_del_aviso():
    a = aviso("rep-1", TipoSituacion.INCENDIO, Gravedad.BAJA)

    emerg = aceptar(a, TipoSituacion.ACCIDENTE_VIAL, Gravedad.ALTA)

    assert (emerg.tipo, emerg.gravedad) == (TipoSituacion.ACCIDENTE_VIAL, Gravedad.ALTA)
    assert (a.tipo, a.gravedad_estimada) == (TipoSituacion.INCENDIO, Gravedad.BAJA)


def test_pv02_un_aviso_aceptado_origina_una_unica_emergencia_y_no_se_evalua_de_nuevo():
    a = aviso()
    aceptar(a)

    with pytest.raises(AvisoNoPendiente):
        aceptar(a)
    with pytest.raises(AvisoNoPendiente):
        a.descartar("op-1", "Duplicado", t(9))

    assert a.estado is EstadoAviso.ACEPTADO
    assert a.descarte is None


def test_pv02_un_aviso_descartado_no_puede_aceptarse_despues():
    a = aviso()
    a.descartar("op-1", "Aviso duplicado", t(3))

    with pytest.raises(AvisoNoPendiente):
        aceptar(a)

    assert a.estado is EstadoAviso.DESCARTADO
    assert a.descarte.justificacion == "Aviso duplicado"


def test_un_aviso_aceptado_no_admite_nuevas_notas():
    a = aviso()
    aceptar(a)

    with pytest.raises(AvisoNoPendiente):
        a.agregar_nota("rep-1", "tarde", t(9))

    assert a.notas == ()


@pytest.mark.parametrize("operador, tipo, gravedad, fecha", [
    (None, TipoSituacion.INUNDACION, Gravedad.ALTA, t(5)),
    ("", TipoSituacion.INUNDACION, Gravedad.ALTA, t(5)),
    ("   ", TipoSituacion.INUNDACION, Gravedad.ALTA, t(5)),
    ("op-1", "inundacion", Gravedad.ALTA, t(5)),
    ("op-1", TipoSituacion.INUNDACION, "alta", t(5)),
    ("op-1", None, Gravedad.ALTA, t(5)),
    ("op-1", TipoSituacion.INUNDACION, None, t(5)),
    ("op-1", TipoSituacion.INUNDACION, Gravedad.ALTA, None),
])
def test_aceptar_con_datos_invalidos_se_rechaza_y_el_aviso_sigue_pendiente(operador, tipo, gravedad, fecha):
    a = aviso()
    registros = a.registros

    with pytest.raises(AceptacionInvalida):
        a.aceptar(operador, tipo, gravedad, fecha)

    assert a.estado is EstadoAviso.PENDIENTE
    assert a.registros == registros


def test_notas_antes_de_aceptar_no_cambian_los_datos_de_la_emergencia():
    a = aviso("rep-1")
    a.agregar_nota("rep-1", "Subió el agua", t(2))

    emerg = aceptar(a)

    assert len(a.notas) == 1
    assert emerg.misiones == ()


# ── PV01 (parte del dominio): cada cosa sabe de quién es ──────

def test_pv01_dos_reportantes_tienen_avisos_y_emergencias_que_se_distinguen_por_reportante():
    a1, a2 = aviso("rep-1"), aviso("rep-2")
    e1, e2 = aceptar(a1), aceptar(a2)

    assert (a1.reportante_id, a2.reportante_id) == ("rep-1", "rep-2")
    assert (e1.reportante_id, e2.reportante_id) == ("rep-1", "rep-2")


# ── Historial de avisos (§9) ──────────────────────────────────

def test_el_aviso_registra_su_creacion_notas_y_evaluacion():
    a = aviso("rep-1", registrado=t(0))
    a.agregar_nota("rep-1", "Subió el agua", t(2))
    emerg = aceptar(a, fecha=t(5))

    operaciones = [r.operacion for r in a.registros]

    assert operaciones == [Operacion.AVISO_REGISTRADO, Operacion.NOTA_AGREGADA, Operacion.AVISO_ACEPTADO]
    assert a.registros[0].actor_id == "rep-1"
    assert a.registros[2].actor_id == "op-1"
    assert emerg.id in a.registros[2].recursos


def test_el_descarte_registra_actor_y_justificacion():
    a = aviso()
    a.descartar("op-9", "Aviso duplicado", t(3))

    registro = a.registros[-1]

    assert registro.operacion is Operacion.AVISO_DESCARTADO
    assert registro.actor_id == "op-9"
    assert registro.dato("justificacion") == "Aviso duplicado"


def test_la_emergencia_registra_su_creacion_con_el_operador_que_acepto():
    emerg = aceptar(aviso(), fecha=t(5))

    creacion = emerg.registros[0]

    assert creacion.operacion is Operacion.EMERGENCIA_CREADA
    assert (creacion.actor_id, creacion.fecha_hora) == ("op-1", t(5))
    assert datetime(2026, 11, 20, 10, 5) == creacion.fecha_hora


def test_un_rechazo_no_deja_registro_en_el_aviso():
    a = aviso()
    aceptar(a)
    registros = a.registros

    with pytest.raises(AvisoNoPendiente):
        aceptar(a)

    assert a.registros == registros
