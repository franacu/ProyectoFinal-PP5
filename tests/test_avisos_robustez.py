"""Datos que nacen juntos y estado coherente (mismos criterios que test_avisos.py)."""

from datetime import datetime

import pytest

from dominio.aviso import Aviso, Descarte, EstadoAviso, Nota, Ubicacion
from dominio.catalogos import Gravedad, TipoSituacion
from dominio.errores import (
    DatoDeAvisoInvalido,
    DescarteInvalido,
    NotaDeOtroAutor,
    NotaInvalida,
)

T0 = datetime(2026, 11, 20, 10, 0)
T1 = datetime(2026, 11, 20, 10, 15)


def nuevo_aviso() -> Aviso:
    return Aviso("rep-1", Ubicacion("Ruta 3 km 12", "Río Grande"), TipoSituacion.INUNDACION,
                 Gravedad.MEDIA, "Agua ingresando a viviendas", T0)


def test_r2_nota_sin_fecha_se_rechaza_y_no_se_agrega():
    aviso = nuevo_aviso()

    with pytest.raises(NotaInvalida):
        aviso.agregar_nota("rep-1", "sin fecha", None)

    assert aviso.notas == ()


@pytest.mark.parametrize("autor", [None, "", "   "])
def test_r2_nota_sin_autor_se_rechaza_con_error_de_dominio(autor):
    with pytest.raises(NotaInvalida):
        Nota(autor, "texto", T1)


def test_r2_nota_de_otro_autor_se_rechaza_y_no_se_agrega():
    aviso = nuevo_aviso()

    with pytest.raises(NotaDeOtroAutor):
        aviso.agregar_nota("rep-999", "no soy el reportante", T1)

    assert aviso.notas == ()


@pytest.mark.parametrize("operador, fecha", [("", T1), ("   ", T1), (None, T1), ("op-1", None)])
def test_r4_r6_descarte_sin_operador_o_sin_fecha_se_rechaza_y_sigue_pendiente(operador, fecha):
    aviso = nuevo_aviso()

    with pytest.raises(DescarteInvalido):
        aviso.descartar(operador, "Aviso duplicado", fecha)

    assert aviso.estado is EstadoAviso.PENDIENTE
    assert aviso.descarte is None


@pytest.mark.parametrize("direccion, localidad", [(None, "Río Grande"), ("", "Río Grande"),
                                                   ("Ruta 3", None), ("Ruta 3", "  ")])
def test_r1_ubicacion_incompleta_se_rechaza_con_error_de_dominio(direccion, localidad):
    with pytest.raises(DatoDeAvisoInvalido):
        Ubicacion(direccion, localidad)


def test_restaurar_rechaza_aviso_descartado_sin_descarte():
    with pytest.raises(DatoDeAvisoInvalido):
        Aviso.restaurar(aviso_id="x", reportante_id="rep-1", ubicacion=Ubicacion("a", "b"),
                        tipo=TipoSituacion.INCENDIO, gravedad_estimada=Gravedad.BAJA,
                        descripcion="d", registrado_en=T0, estado=EstadoAviso.DESCARTADO)


def test_restaurar_rechaza_aviso_aceptado_con_descarte():
    with pytest.raises(DatoDeAvisoInvalido):
        Aviso.restaurar(aviso_id="x", reportante_id="rep-1", ubicacion=Ubicacion("a", "b"),
                        tipo=TipoSituacion.INCENDIO, gravedad_estimada=Gravedad.BAJA,
                        descripcion="d", registrado_en=T0, estado=EstadoAviso.ACEPTADO,
                        descarte=Descarte("op-1", "motivo", T1))