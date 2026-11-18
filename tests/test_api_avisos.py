"""Contrato HTTP de /avisos: códigos de respuesta y efecto de cada operación."""

from tests.conftest import AVISO_DE_INCENDIO, operador, reportante


def registrar(cliente, usuario="ana", **cambios) -> dict:
    respuesta = cliente.post("/avisos", json=AVISO_DE_INCENDIO | cambios, headers=reportante(usuario))
    assert respuesta.status_code == 201
    return respuesta.json()


# ── Registro ──────────────────────────────────────────────────

def test_registrar_devuelve_201_y_el_aviso_pendiente(cliente):
    aviso = registrar(cliente)

    assert aviso["estado"] == "pendiente"
    assert aviso["reportante_id"] == "ana"
    assert aviso["gravedad_estimada"] == "alta"
    assert [r["operacion"] for r in aviso["registros"]] == ["aviso_registrado"]


def test_el_aviso_registrado_se_puede_consultar(cliente):
    aviso = registrar(cliente)

    respuesta = cliente.get(f"/avisos/{aviso['id']}", headers=reportante("ana"))

    assert respuesta.status_code == 200
    assert respuesta.json() == aviso


def test_tipo_fuera_de_catalogo_lo_rechaza_la_api_con_422(cliente):
    respuesta = cliente.post("/avisos", json=AVISO_DE_INCENDIO | {"tipo": "terremoto"}, headers=reportante("ana"))

    assert respuesta.status_code == 422


def test_descripcion_vacia_la_rechaza_el_dominio_con_422(cliente):
    respuesta = cliente.post("/avisos", json=AVISO_DE_INCENDIO | {"descripcion": "   "}, headers=reportante("ana"))

    assert respuesta.status_code == 422
    assert respuesta.json()["error"] == "DatoDeAvisoInvalido"


def test_sin_autenticarse_no_se_puede_registrar_401(cliente):
    assert cliente.post("/avisos", json=AVISO_DE_INCENDIO).status_code == 401


def test_aviso_inexistente_devuelve_404(cliente):
    respuesta = cliente.get("/avisos/no-existe", headers=operador())

    assert respuesta.status_code == 404
    assert respuesta.json()["error"] == "AvisoNoEncontrado"


def test_listar_filtra_por_estado(cliente):
    primero = registrar(cliente)
    segundo = registrar(cliente)
    cliente.post(f"/avisos/{segundo['id']}/descarte", json={"justificacion": "Duplicado"}, headers=operador("op"))

    pendientes = cliente.get("/avisos", params={"estado": "pendiente"}, headers=operador()).json()

    assert [a["id"] for a in pendientes] == [primero["id"]]
    assert len(cliente.get("/avisos", headers=operador()).json()) == 2


# ── Notas ─────────────────────────────────────────────────────

def test_el_reportante_agrega_una_nota(cliente):
    aviso = registrar(cliente)

    respuesta = cliente.post(f"/avisos/{aviso['id']}/notas", json={"texto": "Se ven llamas"}, headers=reportante("ana"))

    assert respuesta.status_code == 201
    guardado = cliente.get(f"/avisos/{aviso['id']}", headers=operador()).json()
    assert [n["texto"] for n in guardado["notas"]] == ["Se ven llamas"]


def test_otro_usuario_no_puede_agregar_notas_403_y_no_cambia_nada(cliente):
    aviso = registrar(cliente)

    respuesta = cliente.post(f"/avisos/{aviso['id']}/notas", json={"texto": "Hola"}, headers=reportante("intruso"))

    assert respuesta.status_code == 403
    assert cliente.get(f"/avisos/{aviso['id']}", headers=operador()).json() == aviso


# ── Evaluación ────────────────────────────────────────────────

def test_descartar_con_justificacion(cliente):
    aviso = registrar(cliente)

    respuesta = cliente.post(f"/avisos/{aviso['id']}/descarte", json={"justificacion": "Falsa alarma"},
                             headers=operador("op"))

    assert respuesta.status_code == 200
    assert respuesta.json()["estado"] == "descartado"
    assert respuesta.json()["descarte"]["operador_id"] == "op"


def test_descartar_sin_justificacion_422_y_el_aviso_sigue_pendiente(cliente):
    aviso = registrar(cliente)

    respuesta = cliente.post(f"/avisos/{aviso['id']}/descarte", json={"justificacion": " "}, headers=operador("op"))

    assert respuesta.status_code == 422
    assert cliente.get(f"/avisos/{aviso['id']}", headers=operador()).json()["estado"] == "pendiente"


def test_aceptar_crea_la_emergencia_con_los_datos_confirmados(cliente):
    aviso = registrar(cliente)

    respuesta = cliente.post(f"/avisos/{aviso['id']}/aceptacion", json={"tipo": "incendio", "gravedad": "media"},
                             headers=operador("op"))

    assert respuesta.status_code == 201
    emergencia = respuesta.json()
    assert emergencia["aviso_id"] == aviso["id"]
    assert emergencia["gravedad"] == "media"
    assert cliente.get(f"/avisos/{aviso['id']}", headers=operador()).json()["estado"] == "aceptado"
    assert cliente.get(f"/emergencias/{emergencia['id']}", headers=operador()).status_code == 200


def test_un_aviso_evaluado_no_se_vuelve_a_evaluar_409(cliente):
    aviso = registrar(cliente)
    cliente.post(f"/avisos/{aviso['id']}/aceptacion", json={"tipo": "incendio", "gravedad": "alta"},
                 headers=operador("op"))

    otra_vez = cliente.post(f"/avisos/{aviso['id']}/aceptacion", json={"tipo": "incendio", "gravedad": "alta"},
                            headers=operador("op"))
    descarte = cliente.post(f"/avisos/{aviso['id']}/descarte", json={"justificacion": "x"}, headers=operador("op"))
    nota = cliente.post(f"/avisos/{aviso['id']}/notas", json={"texto": "x"}, headers=reportante("ana"))

    assert (otra_vez.status_code, descarte.status_code, nota.status_code) == (409, 409, 409)
    assert len(cliente.get("/emergencias", headers=operador()).json()) == 1
