"""Contrato HTTP de recursos, misiones y cierre: escenarios PV04 a PV18 vistos desde la API.

El dominio ya prueba cada regla por separado. Acá se comprueba que la API las respeta de
punta a punta: código HTTP, motivo del rechazo y que nada quede modificado a medias.
"""

import pytest

from tests.conftest import AVISO_DE_INCENDIO, jefe, operador, reportante, responsable, supervisor

RESPONSABLE, OPERADOR, SUPERVISOR = responsable(), operador(), supervisor()


def persona(pid, *competencias):
    return {"id": pid, "nombre": pid.capitalize(), "competencias": list(competencias)}


UNIDADES = {
    # PV: Ana rescate (jefa), Bruno conducción, Carla rescate
    "U-rescate": {"jefe": persona("ana", "rescate"),
                  "personal": [persona("bruno", "conduccion"), persona("carla", "rescate")],
                  "vehiculo": {"id": "VR-1", "categoria": "vehiculo_de_rescate"},
                  "equipamiento": [{"id": "ER-1", "categoria": "equipo_de_rescate"}]},
    "U-rescate-2": {"jefe": persona("diego", "rescate"),
                    "personal": [persona("eva", "conduccion"), persona("fede", "rescate")],
                    "vehiculo": {"id": "VR-2", "categoria": "vehiculo_de_rescate"},
                    "equipamiento": [{"id": "ER-2", "categoria": "equipo_de_rescate"}]},
    "U-ambulancia": {"jefe": persona("gabi", "conduccion"), "personal": [persona("hugo", "primeros_auxilios")],
                     "vehiculo": {"id": "AMB-1", "categoria": "ambulancia"},
                     "equipamiento": [{"id": "ES-1", "categoria": "equipo_sanitario"}]},
    "U-transporte": {"jefe": persona("ines", "conduccion"), "personal": [persona("juan", "evacuacion")],
                     "vehiculo": {"id": "TP-1", "categoria": "transporte_de_personas", "capacidad_evacuados": 10}},
}


@pytest.fixture
def escenario(cliente):
    """Una base, cuatro unidades y una emergencia de incendio abierta. Devuelve el id de la emergencia."""
    base = {"id": "B-centro", "nombre": "Base Centro", "ubicacion": {"direccion": "Maipú 100", "localidad": "Ushuaia"}}
    assert cliente.post("/bases", json=base, headers=RESPONSABLE).status_code == 201
    for uid, datos in UNIDADES.items():
        r = cliente.post("/unidades", json={"id": uid, "base_id": "B-centro", **datos}, headers=RESPONSABLE)
        assert r.status_code == 201, r.json()
    return nueva_emergencia(cliente, "incendio")


def nueva_emergencia(cliente, tipo):
    aviso = cliente.post("/avisos", json=AVISO_DE_INCENDIO | {"tipo": tipo}, headers=reportante()).json()
    r = cliente.post(f"/avisos/{aviso['id']}/aceptacion", json={"tipo": tipo, "gravedad": "alta"}, headers=OPERADOR)
    return r.json()["id"]


def crear_mision(cliente, eid, tipo="rescate", **extra):
    r = cliente.post(f"/emergencias/{eid}/misiones", json={"tipo": tipo, "objetivo": "Objetivo de prueba", **extra},
                     headers=OPERADOR)
    assert r.status_code == 201, r.json()
    return r.json()["id"]


def asignar(cliente, eid, mid, unidad, metodo="post"):
    return getattr(cliente, metodo)(f"/emergencias/{eid}/misiones/{mid}/asignacion", json={"unidad_id": unidad},
                                    headers=OPERADOR)


def mision(cliente, eid, mid):
    return next(m for m in cliente.get(f"/emergencias/{eid}", headers=OPERADOR).json()["misiones"] if m["id"] == mid)


def unidad(cliente, uid):
    return cliente.get(f"/unidades/{uid}", headers=RESPONSABLE).json()


def operaciones(cliente, eid):
    return [r["operacion"] for r in cliente.get(f"/emergencias/{eid}/historial", headers=OPERADOR).json()]


# ── Recursos ──────────────────────────────────────────────────

def test_las_unidades_registradas_quedan_habilitadas_y_libres(cliente, escenario):
    u = unidad(cliente, "U-rescate")

    assert (u["condicion"], u["mision_comprometida_id"], u["jefe_id"]) == ("habilitada", None, "ana")
    assert {p["id"] for p in u["personal"]} == {"ana", "bruno", "carla"}
    assert len(cliente.get("/unidades", headers=RESPONSABLE).json()) == 4


def test_una_persona_no_integra_dos_unidades_409(cliente, escenario):
    r = cliente.post("/unidades/U-ambulancia/personal", json=persona("carla", "rescate"), headers=RESPONSABLE)

    assert r.status_code == 409
    assert r.json()["error"] == "RecursoDuplicado"


def test_unidad_inexistente_404(cliente, escenario):
    assert cliente.get("/unidades/no-existe", headers=RESPONSABLE).status_code == 404


# ── Creación de misiones (PV05) ───────────────────────────────

def test_mision_incompatible_con_la_situacion_422(cliente, escenario):
    accidente = nueva_emergencia(cliente, "accidente_vial")

    r = cliente.post(f"/emergencias/{accidente}/misiones",
                     json={"tipo": "evacuacion", "objetivo": "Evacuar", "cantidad_personas": 5}, headers=OPERADOR)

    assert r.status_code == 422
    assert r.json()["error"] == "MisionIncompatible"


def test_evacuacion_sin_cantidad_de_personas_422(cliente, escenario):
    r = cliente.post(f"/emergencias/{escenario}/misiones", json={"tipo": "evacuacion", "objetivo": "Evacuar"},
                     headers=OPERADOR)

    assert r.status_code == 422


# ── Asignación (§8.2) ─────────────────────────────────────────

def test_asignar_una_unidad_apta_la_compromete(cliente, escenario):
    mid = crear_mision(cliente, escenario)

    r = asignar(cliente, escenario, mid, "U-rescate")

    assert r.status_code == 200
    assert (r.json()["estado"], r.json()["unidad_id"]) == ("asignada", "U-rescate")
    assert unidad(cliente, "U-rescate")["mision_comprometida_id"] == mid


@pytest.mark.parametrize(("tipo", "extra", "unidad_id", "error"), [
    ("rescate", {}, "U-ambulancia", "VehiculoIncompatible"),
    ("evacuacion", {"cantidad_personas": 30}, "U-transporte", "VehiculoIncompatible"),   # capacidad 10
    ("asistencia_sanitaria", {}, "U-rescate", "VehiculoIncompatible"),
])
def test_asignacion_rechazada_no_cambia_nada(cliente, escenario, tipo, extra, unidad_id, error):
    mid = crear_mision(cliente, escenario, tipo, **extra)

    r = asignar(cliente, escenario, mid, unidad_id)

    assert r.status_code == 409
    assert r.json()["error"] == error
    assert mision(cliente, escenario, mid)["estado"] == "pendiente"
    assert unidad(cliente, unidad_id)["mision_comprometida_id"] is None
    assert "mision_asignada" not in operaciones(cliente, escenario)


def test_unidad_ocupada_no_recibe_otra_mision_409(cliente, escenario):
    primera, segunda = crear_mision(cliente, escenario), crear_mision(cliente, escenario)
    asignar(cliente, escenario, primera, "U-rescate")

    r = asignar(cliente, escenario, segunda, "U-rescate")

    assert (r.status_code, r.json()["error"]) == (409, "UnidadOcupada")


def test_unidad_en_mantenimiento_no_se_asigna_409(cliente, escenario):
    cliente.put("/unidades/U-rescate/condicion", json={"condicion": "en_mantenimiento"}, headers=RESPONSABLE)
    mid = crear_mision(cliente, escenario)

    r = asignar(cliente, escenario, mid, "U-rescate")

    assert (r.status_code, r.json()["error"]) == (409, "UnidadNoHabilitada")


def test_equipo_fuera_de_servicio_impide_el_rescate_409(cliente, escenario):
    cliente.put("/unidades/U-rescate/equipamiento/ER-1/condicion", json={"condicion": "fuera_de_servicio"},
                headers=RESPONSABLE)
    mid = crear_mision(cliente, escenario)

    r = asignar(cliente, escenario, mid, "U-rescate")

    assert (r.status_code, r.json()["error"]) == (409, "EquipamientoInsuficiente")


def test_personal_insuficiente_409(cliente, escenario):
    cliente.delete("/unidades/U-rescate/personal/carla", headers=RESPONSABLE)   # queda un solo rescatista
    mid = crear_mision(cliente, escenario)

    r = asignar(cliente, escenario, mid, "U-rescate")

    assert (r.status_code, r.json()["error"]) == (409, "PersonalInsuficiente")


def test_una_unidad_comprometida_no_se_modifica_409(cliente, escenario):
    asignar(cliente, escenario, crear_mision(cliente, escenario), "U-rescate")

    cambio = cliente.put("/unidades/U-rescate/condicion", json={"condicion": "en_mantenimiento"}, headers=RESPONSABLE)
    retiro = cliente.delete("/unidades/U-rescate/personal/bruno", headers=RESPONSABLE)

    assert (cambio.status_code, retiro.status_code) == (409, 409)
    assert unidad(cliente, "U-rescate")["condicion"] == "habilitada"


# ── Reasignación (§8.3, PV18) ─────────────────────────────────

def test_reasignar_registra_unidad_anterior_y_nueva_y_libera_la_anterior(cliente, escenario):
    mid = crear_mision(cliente, escenario)
    asignar(cliente, escenario, mid, "U-rescate")

    r = asignar(cliente, escenario, mid, "U-rescate-2", metodo="put")

    assert r.json()["unidad_id"] == "U-rescate-2"
    assert unidad(cliente, "U-rescate")["mision_comprometida_id"] is None
    assert unidad(cliente, "U-rescate-2")["mision_comprometida_id"] == mid
    registro = cliente.get(f"/emergencias/{escenario}/historial", headers=OPERADOR).json()[-1]
    assert registro["detalle"] == {"unidad_anterior": "U-rescate", "unidad_nueva": "U-rescate-2"}


def test_pv18_reasignacion_invalida_conserva_todo(cliente, escenario):
    mid = crear_mision(cliente, escenario)
    asignar(cliente, escenario, mid, "U-rescate")
    historial_antes = cliente.get(f"/emergencias/{escenario}/historial", headers=OPERADOR).json()

    r = asignar(cliente, escenario, mid, "U-ambulancia", metodo="put")

    assert r.status_code == 409
    assert mision(cliente, escenario, mid)["unidad_id"] == "U-rescate"
    assert unidad(cliente, "U-rescate")["mision_comprometida_id"] == mid
    assert unidad(cliente, "U-ambulancia")["mision_comprometida_id"] is None
    assert cliente.get(f"/emergencias/{escenario}/historial", headers=OPERADOR).json() == historial_antes


# ── Jefe de unidad (§2.3) ─────────────────────────────────────

def test_el_jefe_ve_las_misiones_de_su_unidad_y_no_las_ajenas(cliente, escenario):
    mid = crear_mision(cliente, escenario)
    asignar(cliente, escenario, mid, "U-rescate")

    propias = cliente.get("/misiones/mias", headers=jefe("ana")).json()
    ajenas = cliente.get("/misiones/mias", headers=jefe("diego")).json()

    assert [m["id"] for m in propias] == [mid]
    assert propias[0]["ubicacion"]["localidad"] == "Ushuaia"
    assert ajenas == []


def test_un_jefe_no_puede_iniciar_la_mision_de_otra_unidad_403(cliente, escenario):
    mid = crear_mision(cliente, escenario)
    asignar(cliente, escenario, mid, "U-rescate")

    r = cliente.post(f"/emergencias/{escenario}/misiones/{mid}/inicio", headers=jefe("diego"))

    assert (r.status_code, r.json()["error"]) == (403, "NoEsJefeDeLaUnidad")
    assert mision(cliente, escenario, mid)["estado"] == "asignada"


def test_rechazar_vuelve_a_pendiente_y_libera_la_unidad(cliente, escenario):
    mid = crear_mision(cliente, escenario)
    asignar(cliente, escenario, mid, "U-rescate")

    r = cliente.post(f"/emergencias/{escenario}/misiones/{mid}/rechazo", json={"justificacion": "Desperfecto"},
                     headers=jefe("ana"))

    assert (r.json()["estado"], r.json()["unidad_id"]) == ("pendiente", None)
    assert unidad(cliente, "U-rescate")["mision_comprometida_id"] is None


def test_una_mision_iniciada_no_se_cancela_ni_se_reasigna_409(cliente, escenario):
    mid = crear_mision(cliente, escenario)
    asignar(cliente, escenario, mid, "U-rescate")
    cliente.post(f"/emergencias/{escenario}/misiones/{mid}/inicio", headers=jefe("ana"))

    cancelar = cliente.post(f"/emergencias/{escenario}/misiones/{mid}/cancelacion", headers=OPERADOR)
    reasignar = asignar(cliente, escenario, mid, "U-rescate-2", metodo="put")

    assert (cancelar.status_code, reasignar.status_code) == (409, 409)


# ── Cierre (§7.2) y recorrido completo ────────────────────────

def test_recorrido_completo_hasta_el_cierre(cliente, escenario):
    mid = crear_mision(cliente, escenario)
    asignar(cliente, escenario, mid, "U-rescate")
    ruta = f"/emergencias/{escenario}/misiones/{mid}"

    assert cliente.post(f"/emergencias/{escenario}/cierre", headers=SUPERVISOR).json()["error"] == "MisionSinConcluir"
    cliente.post(f"{ruta}/inicio", headers=jefe("ana"))
    cliente.post(f"{ruta}/novedades", json={"texto": "Primera persona rescatada"}, headers=jefe("ana"))
    fin = cliente.post(f"{ruta}/finalizacion", json={"resultado": "satisfactorio", "tareas": "Rescate de dos personas"},
                       headers=jefe("ana"))
    cierre = cliente.post(f"/emergencias/{escenario}/cierre", headers=SUPERVISOR)

    assert fin.json()["estado"] == "finalizada"
    assert unidad(cliente, "U-rescate")["mision_comprometida_id"] is None
    assert cierre.status_code == 200 and cierre.json()["estado"] == "cerrada"
    assert operaciones(cliente, escenario) == [
        "emergencia_creada", "mision_creada", "mision_asignada", "mision_iniciada", "mision_novedad",
        "mision_finalizada", "emergencia_cerrada"]
    assert escenario not in [e["id"] for e in cliente.get("/emergencias", headers=SUPERVISOR).json()]


def test_no_se_cierra_sin_una_mision_satisfactoria_409(cliente, escenario):
    mid = crear_mision(cliente, escenario)
    cliente.post(f"/emergencias/{escenario}/misiones/{mid}/cancelacion", headers=OPERADOR)

    r = cliente.post(f"/emergencias/{escenario}/cierre", headers=SUPERVISOR)

    assert (r.status_code, r.json()["error"]) == (409, "SinMisionExitosa")


def test_una_emergencia_cerrada_no_admite_misiones_409(cliente, escenario):
    test_recorrido_completo_hasta_el_cierre(cliente, escenario)

    r = cliente.post(f"/emergencias/{escenario}/misiones", json={"tipo": "rescate", "objetivo": "Otra"},
                     headers=OPERADOR)

    assert (r.status_code, r.json()["error"]) == (409, "EmergenciaCerrada")
