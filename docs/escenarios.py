"""Grupo «Los 19 escenarios»: una diapositiva por PV con capturas reales y respuestas reales de la API.

Las capturas (docs/img/pv/) y las respuestas (docs/img/pv/intercambios.json) se obtuvieron
reproduciendo cada escenario contra el sistema levantado (API + Keycloak), en este orden.
"""
import json
import re
from pathlib import Path

from sistema_completo import JS, esc, md

AQUI = Path(__file__).resolve().parent
IMG = "img/pv/"
INTERCAMBIOS = json.loads((AQUI / "img" / "pv" / "intercambios.json").read_text(encoding="utf-8"))
UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")


def _corto(texto):
    return UUID.sub(lambda m: m.group(0)[:8] + "…", texto)


def foto(archivo, pie):
    return (f'<figure class="sc-foto"><img src="{IMG}{archivo}.webp" alt="{esc(pie)}" loading="lazy" tabindex="0" '
            f'title="Clic para ampliar"><figcaption>{md(pie)}</figcaption></figure>')


def http(clave, pie):
    """Un pedido real a la API y su respuesta, tal como se obtuvieron."""
    x = INTERCAMBIOS[clave]
    cuerpo = f"\n{json.dumps(x['cuerpo'], ensure_ascii=False)}" if x["cuerpo"] else ""
    resp = json.dumps(x["respuesta"], ensure_ascii=False, indent=1)
    clase = "c4" if x["codigo"] < 500 else "c5"
    return (f'<figure class="pv-http"><div class="pv-pedido"><span class="pv-quien">{esc(x["usuario"])}</span>'
            f'<code>{esc(x["metodo"])} {esc(_corto(x["ruta"]))}{esc(cuerpo)}</code></div>'
            f'<div class="pv-resp"><span class="sc-cod {clase}">{x["codigo"]}</span><pre>{esc(_corto(resp))}</pre></div>'
            f'<figcaption>{md(pie)}</figcaption></figure>')


# (PV, título, lo que pide el enunciado, cómo lo resuelve el modelo, pruebas, [evidencias])
ESCENARIOS = [
    ("PV01", "Cada reportante ve solo sus avisos",
     "Dos reportantes registran avisos distintos; cada uno consulta los suyos, pero no los del otro.",
     "`GET /avisos` filtra por el usuario del token. Para un aviso ajeno, `Usuario.exigir_acceso_a()` lanza "
     "`AccesoDenegado` → 403.",
     "test_evaluacion_avisos · test_autorizacion",
     [foto("pv01-municipio", "`municipio` ve solo su aviso de Kuanip 450; el del hospital no aparece."),
      http("pv01", "Si `municipio` pide el aviso del hospital por su id, la API lo rechaza.")]),
    ("PV02", "Aceptar un aviso y descartar otro",
     "El operador acepta una inundación confirmando su gravedad y descarta otro aviso con una justificación. "
     "Cada reportante ve la evaluación del suyo.",
     "`Aviso.aceptar()` origina la emergencia; `Aviso.descartar()` exige la justificación y la guarda en un `Descarte`. "
     "El reportante ve tipo, gravedad y estado de la emergencia, no sus misiones.",
     "test_evaluacion_avisos",
     [foto("pv02-pendientes", "El operador ve los dos avisos pendientes, con aceptar y descartar."),
      foto("pv02-hospital", "El hospital ve el descarte y su justificación."),
      foto("pv02-municipio", "El municipio ve su aviso aceptado y la emergencia abierta.")]),
    ("PV03", "Emergencias por gravedad y antigüedad",
     "Las emergencias abiertas se listan Alta, Media y Baja; a igual gravedad, primero la aceptada antes.",
     "`Emergencia.clave_de_prioridad()` devuelve (gravedad, momento de aceptación) y `abiertas_por_prioridad()` ordena "
     "por esa clave. El orden no depende de cuándo se registró el aviso.",
     "test_emergencias (incluye avisos registrados en otro orden)",
     [foto("pv03-prioridad", "Dos de gravedad alta (en orden de aceptación), luego media y baja, numeradas.")]),
    ("PV04", "Tres misiones en una emergencia",
     "Una inundación origina una evacuación de ocho personas, un rescate y una asistencia sanitaria.",
     "`Emergencia.crear_mision()` agrega cada misión; cada una es un objeto con su propio estado.",
     "test_emergencias · test_api_misiones",
     [foto("pv04-misiones", "Las tres misiones de la inundación, cada una pendiente por su cuenta.")]),
    ("PV05", "La situación limita los tipos de misión",
     "Se intenta crear una evacuación para un accidente vial: se rechaza. Luego se crean un rescate y una asistencia.",
     "Cada subclase declara `situaciones_admitidas`; `verificar_situacion()` lanza `MisionIncompatible` → 422.",
     "test_emergencias · test_api_misiones",
     [foto("pv05-rechazo", "La evacuación no está contemplada para un accidente vial."),
      foto("pv05-ok", "El rescate y la asistencia sanitaria sí se crean.")]),
    ("PV06", "Capacidad del transporte",
     "Una evacuación de ocho personas no puede ir en un vehículo de seis plazas; sí en uno con capacidad suficiente.",
     "Doble despacho: la misión llama a `vehiculo.verificar_evacuacion(cantidad)` y `TransportePersonas` compara con "
     "su capacidad.",
     "test_asignacion · test_recursos",
     [foto("pv06-rechazo", "`U-traslado-6` tiene 6 plazas: «se necesitan 8 plazas y hay 6»."),
      foto("pv06-ok", "`U-transporte-1` (20 plazas) se asigna sin problema.")]),
    ("PV07", "Competencias y cantidad de integrantes",
     "Un rescate pide conductor y dos rescatistas distintos. Con uno solo se rechaza; al incorporar otro, se acepta.",
     "`existe_distribucion()` busca una persona distinta por puesto: alguien con dos competencias no cubre dos puestos.",
     "test_asignacion · test_recursos (también el caso Ana, Bruno y Carla)",
     [foto("pv07-rechazo", "`U-rescate-3` tiene un conductor y un solo rescatista: `PersonalInsuficiente`."),
      foto("pv07-incorpora", "El responsable de recursos incorpora a Pablo, rescatista."),
      foto("pv07-ok", "Ahora la asignación se acepta.")]),
    ("PV08", "El vehículo tiene que servir para la misión",
     "Una asistencia sanitaria no se asigna a un transporte de personas, aunque la unidad tenga primeros auxilios.",
     "`Ambulancia` es la única que responde bien a `verificar_asistencia()`; las demás categorías lanzan "
     "`VehiculoIncompatible`. Sin `if` por categoría.",
     "test_asignacion",
     [foto("pv08-rechazo", "`U-traslado-6` tiene un paramédico, pero su vehículo es un transporte: se rechaza.")]),
    ("PV09", "Equipamiento fuera de servicio",
     "Con el equipo de rescate fuera de servicio la asignación se rechaza; al restablecerlo, se acepta.",
     "`verificar_equipamiento()` pide un equipo de la categoría **operativo** con `tiene_equipo_operativo()`.",
     "test_asignacion · test_recursos",
     [foto("pv09-baja", "El responsable da de baja el equipo `ER-2` de `U-rescate-2`."),
      foto("pv09-rechazo", "Rechazo: falta un equipo de rescate operativo."),
      foto("pv09-ok", "Con el equipo habilitado otra vez, la asignación se acepta.")]),
    ("PV10", "Una unidad, una misión a la vez",
     "Una unidad asignada no puede destinarse a otra misión; la primera asignación no cambia.",
     "`Unidad.comprometer()` falla con `UnidadOcupada` si ya tiene misión. La interfaz ni siquiera ofrece unidades "
     "comprometidas; el intento se hace contra la API.",
     "test_asignacion",
     [foto("pv10-comprometida", "`U-rescate-2` figura comprometida con su misión."),
      http("pv10", "Asignarla a otra misión responde 409 y no altera la primera.")]),
    ("PV11", "Ejecución de una misión",
     "El jefe inicia una misión asignada, registra una novedad y la finaliza. La unidad queda libre.",
     "Patrón State: `_Asignada.iniciar()` pasa a `_EnEjecucion`, que admite novedades y `finalizar()`. Al finalizar, "
     "la unidad se libera.",
     "test_ejecucion",
     [foto("pv11-asignada", "Diego ve la misión asignada a su unidad."),
      foto("pv11-ejecucion", "En ejecución, con una novedad registrada."),
      foto("pv11-finalizada", "Finalizada con resultado satisfactorio."),
      foto("pv11-liberada", "`U-rescate-2` vuelve a estar disponible.")]),
    ("PV12", "Cada uno opera solo lo que le corresponde",
     "Un jefe intenta finalizar una misión de otra unidad, un reportante intenta asignar y un responsable de recursos "
     "intenta cerrar una emergencia.",
     "Perfil por ruta con `requiere(...)`; relación con la unidad con `Unidad.exigir_jefe()`. Todo termina en 403. "
     "En la interfaz esas opciones no existen para esos perfiles: se demuestra con la API.",
     "test_autorizacion · test_ejecucion",
     [http("pv12-jefe", "Diego (jefe de `U-rescate-2`) intenta finalizar una misión de `U-rescate-1`."),
      http("pv12-reportante", "El hospital intenta asignar una misión."),
      http("pv12-recursos", "El responsable de recursos intenta cerrar una emergencia.")]),
    ("PV13", "Rechazo y reasignación",
     "Un jefe rechaza justificadamente una misión no iniciada y el operador la asigna a otra unidad; luego se reasigna "
     "en forma directa. En ejecución no se puede.",
     "`rechazar()` vuelve la misión a pendiente y libera la unidad; `reasignar()` cambia de unidad. `_EnEjecucion` "
     "no admite ninguna de las dos.",
     "test_ejecucion",
     [foto("pv13-rechazada", "Gabi rechaza: «La ambulancia tiene una rueda pinchada»."),
      foto("pv13-asignada-otra", "El operador la asigna a `U-ambulancia-2`."),
      foto("pv13-reasignada", "Reasignación directa a `U-ambulancia-1`."),
      http("pv13-ejecucion", "Reasignar una misión en ejecución se rechaza.")]),
    ("PV14", "Recursos de una unidad comprometida",
     "Se incorpora personal a una unidad disponible; modificar una unidad asignada se rechaza.",
     "Cada operación de recursos de `Unidad` primero exige que no esté comprometida: `UnidadComprometida` → 409.",
     "test_recursos",
     [foto("pv07-incorpora", "Incorporación en una unidad libre (`U-rescate-3`)."),
      foto("pv14-rechazo", "Retirar a alguien de `U-rescate-1`, comprometida, se rechaza.")]),
    ("PV15", "Cancelación",
     "El operador cancela una misión asignada no iniciada: la unidad queda libre y la misión no puede iniciarse.",
     "`cancelar()` pasa a `_Cancelada`, estado final que rechaza `iniciar()`.",
     "test_ejecucion",
     [foto("pv15-cancelada", "La asistencia sanitaria queda cancelada."),
      foto("pv15-libre", "`U-ambulancia-1` vuelve a estar disponible."),
      http("pv15", "Gabi intenta iniciarla igual: 409.")]),
    ("PV16", "Cierre de una emergencia",
     "No se cierra con misiones sin concluir ni sin ninguna satisfactoria. Cuando todas concluyeron y una fue "
     "satisfactoria, se cierra y ya no admite misiones.",
     "`_Abierta.cerrar()` pregunta a cada misión `verificar_concluida()` y exige `es_exitosa()` en alguna. "
     "`_Cerrada` rechaza todo cambio.",
     "test_emergencias",
     [foto("pv16-con-misiones", "Con una misión asignada: `MisionSinConcluir`."),
      foto("pv16-sin-misiones", "Sin misiones: `SinMisionExitosa`."),
      foto("pv16-cerrada", "Todo concluido y un resultado satisfactorio: cerrada."),
      http("pv16", "Una emergencia cerrada no admite misiones.")]),
    ("PV17", "Historial que no cambia",
     "El historial conserva cada operación con sus datos, incluidas las unidades anterior y nueva de una reasignación. "
     "Cambiar después una unidad no altera lo registrado.",
     "Cada operación agrega un `Registro` inmutable con copia de los datos de ese momento; no guarda referencias a "
     "la unidad.",
     "test_emergencias",
     [foto("pv17-historial", "Asignación, rechazo con justificación, reasignación (anterior y nueva) y cancelación."),
      foto("pv17-unidad-cambiada", "Después se incorpora a Tomás en `U-ambulancia-2`."),
      foto("pv17-historial-despues", "El historial de la emergencia sigue igual.")]),
    ("PV18", "Un error no deja cambios a medias",
     "Una reasignación a una unidad no apta se rechaza: se conserva la asignación anterior y la disponibilidad de "
     "ambas unidades, y no se registra.",
     "Fallar antes de modificar: `Mision.reasignar()` primero compromete la unidad nueva (que verifica todo antes de "
     "reservarse) y recién después libera la anterior; el registro se agrega al final.",
     "test_emergencias · test_api_misiones",
     [foto("pv18-rechazo", "Reasignar el rescate a una ambulancia se rechaza; sigue en `U-rescate-3`."),
      foto("pv18-u-rescate-3", "`U-rescate-3` sigue comprometida."),
      foto("pv18-u-ambulancia-1", "`U-ambulancia-1` sigue disponible."),
      foto("pv18-historial", "El historial no registra ninguna reasignación.")]),
]


def slides(resumen):
    """`resumen` es la diapositiva con la tabla de los 19 escenarios; va primero."""
    s = [resumen]
    total = len(ESCENARIOS) + 1
    for n, (pv, titulo, pide, como, pruebas, evid) in enumerate(ESCENARIOS, 1):
        cols = min(len(evid), 4)
        s.append(dict(eyebrow=f"escenarios · {pv} · {n} de {total}", titulo=f"{pv} · {titulo}", html=(
            f'<div class="pv-caso"><div class="pv-txt">'
            f'<div><h3>Qué pide el enunciado</h3><p class="explain">{md(pide)}</p></div>'
            f'<div><h3>Cómo lo resuelve el modelo</h3><p class="explain">{md(como)}</p></div>'
            f'<div><h3>Pruebas</h3><p class="sc-pie"><code>{esc(pruebas)}</code></p></div></div>'
            f'<div class="pv-evid c{cols}">{"".join(evid)}</div></div>')))
    s.append(dict(eyebrow=f"escenarios · PV19 · {total} de {total}", titulo="PV19 · Demostración integral", html=(
        '<p class="lead">El recorrido completo con los cinco participantes está en el grupo <b>10 · La interfaz en uso</b>: '
        'reportante, operador, responsable de recursos, jefe de unidad y supervisor, sobre la misma emergencia.</p>'
        '<div class="callout">Las capturas de este grupo se tomaron reproduciendo los escenarios en orden contra el sistema '
        'levantado (API, MongoDB y Keycloak). Las respuestas de la API son las que devolvió en esa corrida; los ids '
        'largos se muestran abreviados.</div>' + JS)))   # la ampliación de imágenes va al final de la página
    return s


CSS = r"""
.pv-caso{display:flex;flex-direction:column;gap:clamp(10px,1.6vh,16px)}
.pv-txt{display:grid;grid-template-columns:1fr 1.25fr .7fr;gap:8px 26px}
.pv-txt h3{margin:0 0 4px;font-size:clamp(13px,1.1vw,15px);color:var(--muted);font-weight:600}
.pv-txt .explain{margin:0}.pv-txt .sc-pie{margin:0}
.pv-evid{display:grid;gap:14px;align-items:start}
.pv-evid.c1{grid-template-columns:minmax(0,1fr);max-width:1000px}.pv-evid.c2{grid-template-columns:repeat(2,minmax(0,1fr))}
.pv-evid.c3{grid-template-columns:repeat(3,minmax(0,1fr))}.pv-evid.c4{grid-template-columns:repeat(4,minmax(0,1fr))}
.pv-evid .sc-foto img{max-height:56vh}
.pv-evid.c2 .sc-foto img,.pv-evid.c3 .sc-foto img{max-height:46vh}.pv-evid.c4 .sc-foto img{max-height:50vh}
.pv-http{margin:0;background:var(--code);border:1px solid #26334b;border-radius:10px;overflow:hidden;display:flex;flex-direction:column;min-width:0}
.pv-pedido{display:flex;gap:10px;align-items:flex-start;padding:10px 12px;border-bottom:1px solid #26334b;background:#0d1526}
.pv-pedido code{white-space:pre-wrap;word-break:break-all;color:#e6edf8;font-size:12.5px}
.pv-quien{flex:none;background:var(--gold);color:#0b1020;font-weight:700;font-size:11.5px;border-radius:99px;padding:2px 9px}
.pv-resp{display:flex;gap:10px;align-items:flex-start;padding:10px 12px}
.pv-resp pre{margin:0;white-space:pre-wrap;word-break:break-word;color:#cfe0f5;font:12.5px/1.5 ui-monospace,SFMono-Regular,Menlo,monospace}
.pv-http figcaption{font-size:12.5px;color:var(--muted);padding:0 12px 10px;line-height:1.4}
@media (max-width:900px){.pv-txt,.pv-evid.c2,.pv-evid.c3,.pv-evid.c4{grid-template-columns:1fr}}
"""
