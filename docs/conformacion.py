"""Sección «Conformación del diagrama»: del enunciado a las clases, de las clases a las relaciones.

1. Qué se extrae del enunciado.
2. Una diapositiva por clase: lo que dice el enunciado (con su §) y la caja UML leída del código real.
3. Las relaciones, en pasos acumulativos sobre el diagrama compacto.
4. El diagrama de clases completo.

Las cajas y el diagrama salen de diagrama_interactivo.py, que lee el código: si el código cambia,
la sección cambia con él.
"""
import html
import re

import diagrama_interactivo as d


def esc(t):
    return html.escape(str(t), quote=False)


def md(t):
    t = esc(t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    return re.sub(r"`(.+?)`", r"<code>\1</code>", t)


# ───────────────────────── 1 · las clases, tal como las pide el enunciado ─────────────────────────
# (título, [clases a dibujar], [(lo que dice el enunciado, §, en qué se convierte)], idea)
CLASES = [
    ("Aviso: lo que informa el reportante", ["Aviso"], [
        ("Al registrar un aviso se indica ubicación, tipo de situación, gravedad estimada y una descripción.", "§2.1",
         "atributos `ubicacion`, `tipo`, `gravedad_estimada`, `descripcion`"),
        ("Mientras esté pendiente, su reportante puede agregar notas; cada nota conserva autor, fecha y hora.", "§2.1",
         "`agregar_nota()` y el valor `Nota`"),
        ("Empieza pendiente; un operador lo acepta y origina una emergencia, o lo descarta con una justificación.", "§7.1",
         "`estado`, `aceptar()`, `descartar()` y el valor `Descarte`"),
        ("Se registra la creación y la evaluación de cada aviso.", "§9", "`registros`"),
    ], "El aviso es una entidad: tiene identidad y cambia de estado."),
    ("Emergencia: lo que se atiende", ["Emergencia"], [
        ("Conserva situación, gravedad, ubicación, aviso de origen y misiones asociadas.", "§7.2",
         "`tipo`, `gravedad`, `ubicacion`, `aviso_id`, `misiones`"),
        ("Mientras esté abierta, el operador agrega misiones compatibles con la situación.", "§7.2, §6.4",
         "`crear_mision()`"),
        ("El operador asigna, reasigna y cancela; el jefe rechaza, inicia, registra novedades y finaliza.", "§2.2, §2.3",
         "`asignar_mision()`, `iniciar_mision()`, `finalizar_mision()`…"),
        ("Solo el supervisor la cierra, cuando todas sus misiones concluyeron y alguna fue satisfactoria.", "§7.2",
         "`cerrar()`"),
        ("Las abiertas se ordenan por gravedad y por el momento de aceptación del aviso.", "§4", "`creada_en`"),
    ], "La emergencia es la raíz de sus misiones: todo cambio sobre una misión pasa por ella."),
    ("Misión: cada intervención", ["Mision", "Evacuacion", "Rescate", "AsistenciaSanitaria"], [
        ("Hay tres tipos de misión: evacuación, rescate y asistencia sanitaria, cada una con sus requisitos.", "§6.1 a §6.3",
         "`Mision` abstracta y tres subclases"),
        ("Los requisitos dependen del tipo de misión, no de la situación; cada situación admite ciertos tipos.", "§6.4",
         "`puestos`, `situaciones_admitidas`, `verificar_vehiculo()`"),
        ("Atraviesa los estados pendiente, asignada, en ejecución, finalizada y cancelada.", "§8.1", "`estado`"),
        ("Pertenece a una sola emergencia y tiene, como máximo, una unidad asignada.", "§6", "`asignacion`"),
        ("La evacuación indica cuántas personas trasladar.", "§6.1", "`cantidad` en `Evacuacion`"),
    ], "Lo común vive en Mision; cada subclase declara solo lo que la distingue."),
    ("Novedad y Resultado: lo que informa el jefe", ["Novedad", "Resultado"], [
        ("Durante la ejecución, el jefe puede registrar novedades.", "§2.3", "valor `Novedad`: jefe, texto y fecha"),
        ("Al finalizar registra un resultado, satisfactorio o no, y describe las tareas realizadas.", "§2.3",
         "valor `Resultado`: resultado, tareas y fecha"),
    ], "Son valores inmutables: lo informado no se cambia después."),
    ("Unidad: el conjunto que se envía", ["Unidad"], [
        ("Tiene identificación, base, jefe, vehículo, dotación de personal, equipamiento y condición de servicio.", "§5.2",
         "atributos `base_id`, `jefe_id`, `vehiculo`, `personal`, `equipamiento`, `condicion`"),
        ("Puede estar habilitada, en mantenimiento o fuera de servicio.", "§8.4",
         "`declarar_en_mantenimiento()`, `restablecer_servicio()`…"),
        ("Al recibir una misión queda reservada y no se modifica hasta liberarse.", "§8.4",
         "`mision_id`, `comprometer()`, `liberar()`"),
        ("Un jefe solo opera sobre misiones de su propia unidad.", "§2.3", "`exigir_jefe()`"),
    ], "La condición de servicio y el compromiso con una misión son dos datos distintos."),
    ("Vehículo: tres categorías", ["Vehiculo", "TransportePersonas", "VehiculoRescate", "Ambulancia"], [
        ("Cada vehículo tiene identificación, categoría y condición operativa.", "§5.4", "`id`, `condicion`, `categoria`"),
        ("Hay transporte de personas, vehículo de rescate y ambulancia.", "§5.4", "`Vehiculo` abstracta y tres subclases"),
        ("El transporte tiene una capacidad máxima de evacuados.", "§5.4", "`capacidad_evacuados`"),
        ("Fuera de servicio, no puede usarse en una misión.", "§5.4", "`verificar_operativo()`"),
    ], "Cada categoría responde para qué misión sirve: nadie compara categorías con if."),
    ("Persona y Equipo: los recursos", ["Persona", "Equipo"], [
        ("El personal tiene identificación y una o varias competencias.", "§5.3",
         "`Persona`: `id`, `nombre`, `competencias`, `tiene()`"),
        ("Cada elemento de equipo tiene identificación, categoría y condición operativa.", "§5.5",
         "`Equipo`: `id`, `categoria`, `condicion`"),
        ("Un elemento fuera de servicio no satisface el requisito de la misión.", "§5.5", "`con_condicion()`"),
    ], "Son valores: se validan al crearse y no cambian."),
    ("Flota: todas las unidades juntas", ["Flota"], [
        ("Hay varias bases operativas, cada una con identificación y ubicación; cada unidad pertenece a una base.", "§5.1",
         "`BaseOperativa`, `bases`, `unidades_de()`"),
        ("Una misma persona, vehículo o equipo no puede formar parte de dos unidades a la vez.", "§5.2",
         "`incorporar_unidad()`, `incorporar_personal()`…"),
    ], "Una unidad sola no ve a las demás: la regla de no repetir recursos necesita a la Flota."),
    ("Registro: la constancia de cada cambio", ["Registro"], [
        ("Cada registro identifica actor, fecha y hora, operación y recursos afectados, y conserva cambios y motivos.", "§9",
         "`actor_id`, `fecha_hora`, `operacion`, `recursos`, `detalle`"),
        ("Los registros no pueden modificarse ni eliminarse.", "§9", "valor inmutable"),
    ], "Aviso, Emergencia y Unidad guardan su propio historial de registros."),
]

# ───────────────────────── 2 · las relaciones, en pasos ─────────────────────────
# (título, [pares nuevos "Origen Destino"], [(relación, multiplicidad leída, §)])
PASOS = [
    ("El aviso origina la emergencia, y la emergencia reúne sus misiones",
     ["Aviso Emergencia", "Emergencia Mision", "Emergencia Registro"], [
        ("Aviso → Emergencia", "un aviso aceptado origina **una única** emergencia; uno pendiente o descartado, ninguna (1 a 0..1)", "§7.1"),
        ("Emergencia ◆ Mision", "una emergencia **contiene** cero o más misiones; cada misión pertenece a una sola", "§6, §7.2"),
        ("Emergencia ◆ Registro", "cada emergencia guarda **su historial**: al menos el registro de su creación", "§9"),
    ]),
    ("La misión: su unidad, sus tipos y lo que informa el jefe",
     ["Mision Unidad", "Mision Novedad", "Mision Resultado", "Mision Evacuacion", "Mision Rescate", "Mision AsistenciaSanitaria"], [
        ("Mision → Unidad", "una misión tiene **como máximo una** unidad asignada (0..1)", "§6"),
        ("Mision ◆ Novedad / Resultado", "registra cero o más **novedades** y, al finalizar, **un** resultado (0..1 mientras no termine)", "§2.3"),
        ("Mision △ Evacuacion, Rescate, AsistenciaSanitaria", "los tres tipos **heredan** de Mision", "§6"),
    ]),
    ("La unidad y sus recursos",
     ["Unidad Persona", "Unidad Equipo", "Unidad Vehiculo", "Mision Vehiculo",
      "Vehiculo TransportePersonas", "Vehiculo VehiculoRescate", "Vehiculo Ambulancia"], [
        ("Unidad ◆ Persona", "su **dotación**: una o más personas, jefe incluido (1..*)", "§5.2"),
        ("Unidad ◆ Vehiculo / Equipo", "**un** vehículo y cero o más equipos", "§5.2"),
        ("Vehiculo △ tres categorías", "transporte, rescate y ambulancia **heredan** de Vehiculo", "§5.4"),
        ("Mision ⇢ Vehiculo", "la misión le **pregunta** al vehículo si sirve (doble despacho)", "§6.4"),
    ]),
    ("La flota agrupa todas las unidades",
     ["Flota Unidad"], [
        ("Flota ◆ Unidad", "la flota reúne cero o más unidades y controla que **ningún recurso esté en dos**", "§5.1, §5.2"),
    ]),
]


# ───────────────────────── dibujo ─────────────────────────

def caja_uml(nombre):
    """Caja UML en HTML con los atributos y operaciones reales de la clase."""
    archivo, simbolo, estereotipo = d.CLASES[nombre]
    attrs, ops = d.miembros(archivo, simbolo, {})
    abstracta = nombre in d.ABSTRACTAS
    filas = lambda xs: "".join(f"<li>{esc(t)}</li>" for t, *_ in xs) or '<li class="vacio">—</li>'
    est = f'<small>«{esc(estereotipo)}»</small>' if estereotipo else ""
    return (f'<div class="uml{" abs" if abstracta else ""}"><div class="uml-cab">{est}<b>{esc(nombre)}</b></div>'
            f'<ul>{filas(attrs)}</ul><ul>{filas(ops)}</ul></div>')


def _svg(compacto):
    """El diagrama de clases de diagrama_interactivo: completo, o solo con nombres (compacto)."""
    original = d.miembros
    if compacto:
        d.miembros = lambda archivo, simbolo, datos: ([], [])
    try:
        datos = {}
        cajas, colder = d.disenar(datos)
        for nom, (archivo, simbolo, _) in d.CLASES.items():
            datos[simbolo] = d.codigo(archivo, simbolo, nom)
        svg = d.svg_clases(cajas, colder, datos)
    finally:
        d.miembros = original
    return svg.replace(' id="svgc"', "", 1)


def _marcar(svg, hechos, nuevos):
    """Oculta las relaciones que todavía no se vieron y resalta las de este paso."""
    def clase_de(n):
        if any(n.startswith(p) for p in nuevos):
            return "nueva"
        return "" if any(n.startswith(p) for p in hechos) else "oculta"
    svg = re.sub(r'class="(ln|et|mu)" data-n="([^"]+)"',
                 lambda m: f'class="{m.group(1)} {clase_de(m.group(2))}" data-n="{m.group(2)}"', svg)
    foco = {c for p in nuevos for c in p.split()}
    return re.sub(r'<g class="nodo([^"]*)" data-k="([^"]+)"',
                  lambda m: f'<g class="nodo{m.group(1)}{" foco" if m.group(2) in foco else ""}" data-k="{m.group(2)}"', svg)


def slides():
    s = []
    proceso = "".join(f'<div class="paso-c"><b>{n}</b><span>{esc(t)}</span><small>{esc(x)}</small></div>' for n, t, x in [
        (1, "Leer el enunciado", "marcar quién informa, qué se registra y qué reglas se repiten"),
        (2, "Armar cada clase", "lo que sabe (atributos) y lo que hace (operaciones)"),
        (3, "Relacionarlas", "quién contiene a quién, con qué multiplicidad"),
        (4, "El diagrama completo", "lo mismo que está en el código"),
    ])
    s.append(dict(eyebrow="conformación del diagrama", titulo="Del enunciado al diagrama de clases", grande=True,
                  html=f'<p class="lead">Antes del código, el modelo: se lee el enunciado, se arma cada clase con lo que '
                       f'sabe y lo que hace, y recién después se definen las relaciones entre ellas.</p>'
                       f'<div class="proceso-c">{proceso}</div>'))
    for n, (titulo, clases, dichos, idea) in enumerate(CLASES, 1):
        filas = "".join(
            f'<li><p>{esc(t)} <span class="sec">{esc(sec)}</span></p><p class="a">→ {md(a)}</p></li>' for t, sec, a in dichos)
        principal, *hijas = clases
        if hijas and principal in d.HERENCIA:
            cajas = caja_uml(principal) + '<div class="hijas">' + "".join(caja_uml(h) for h in hijas) + "</div>"
        else:
            cajas = '<div class="lado">' + "".join(caja_uml(c) for c in clases) + "</div>"
        s.append(dict(eyebrow=f"conformación del diagrama · clase {n} de {len(CLASES)}", titulo=titulo,
                      clase=d.CLASES[principal][1],
                      html=f'<div class="conf"><div class="card"><h3>Lo que dice el enunciado</h3><ul class="dichos">{filas}</ul>'
                           f'<div class="callout">{esc(idea)}</div></div><div class="umls">{cajas}</div></div>'))
    compacto, hechos = _svg(compacto=True), []
    for n, (titulo, nuevos, explic) in enumerate(PASOS, 1):
        lista = "".join(f'<li><code>{esc(r)}</code><span>{md(t)}</span><span class="sec">{esc(sec)}</span></li>'
                        for r, t, sec in explic)
        s.append(dict(eyebrow=f"conformación del diagrama · relaciones, paso {n} de {len(PASOS)}", titulo=titulo,
                      html=f'<div class="dgw paso">{_marcar(compacto, hechos, nuevos)}</div><ul class="rels">{lista}</ul>'))
        hechos += nuevos
    total = len(d.RELACIONES) + sum(len(h) for h in d.HERENCIA.values())
    s.append(dict(eyebrow="conformación del diagrama · resultado", titulo="El diagrama de clases completo", clase="Emergencia",
                  html=f'<div class="final"><div class="dgw completo"><div class="zoom" tabindex="0" '
                       f'aria-label="Diagrama de clases. Rueda del mouse para acercar, arrastrá para moverte.">{_svg(compacto=False)}</div>'
                       f'<div class="zctl"><button type="button" data-z="-" aria-label="Alejar">−</button>'
                       f'<button type="button" data-z="+" aria-label="Acercar">+</button>'
                       f'<button type="button" data-z="0">Ajustar</button><span>Rueda para acercar · arrastrá para moverte</span></div></div>'
                       f'<div class="card"><h3>Lo que quedó</h3><ul class="cifras">'
                       f'<li><b>{len(d.CLASES)}</b> clases, leídas del código</li>'
                       f'<li><b>{total}</b> relaciones: {len(d.RELACIONES)} entre clases y '
                       f'{sum(len(h) for h in d.HERENCIA.values())} de herencia</li>'
                       f'<li><b>{len(d.HERENCIA)}</b> jerarquías: Mision y Vehiculo</li></ul>'
                       f'<div class="callout">Para ver el código de cada clase, los estados de la misión o la lista, '
                       f'abrí <b>Diagramas</b> desde el menú ☰ (tecla <b>D</b>).</div></div></div>{ZOOM_JS}'))
    return s


ZOOM_JS = r"""<script>
/* zoom y desplazamiento del diagrama completo: rueda para acercar, arrastrar para moverse */
document.querySelectorAll('.dgw.completo').forEach(caja=>{
 const z=caja.querySelector('.zoom'),svg=z.querySelector('svg'),vb=svg.viewBox.baseVal;
 svg.setAttribute('width',vb.width);svg.setAttribute('height',vb.height);
 let s=1,x=0,y=0,movido=false;
 const pintar=()=>{svg.style.transform=`translate(${x}px,${y}px) scale(${s})`};
 const ajustar=()=>{const w=z.clientWidth,h=z.clientHeight;if(!w||!h)return;
  s=Math.min(w/vb.width,h/vb.height)*.97;x=(w-vb.width*s)/2;y=(h-vb.height*s)/2;movido=false;pintar()};
 const acercar=(f,cx,cy)=>{const n=Math.min(4,Math.max(.15,s*f));if(cx===undefined){cx=z.clientWidth/2;cy=z.clientHeight/2}
  x=cx-(cx-x)*n/s;y=cy-(cy-y)*n/s;s=n;movido=true;pintar()};
 new ResizeObserver(()=>{if(!movido)ajustar()}).observe(z);
 z.addEventListener('wheel',e=>{e.preventDefault();const r=z.getBoundingClientRect();acercar(e.deltaY<0?1.15:1/1.15,e.clientX-r.left,e.clientY-r.top)},{passive:false});
 let arr=null;
 z.addEventListener('pointerdown',e=>{arr={px:e.clientX,py:e.clientY,x,y};z.setPointerCapture(e.pointerId);z.classList.add('arrastra')});
 z.addEventListener('pointermove',e=>{if(!arr)return;x=arr.x+e.clientX-arr.px;y=arr.y+e.clientY-arr.py;movido=true;pintar()});
 const soltar=()=>{arr=null;z.classList.remove('arrastra')};z.addEventListener('pointerup',soltar);z.addEventListener('pointercancel',soltar);
 z.addEventListener('dblclick',ajustar);
 z.addEventListener('click',e=>e.stopPropagation());
 caja.querySelectorAll('[data-z]').forEach(b=>b.addEventListener('click',e=>{e.stopPropagation();const t=b.dataset.z;
  if(t==='0')ajustar();else acercar(t==='+'?1.3:1/1.3)}));
});
</script>"""


CSS = r"""
/* ── conformación del diagrama ─────────────────────────────────────────── */
.proceso-c{display:grid;grid-template-columns:repeat(4,1fr);gap:clamp(10px,1.2vw,16px);margin-top:clamp(14px,3vh,30px)}
.paso-c{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:clamp(14px,2.4vh,22px) 18px;display:flex;flex-direction:column;gap:6px}
.paso-c b{display:inline-grid;place-items:center;width:34px;height:34px;border-radius:50%;background:var(--accent);color:#0b1020;font-size:16px}
.paso-c span{font-weight:700;font-size:clamp(16px,1.5vw,20px)}.paso-c small{color:var(--muted);font-size:clamp(13px,1.1vw,15px);line-height:1.4}
.conf{display:grid;grid-template-columns:minmax(0,1.05fr) minmax(0,1fr);gap:clamp(14px,1.6vw,24px);align-items:start}
.dichos{list-style:none;padding:0;margin:0}
.dichos li{padding:clamp(6px,1.1vh,10px) 0;border-bottom:1px solid var(--line);margin:0}.dichos li:last-child{border-bottom:0}
.dichos p{margin:0;font-size:clamp(14px,1.25vw,17px);line-height:1.45;color:var(--soft)}
.dichos p.a{color:var(--accent);font-size:clamp(13px,1.1vw,15px);margin-top:3px}.dichos p.a code{color:#bce9df}
.sec{display:inline-block;color:var(--gold);font-size:.82em;font-weight:700;margin-left:4px;white-space:nowrap}
.umls{display:flex;flex-direction:column;gap:12px;align-items:stretch}
.umls .lado{display:flex;gap:12px;align-items:flex-start;flex-wrap:wrap}.umls .lado .uml{flex:1;min-width:220px}
.umls .hijas{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;position:relative;padding-top:14px}
.umls .hijas::before{content:"△ heredan de la clase de arriba";position:absolute;top:-4px;left:2px;color:var(--muted);font-size:12px}
.uml{background:var(--panel);border:1px solid var(--line);border-radius:12px;overflow:hidden;font:clamp(12px,1vw,14px)/1.5 ui-monospace,SFMono-Regular,Menlo,monospace}
.uml.abs{border-style:dashed}
.uml-cab{background:#1d2a44;padding:8px 12px;text-align:center;font-family:Inter,ui-sans-serif,system-ui,sans-serif}
.uml-cab small{display:block;color:var(--muted);font-size:12px}.uml-cab b{font-size:clamp(15px,1.35vw,18px);color:var(--text)}
.uml.abs .uml-cab b{font-style:italic}
.uml ul{list-style:none;margin:0;padding:6px 12px;border-top:1px solid var(--line);color:#c5d0e4;font-size:inherit;line-height:1.5}
.uml li{margin:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.uml li.vacio{color:var(--muted)}
.hijas .uml{font-size:clamp(11px,.9vw,12.5px)}
/* diagramas */
.dgw{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:10px;min-height:0}
.dgw svg{display:block;width:100%;height:auto;max-height:calc(100vh - 380px)}
.dgw .box{fill:#121a2d;stroke:#3a4a6b;stroke-width:1.2}.dgw .box.abs{stroke-dasharray:6 4}
.dgw .cab{fill:#1d2a44}.dgw .cabraiz{fill:#1f4d48}
.dgw .nm{font:700 16px Inter,ui-sans-serif,system-ui,sans-serif;fill:#eef3ff}.dgw .nm.it{font-style:italic}
.dgw .sb{font:13px Inter,ui-sans-serif,system-ui,sans-serif;fill:#9eacc6}.dgw .raiz .sb{fill:#d6f3ee}
.dgw .mb{font:13px ui-monospace,SFMono-Regular,Menlo,monospace;fill:#c5d0e4}
.dgw .sep{stroke:#2a3854}.dgw .puente,.dgw .hit{fill:transparent}.dgw .vs{display:none}
.dgw .ln{fill:none;stroke:#7d8ba8;stroke-width:1.6}.dgw .mk{fill:#7d8ba8}.dgw .mkh{fill:#121a2d;stroke:#7d8ba8;stroke-width:1.4}
.dgw .et{font:13px Inter,ui-sans-serif,system-ui,sans-serif;fill:#9eacc6;paint-order:stroke;stroke:#121a2d;stroke-width:4px}
.dgw .mu{font:700 13px Inter,ui-sans-serif,system-ui,sans-serif;fill:#f3c969;paint-order:stroke;stroke:#121a2d;stroke-width:4px}
.dgw .oculta{display:none}
.dgw.paso .nodo{opacity:.5}.dgw.paso .nodo.foco{opacity:1}.dgw.paso .nodo.foco .box{stroke:#71d5c3;stroke-width:2.4}
.dgw .ln.nueva{stroke:#71d5c3;stroke-width:3}.dgw .et.nueva{fill:#71d5c3;font-weight:700}.dgw .mu.nueva{fill:#f3c969}
.rels{list-style:none;padding:0;margin:clamp(10px,1.8vh,16px) 0 0;display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:8px 16px}
.rels li{display:flex;flex-direction:column;gap:2px;margin:0;padding:8px 12px;border-left:3px solid var(--accent);background:var(--panel);border-radius:0 10px 10px 0}
.rels code{color:#bce9df;font-weight:700}.rels span{font-size:clamp(13px,1.1vw,15px);color:var(--soft);line-height:1.4}.rels .sec{margin:0}
.final{display:grid;grid-template-columns:minmax(0,1.7fr) minmax(240px,.8fr);gap:clamp(14px,1.6vw,22px);align-items:start}
.final .dgw{padding:0;overflow:hidden;position:relative}
.dgw .zoom{height:calc(100vh - 300px);min-height:300px;overflow:hidden;cursor:grab;touch-action:none;position:relative}
.dgw .zoom.arrastra{cursor:grabbing}.dgw .zoom:focus-visible{outline:2px solid var(--accent);outline-offset:-2px}
.dgw .zoom svg{position:absolute;left:0;top:0;max-height:none;width:auto;transform-origin:0 0;user-select:none}
.zctl{display:flex;align-items:center;gap:6px;padding:8px 10px;border-top:1px solid var(--line);background:var(--panel)}
.zctl button{min-width:38px;padding:6px 10px;font-size:15px}.zctl span{color:var(--muted);font-size:12.5px;margin-left:8px}
.cifras{list-style:none;padding:0;margin:0 0 10px}.cifras li{margin:0 0 8px}.cifras b{color:var(--accent);font-size:1.3em;margin-right:4px}
@media (max-width:980px){.conf,.final,.proceso-c{grid-template-columns:1fr}}
"""
