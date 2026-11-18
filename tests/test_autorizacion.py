"""Autenticación y autorización (§9): perfiles (PV12), relación con el recurso (PV01) y token real.

Las pruebas de la primera parte usan la identidad de prueba de conftest.py. Las del final
arman la aplicación SIN ese reemplazo y le envían tokens firmados como los de Keycloak, para
comprobar la verificación de firma, realm, vencimiento y perfil.
"""

import time

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient

from app.auth import keycloak
from app.main import Repositorios, crear_aplicacion
from tests.conftest import AVISO_DE_INCENDIO, jefe, operador, reportante, responsable, supervisor

# ── PV12: cada perfil solo hace lo suyo ───────────────────────

PROHIBIDOS = [
    ("post", "/avisos", reportante, operador()),                                  # registrar avisos
    ("post", "/avisos/x/aceptacion", operador, reportante()),                     # evaluar
    ("post", "/avisos/x/descarte", operador, supervisor()),
    ("get", "/emergencias", operador, reportante()),                              # consultar emergencias
    ("get", "/emergencias", operador, jefe("ana")),
    ("post", "/emergencias/x/misiones", operador, jefe("ana")),                   # planificar
    ("post", "/emergencias/x/misiones/m/asignacion", operador, responsable()),
    ("post", "/emergencias/x/misiones/m/inicio", jefe, operador()),               # ejecutar
    ("post", "/emergencias/x/misiones/m/finalizacion", jefe, supervisor()),
    ("post", "/emergencias/x/cierre", supervisor, operador()),                    # cerrar
    ("post", "/unidades", responsable, operador()),                               # administrar recursos
    ("put", "/unidades/u/condicion", responsable, jefe("ana")),
    ("get", "/unidades", responsable, reportante()),
]


@pytest.mark.parametrize(("metodo", "ruta", "_perfil_correcto", "intruso"), PROHIBIDOS)
def test_pv12_un_perfil_no_usa_operaciones_de_otro_403(cliente, metodo, ruta, _perfil_correcto, intruso):
    respuesta = getattr(cliente, metodo)(ruta, headers=intruso, **({} if metodo == "get" else {"json": {}}))

    assert respuesta.status_code == 403
    assert "permitida solo para" in respuesta.json()["detail"]


def test_sin_token_401(cliente):
    assert cliente.get("/emergencias").status_code == 401


# ── PV01: el reportante solo ve lo suyo ───────────────────────

def avisos_de_dos_reportantes(cliente):
    propio = cliente.post("/avisos", json=AVISO_DE_INCENDIO, headers=reportante("hospital")).json()
    ajeno = cliente.post("/avisos", json=AVISO_DE_INCENDIO, headers=reportante("municipio")).json()
    return propio, ajeno


def test_pv01_el_listado_del_reportante_solo_trae_sus_avisos(cliente):
    propio, ajeno = avisos_de_dos_reportantes(cliente)

    del_hospital = cliente.get("/avisos", headers=reportante("hospital")).json()
    del_operador = cliente.get("/avisos", headers=operador()).json()

    assert [a["id"] for a in del_hospital] == [propio["id"]]
    assert {a["id"] for a in del_operador} == {propio["id"], ajeno["id"]}


def test_pv01_un_reportante_no_consulta_el_aviso_de_otro_403(cliente):
    _, ajeno = avisos_de_dos_reportantes(cliente)

    respuesta = cliente.get(f"/avisos/{ajeno['id']}", headers=reportante("hospital"))

    assert (respuesta.status_code, respuesta.json()["error"]) == (403, "AccesoDenegado")


def test_el_reportante_ve_un_resumen_de_su_emergencia_y_no_la_ajena(cliente):
    propio, ajeno = avisos_de_dos_reportantes(cliente)
    for aviso in (propio, ajeno):
        cliente.post(f"/avisos/{aviso['id']}/aceptacion", json={"tipo": "incendio", "gravedad": "media"},
                     headers=operador())

    resumen = cliente.get(f"/avisos/{propio['id']}/emergencia", headers=reportante("hospital"))
    ajena = cliente.get(f"/avisos/{ajeno['id']}/emergencia", headers=reportante("hospital"))
    completa = cliente.get(f"/avisos/{propio['id']}/emergencia", headers=operador())

    assert set(resumen.json()) == {"id", "tipo", "gravedad", "ubicacion", "estado"}   # sin misiones ni historial
    assert ajena.status_code == 403
    assert "registros" in completa.json()


def test_aviso_no_aceptado_no_tiene_emergencia_404(cliente):
    propio, _ = avisos_de_dos_reportantes(cliente)

    assert cliente.get(f"/avisos/{propio['id']}/emergencia", headers=reportante("hospital")).status_code == 404


# ── Verificación real del token (sin la identidad de prueba) ──

CLAVE = rsa.generate_private_key(public_exponent=65537, key_size=2048)
OTRA_CLAVE = rsa.generate_private_key(public_exponent=65537, key_size=2048)


class _ClavesDePrueba:
    """Hace de JWKS de Keycloak: devuelve la clave pública del realm."""

    def get_signing_key_from_jwt(self, _token):
        return type("Clave", (), {"key": CLAVE.public_key()})()


def token(usuario="hospital", roles=("reportante",), realm="crce", vence_en=300, clave=CLAVE):
    ahora = int(time.time())
    datos = {"preferred_username": usuario, "realm_access": {"roles": list(roles)},
             "iss": f"http://localhost:8080/realms/{realm}", "iat": ahora, "exp": ahora + vence_en}
    return {"Authorization": f"Bearer {jwt.encode(datos, clave, algorithm='RS256')}"}


@pytest.fixture
def cliente_real(monkeypatch):
    monkeypatch.setattr(keycloak.verificador, "_cliente_jwks", lambda: _ClavesDePrueba())
    with TestClient(crear_aplicacion(Repositorios.en_memoria())) as cliente:
        yield cliente


def test_token_valido_identifica_al_usuario_y_su_perfil(cliente_real):
    respuesta = cliente_real.post("/avisos", json=AVISO_DE_INCENDIO, headers=token("hospital"))

    assert respuesta.status_code == 201
    assert respuesta.json()["reportante_id"] == "hospital"


@pytest.mark.parametrize(("encabezado", "codigo"), [
    (token(vence_en=-10), 401),                      # vencido
    (token(realm="otro"), 401),                      # de otro realm
    (token(clave=OTRA_CLAVE), 401),                  # firma que no es de Keycloak
    ({"Authorization": "Bearer basura"}, 401),       # mal formado
    (token(roles=("offline_access",)), 403),         # sin ninguno de los cinco perfiles
    (token(roles=("operador",)), 403),               # perfil válido pero no le corresponde registrar avisos
])
def test_tokens_rechazados(cliente_real, encabezado, codigo):
    assert cliente_real.post("/avisos", json=AVISO_DE_INCENDIO, headers=encabezado).status_code == codigo


# ── Carga inicial (§9) ────────────────────────────────────────

def test_la_carga_inicial_es_reproducible_y_vincula_jefes_con_usuarios():
    import json
    from pathlib import Path

    from app import semilla
    from app.recursos.repository import RepositorioFlotaEnMemoria

    flota = RepositorioFlotaEnMemoria()
    primera, segunda = semilla.cargar(flota), semilla.cargar(flota)

    assert len(primera) == 6 and segunda == []
    realm = json.loads(Path("keycloak/crce-realm.json").read_text())
    jefes_en_keycloak = {u["username"] for u in realm["users"] if "jefe_unidad" in u["realmRoles"]}
    assert {u.jefe.id for u in flota.cargar().unidades} == jefes_en_keycloak
