"""Versión de 15 minutos: qué pasos y qué notas se muestran, y los ejemplos «así se ve en la web».

El guion completo sigue en guion.py / guion_extra.py (se genera como presentar_completa.html).
Acá solo se elige: no se reescribe nada, salvo los ejemplos web.
"""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

# ("p", n)               paso entero de PASOS (1-based): enunciado, extraer, relaciones
# ("e", clave)           escenario con esa clave
# ("c", archivo, símbolo, [términos])  paso de código, solo con esas notas
CORTO = [
    ("p", 1), ("p", 2), ("p", 3), ("p", 4), ("p", 5), ("p", 7),
    ("c", "dominio/catalogos.py", "Catalogo", ["Enum", "classmethod"]),
] + [("d", k) for k in (
    "ubicacion",
    "aviso_estado", "aviso_estados", "aviso_aceptar_in", "aviso_aceptar",
    "emergencia_estado", "emergencia_crear_in", "emergencia_crear", "emergencia_asignar_in", "emergencia_asignar",
    "mision_estado", "mision_transiciones", "mision_sinunidad", "mision_asignar_in", "mision_asignar", "mision_finalizar_in", "mision_finalizar",
    "vehiculo_base", "vehiculo_transporte", "mision_evacuacion", "mision_rescate",
    "dist_verificar", "dist_idea",
    "unidad_condicion", "unidad_init_in", "unidad_init", "unidad_comprometer", "unidad_liberar",
    "flota_clase", "flota_incorporar_in", "flota_incorporar")] + [
    ("p", 66), ("p", 67),
]


def seleccionar(pasos):
    """Devuelve los pasos de la versión corta (copias: no toca el guion completo)."""
    salida = []
    for it in CORTO:
        if it[0] == "p":
            salida.append(pasos[it[1] - 1])
        elif it[0] == "d":
            from guion_codigo import PASOS_DIRECTOS
            salida.append(PASOS_DIRECTOS[it[1]])
        elif it[0] == "e":
            salida.append(next(p for p in pasos if p["tipo"] == "escenario" and p["clave"] == it[1]))
        else:
            _, archivo, simbolo, terminos = it
            p = next(p for p in pasos if p["tipo"] == "codigo" and p["archivo"] == archivo and p["simbolo"] == simbolo)
            por_termino = {n[1]: n for n in p["notas"]}
            faltan = [t for t in terminos if t not in por_termino]
            if faltan:
                raise SystemExit(f"Versión corta: {simbolo} no tiene las notas {faltan}")
            salida.append({**p, "notas": [n for n in p["notas"] if n[1] in terminos]})
    return salida


# ── Mensajes reales (se ejecuta el dominio para no escribirlos a mano) ──────────
def _mensajes():
    from datetime import datetime  # noqa: F401
    from tests.escenarios import (CategoriaEquipo, Competencia as C, Equipo, Gravedad, TipoSituacion,
                                  Unidad, aviso, emergencia, t, unidad_de_rescate)
    from dominio.mision import Rescate
    from dominio.personal import Persona
    from dominio.vehiculos import VehiculoRescate
    r = {}
    a = aviso()
    a.aceptar("op-1", TipoSituacion.INUNDACION, Gravedad.MEDIA, t(5))
    try:
        a.aceptar("op-1", TipoSituacion.INUNDACION, Gravedad.MEDIA, t(6))
    except Exception as x:  # noqa: BLE001
        r["aceptar"] = (type(x).__name__, str(x))
    e = emergencia()
    u1 = unidad_de_rescate("ur1")
    e.crear_mision(Rescate("Rescatar familia", "m1"), "op-1", t(6))
    e.crear_mision(Rescate("Rescatar vecinos", "m2"), "op-1", t(7))
    e.asignar_mision("m1", u1, "op-1", t(8))
    try:
        e.asignar_mision("m2", u1, "op-1", t(9))
    except Exception as x:  # noqa: BLE001
        r["asignar"] = (type(x).__name__, str(x))
    ana = Persona("p1", "Ana", frozenset({C.CONDUCCION, C.RESCATE}))
    bruno = Persona("p2", "Bruno", frozenset({C.CONDUCCION}))
    u3 = Unidad("ur3", "base-1", jefe=ana, vehiculo=VehiculoRescate(id="v3"), personal=(bruno,),
                equipamiento=(Equipo("eq3", CategoriaEquipo.EQUIPO_DE_RESCATE),))
    try:
        e.asignar_mision("m2", u3, "op-1", t(9))
    except Exception as x:  # noqa: BLE001
        r["distribucion"] = (type(x).__name__, str(x))
    return r


def _json(d, compacto=False):
    import json
    return json.dumps(d, ensure_ascii=False) if compacto else json.dumps(d, ensure_ascii=False, indent=2)


def web():
    m = _mensajes()
    nota = "Formato ilustrativo de la API que se arma en la entrega final; los mensajes de error son los reales del dominio."
    return {
        ("dominio/aviso.py", "Aviso.aceptar"): dict(
            nota=nota,
            pantalla="Avisos pendientes › Inundación, Ruta 3 km 12", boton="Aceptar aviso",
            pedido="POST /avisos/{aviso_id}/aceptar  " + _json({"operador_id": "op-1", "tipo": "inundacion", "gravedad": "media"}, True),
            llamadas=[("Aviso.aceptar()", "recibe el pedido"),
                      ("_estado.aceptar()", "Pendiente devuelve Aceptado; si no, lanza error"),
                      ("Emergencia(...)", "se crea y valida los datos"),
                      ("Registro.de(...)", "arma el registro de la operación"),
                      ("_estado y _registros", "recién acá cambia el aviso"),
                      ("return emergencia", "la web recibe la emergencia")],
            ok=("201 Creado", _json({"emergencia_id": "e-7", "estado": "abierta", "aviso": "aceptado"}), "Primer clic en «Aceptar aviso»"),
            error=("409 Conflicto", _json({"error": m["aceptar"][0], "mensaje": m["aceptar"][1]}), "Segundo clic sobre el mismo aviso")),
        ("dominio/emergencia.py", "Emergencia.asignar_mision"): dict(
            nota=nota,
            pantalla="Emergencia e-7 › Misión «Rescatar vecinos»", boton="Asignar unidad ur2",
            pedido="POST /emergencias/e-7/misiones/m2/asignar  " + _json({"unidad_id": "ur2", "operador_id": "op-1"}, True),
            llamadas=[("Emergencia.asignar_mision()", "recibe el pedido"),
                      ("_estado.permitir_modificaciones()", "la emergencia debe estar abierta"),
                      ("Mision.asignar(unidad)", "Pendiente pasa a Asignada"),
                      ("Unidad.comprometer(mision)", "verifica las condiciones en orden"),
                      ("registro y reserva", "solo si todo pasó")],
            ok=("200 OK", _json({"mision": "m2", "estado": "asignada", "unidad": "ur2"}), "La unidad ur2 está libre y cumple todo"),
            error=("409 Conflicto", _json({"error": m["asignar"][0], "mensaje": m["asignar"][1]}), "El operador eligió ur1, que ya tiene la misión m1")),
    }
