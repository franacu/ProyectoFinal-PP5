"""Avance 1 — cada test nombra la regla (R1..R6) que prueba.

Cada regla se mira desde tres lados: camino feliz, rechazo y estado posterior.
"""

from datetime import datetime

import pytest

from dominio.aviso import Aviso, Descarte, EstadoAviso, Nota, Ubicacion
from dominio.catalogos import Gravedad, TipoSituacion
from dominio.errores import (
    AvisoNoPendiente,
    DatoDeAvisoInvalido,
    JustificacionVacia,
    NotaInvalida,
)

T0 = datetime(2026, 11, 20, 10, 0)
T1 = datetime(2026, 11, 20, 10, 15)
T2 = datetime(2026, 11, 20, 10, 30)


def nuevo_aviso() -> Aviso:
    return Aviso(
        reportante_id="rep-1",
        ubicacion=Ubicacion("Ruta 3 km 12", "Río Grande"),
        tipo=TipoSituacion.INUNDACION,
        gravedad_estimada=Gravedad.MEDIA,
        descripcion="Agua ingresando a viviendas",
        registrado_en=T0,
    )


def datos_originales(aviso: Aviso) -> tuple:
    return (aviso.ubicacion, aviso.tipo, aviso.gravedad_estimada, aviso.descripcion,
            aviso.reportante_id, aviso.registrado_en)


# ── R1 ────────────────────────────────────────────────────────

def test_r1_aviso_nuevo_nace_pendiente_sin_notas_ni_descarte():
    aviso = nuevo_aviso()

    assert aviso.estado is EstadoAviso.PENDIENTE
    assert aviso.notas == ()
    assert aviso.descarte is None
    assert aviso.registrado_en == T0
    assert aviso.reportante_id == "rep-1"


@pytest.mark.parametrize("campo, valor", [
    ("tipo", "inundacion"),
    ("gravedad_estimada", "alta"),
    ("descripcion", "   "),
    ("reportante_id", ""),
])
def test_r1_aviso_rechaza_datos_invalidos_o_fuera_de_catalogo(campo, valor):
    datos = dict(reportante_id="rep-1", ubicacion=Ubicacion("Calle 1", "Ushuaia"),
                 tipo=TipoSituacion.INCENDIO, gravedad_estimada=Gravedad.ALTA,
                 descripcion="Humo", registrado_en=T0)
    datos[campo] = valor

    with pytest.raises(DatoDeAvisoInvalido):
        Aviso(**datos)


# ── R2 ────────────────────────────────────────────────────────

def test_r2_nota_en_aviso_pendiente_conserva_autor_fecha_y_hora():
    aviso = nuevo_aviso()

    aviso.agregar_nota("rep-1", "Subió el nivel del agua", T1)

    assert aviso.notas == (Nota("rep-1", "Subió el nivel del agua", T1),)


def test_r2_dos_notas_se_conservan_en_orden_de_llegada():
    aviso = nuevo_aviso()

    aviso.agregar_nota("rep-1", "primera", T1)
    aviso.agregar_nota("rep-1", "segunda", T2)

    assert [n.texto for n in aviso.notas] == ["primera", "segunda"]


def test_r2_nota_vacia_se_rechaza_y_no_se_agrega():
    aviso = nuevo_aviso()

    with pytest.raises(NotaInvalida):
        aviso.agregar_nota("rep-1", "   ", T1)

    assert aviso.notas == ()


def test_r2_notas_no_se_pueden_modificar_desde_afuera():
    aviso = nuevo_aviso()

    with pytest.raises(AttributeError):
        aviso.notas.append(Nota("rep-1", "colada", T1))  # tupla: no tiene append

    assert aviso.notas == ()


# ── R3 ────────────────────────────────────────────────────────

def test_r3_agregar_nota_no_cambia_datos_originales():
    aviso = nuevo_aviso()
    antes = datos_originales(aviso)

    aviso.agregar_nota("rep-1", "Hay dos personas aisladas", T1)

    assert datos_originales(aviso) == antes


# ── R4 ────────────────────────────────────────────────────────

def test_r4_descartar_con_justificacion_conserva_justificacion_y_fecha():
    aviso = nuevo_aviso()

    aviso.descartar("op-1", "Aviso duplicado", T1)

    assert aviso.estado is EstadoAviso.DESCARTADO
    assert aviso.descarte == Descarte("op-1", "Aviso duplicado", T1)


@pytest.mark.parametrize("justificacion", ["", "   "])
def test_r4_r6_descartar_con_justificacion_vacia_se_rechaza_y_sigue_pendiente(justificacion):
    aviso = nuevo_aviso()

    with pytest.raises(JustificacionVacia):
        aviso.descartar("op-1", justificacion, T1)

    assert aviso.estado is EstadoAviso.PENDIENTE
    assert aviso.descarte is None


# ── R5 + R6 ───────────────────────────────────────────────────

def test_r5_r6_aviso_descartado_rechaza_nuevas_notas_sin_cambiar_las_existentes():
    aviso = nuevo_aviso()
    aviso.agregar_nota("rep-1", "antes del descarte", T1)
    aviso.descartar("op-1", "Falsa alarma", T2)

    with pytest.raises(AvisoNoPendiente):
        aviso.agregar_nota("rep-1", "después del descarte", T2)

    assert [n.texto for n in aviso.notas] == ["antes del descarte"]


def test_r5_r6_segundo_descarte_se_rechaza_y_conserva_justificacion_original():
    aviso = nuevo_aviso()
    aviso.descartar("op-1", "Falsa alarma", T1)

    with pytest.raises(AvisoNoPendiente):
        aviso.descartar("op-2", "Otro motivo", T2)

    assert aviso.descarte == Descarte("op-1", "Falsa alarma", T1)
    assert aviso.estado is EstadoAviso.DESCARTADO


def aviso_aceptado() -> Aviso:
    # No existe aceptar() todavía: se reconstruye un aviso en ese estado.
    return Aviso.restaurar(
        aviso_id="av-9", reportante_id="rep-1",
        ubicacion=Ubicacion("Ruta 3 km 12", "Río Grande"),
        tipo=TipoSituacion.INUNDACION, gravedad_estimada=Gravedad.ALTA,
        descripcion="Agua", registrado_en=T0, estado=EstadoAviso.ACEPTADO,
    )


def test_r5_r6_aviso_aceptado_rechaza_nuevas_notas():
    aviso = aviso_aceptado()

    with pytest.raises(AvisoNoPendiente):
        aviso.agregar_nota("rep-1", "tarde", T1)

    assert aviso.notas == ()
    assert aviso.estado is EstadoAviso.ACEPTADO


def test_r5_r6_aviso_aceptado_rechaza_descarte():
    aviso = aviso_aceptado()

    with pytest.raises(AvisoNoPendiente):
        aviso.descartar("op-1", "Me arrepentí", T1)

    assert aviso.estado is EstadoAviso.ACEPTADO
    assert aviso.descarte is None


def test_restaurar_rechaza_estado_incoherente_con_descarte():
    with pytest.raises(DatoDeAvisoInvalido):
        Aviso.restaurar(
            aviso_id="x", reportante_id="rep-1", ubicacion=Ubicacion("a", "b"),
            tipo=TipoSituacion.INCENDIO, gravedad_estimada=Gravedad.BAJA,
            descripcion="d", registrado_en=T0, estado=EstadoAviso.PENDIENTE,
            descarte=Descarte("op-1", "motivo", T1),
        )
