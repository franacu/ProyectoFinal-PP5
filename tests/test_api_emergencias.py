"""Contrato HTTP de /emergencias y traducción de errores a códigos HTTP."""

import pytest

from app.internal.errores_http import codigo_para
from dominio import errores
from tests.conftest import AVISO_DE_INCENDIO, operador, reportante


def emergencia_con(cliente, gravedad: str) -> str:
    aviso = cliente.post("/avisos", json=AVISO_DE_INCENDIO, headers=reportante("ana")).json()
    respuesta = cliente.post(f"/avisos/{aviso['id']}/aceptacion", json={"tipo": "incendio", "gravedad": gravedad},
                             headers=operador("op"))
    return respuesta.json()["id"]


def test_abiertas_por_prioridad_pv03(cliente):
    media = emergencia_con(cliente, "media")
    alta_vieja = emergencia_con(cliente, "alta")
    baja = emergencia_con(cliente, "baja")
    alta_nueva = emergencia_con(cliente, "alta")

    orden = [e["id"] for e in cliente.get("/emergencias", headers=operador()).json()]

    assert orden == [alta_vieja, alta_nueva, media, baja]


def test_emergencia_inexistente_404(cliente):
    assert cliente.get("/emergencias/no-existe", headers=operador()).status_code == 404


def test_estado_del_servicio(cliente):
    assert cliente.get("/estado").json()["estado"] == "en línea"


def test_la_raiz_lleva_a_la_interfaz_y_la_configuracion_no_pide_token(cliente):
    assert cliente.get("/").url.path == "/app/"
    assert "CRCE" in cliente.get("/app/").text
    assert cliente.get("/configuracion").json()["realm"] == "crce"


@pytest.mark.parametrize(("error", "codigo"), [
    (errores.NoEncontrado, 404),
    (errores.NotaDeOtroAutor, 403),
    (errores.AvisoNoPendiente, 409),
    (errores.UnidadOcupada, 409),
    (errores.EmergenciaCerrada, 409),
    (errores.JustificacionVacia, 422),
    (errores.DatoDeAvisoInvalido, 422),
])
def test_cada_error_del_dominio_tiene_su_codigo_http(error, codigo):
    assert codigo_para(error("motivo")) == codigo
