"""Genera docs/presentar.html: presentación de UN clic (espacio, flecha o clic).

Uso:  python docs/presentar.py
El código que se muestra se lee del repo (nunca se copia a mano) y cada nota
se ubica por el texto de la línea: si alguien cambia el código y la nota ya
no coincide, el script falla en lugar de mostrar algo desactualizado.
"""
import html
import json
import re
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import diagrama_interactivo as d  # noqa: E402
from escenarios_guion import ESCENARIOS, PREAMBULO  # noqa: E402
from guion import ALTERNATIVA, DECISION, EXPLICA, PASOS  # noqa: E402


def esc(t):
    return html.escape(t, quote=False)


def md(t):
    t = esc(t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    return re.sub(r"`(.+?)`", r"<code>\1</code>", t)


def paso_enunciado(p):
    n = 0
    parrafos = []
    for par in p["texto"]:
        def marca(m):
            nonlocal n
            n += 1
            return f'<mark data-k="{n}">{esc(m.group(1))}</mark>'
        partes = re.split(r"(\[\[.+?\]\])", par)
        out = "".join(marca(re.match(r"\[\[(.+?)\]\]", x)) if x.startswith("[[") else esc(x) for x in partes)
        parrafos.append(f"<p>{out}</p>")
    cuerpo = (f'<div class="hoja"><div class="fuente">Enunciado · {esc(p["fuente"])}</div>' + "".join(parrafos) + "</div>")
    return cuerpo, n


def paso_extraer(p):
    tarjetas = "".join(
        f'<div class="tarjeta-x" data-k="{i + 1}"><span class="frase">«{esc(a)}»</span><span class="flecha">→</span>'
        f'<span class="pieza"><b>{esc(b)}</b><small>{esc(c)}</small></span></div>'
        for i, (a, b, c) in enumerate(p["items"]))
    return f'<div class="lista-x">{tarjetas}</div>', len(p["items"])


def paso_resumen(p):
    li = "".join(f'<li data-k="{i + 1}">{md(x)}</li>' for i, x in enumerate(p["puntos"]))
    return f'<ul class="resumen">{li}</ul>', len(p["puntos"])


def _comentarios_arriba(texto):
    """Pasa «código   # comentario» a dos renglones, para que el ejemplo no se parta al achicar el panel."""
    salida = []
    for linea in texto.split("\n"):
        m = re.match(r"^(\s*)(.*?\S)\s{2,}#\s*(.*)$", linea)
        if m and not m.group(2).startswith("#"):
            salida += [f"{m.group(1)}# {m.group(3)}", f"{m.group(1)}{m.group(2)}"]
        else:
            salida.append(linea)
    return "\n".join(salida)


def paso_codigo(p):
    e = d.codigo(p["archivo"], p["simbolo"])
    if e is None:
        raise SystemExit(f"No encuentro {p['simbolo']} en {p['archivo']}")
    lineas = e["codigo"].split("\n")
    ini = e["linea"]
    pos, ubic = 0, []
    for needle, *_ in p["notas"]:
        hallada = next((i for i in range(pos, len(lineas)) if needle in lineas[i]), None)
        if hallada is None:
            hallada = next((i for i in range(len(lineas)) if needle in lineas[i]), None)
        if hallada is None:
            raise SystemExit(f"Nota sin línea: {needle!r} en {p['archivo']}::{p['simbolo']}")
        ubic.append(hallada)
        pos = hallada
    filas = "".join(f'<div class="l" data-i="{i}"><span class="n">{ini + i}</span><span class="c">{esc(t) or " "}</span></div>'
                    for i, t in enumerate(lineas))
    notas = []
    for i, (_, t, q, w) in enumerate(p["notas"]):
        largo, ejemplo = EXPLICA.get((p["archivo"], p["simbolo"], t), (q, ""))
        ejemplo = _comentarios_arriba(ejemplo)
        dec = DECISION.get((p["archivo"], p["simbolo"], t))
        if dec is None:
            raise SystemExit(f"Falta la decisión de {p['simbolo']} · {t}")
        notas.append(dict(linea=ubic[i], termino=t, que=largo, porque=w, ejemplo=ejemplo,
                          problema=dec[0], otra=dec[1], eleccion=dec[2]))
    cab = (f'<div class="por-que"><b>Por qué existe:</b> {esc(p["por_que"])}</div>')
    cuerpo = (f'{cab}<div class="dos"><div class="codigo"><div class="ruta">{esc(p["archivo"])}:{ini}</div>{filas}</div>'
              f'<aside class="nota" aria-live="polite"><div class="vacio">Clic para ver línea por línea.</div></aside></div>')
    return cuerpo, len(notas), notas


COLOR_RELACION = {"c": "composición", "a": "asociación", "h": "herencia", "d": "dependencia"}


def _ancho(nombre):
    return max(100, 8 * len(nombre) + 20)


def _borde(c, w, h, otro):
    """Punto donde la recta centro→otro sale del rectángulo (c, w, h)."""
    dx, dy = otro[0] - c[0], otro[1] - c[1]
    t = min((w / 2) / abs(dx) if dx else 1e9, (h / 2) / abs(dy) if dy else 1e9)
    return (c[0] + dx * t, c[1] + dy * t)


def paso_relaciones(p):
    cajas = p["cajas"]
    primera = {}
    for i, a in enumerate(p["aristas"], 1):
        primera.setdefault(a["o"], i)
        primera.setdefault(a["d"], i)
    H = 44
    partes = []
    for i, a in enumerate(p["aristas"], 1):
        co, cd = cajas[a["o"]], cajas[a["d"]]
        o = _borde(co, _ancho(a["o"]), H, cd)
        t = _borde(cd, _ancho(a["d"]), H, co)
        dx, dy = t[0] - o[0], t[1] - o[1]
        L = (dx * dx + dy * dy) ** 0.5 or 1
        ux, uy = dx / L, dy / L
        nx, ny = -uy, ux
        dash = ' stroke-dasharray="6 5"' if a["tipo"] == "d" else ""
        g = [f'<line x1="{o[0]:.1f}" y1="{o[1]:.1f}" x2="{t[0]:.1f}" y2="{t[1]:.1f}" class="arista"{dash}/>']
        if a["tipo"] == "c":      # rombo lleno en el extremo del contenedor
            pts = [(o[0], o[1]), (o[0] + ux * 11 + nx * 6, o[1] + uy * 11 + ny * 6),
                   (o[0] + ux * 22, o[1] + uy * 22), (o[0] + ux * 11 - nx * 6, o[1] + uy * 11 - ny * 6)]
            g.append('<polygon points="' + " ".join(f"{x:.1f},{y:.1f}" for x, y in pts) + '" class="rombo"/>')
        elif a["tipo"] == "h":    # triángulo hueco en el padre
            b = (t[0] - ux * 14, t[1] - uy * 14)
            pts = [t, (b[0] + nx * 8, b[1] + ny * 8), (b[0] - nx * 8, b[1] - ny * 8)]
            g.append('<polygon points="' + " ".join(f"{x:.1f},{y:.1f}" for x, y in pts) + '" class="tri"/>')
        else:                     # flecha abierta
            b = (t[0] - ux * 12, t[1] - uy * 12)
            g.append(f'<polyline points="{b[0] + nx * 6:.1f},{b[1] + ny * 6:.1f} {t[0]:.1f},{t[1]:.1f} {b[0] - nx * 6:.1f},{b[1] - ny * 6:.1f}" class="flecha-e"/>')
        if a["mo"]:
            g.append(f'<text x="{o[0] + ux * 30 + nx * 13:.1f}" y="{o[1] + uy * 30 + ny * 13 + 4:.1f}" class="mult" text-anchor="middle">{esc(a["mo"])}</text>')
        if a["md"]:
            g.append(f'<text x="{t[0] - ux * 30 + nx * 13:.1f}" y="{t[1] - uy * 30 + ny * 13 + 4:.1f}" class="mult" text-anchor="middle">{esc(a["md"])}</text>')
        mx, my = (o[0] + t[0]) / 2, (o[1] + t[1]) / 2
        if a["tipo"] != "h":
            g.append(f'<text x="{mx:.1f}" y="{my - 7:.1f}" class="etq" text-anchor="middle">{esc(a["etiqueta"])}</text>')
        partes.append(f'<g class="ar" data-k="{i}">{"".join(g)}</g>')
    for nombre, (cx, cy) in cajas.items():
        w = _ancho(nombre)
        partes.append(f'<g class="cj" data-k="{primera[nombre]}"><rect x="{cx - w / 2:.1f}" y="{cy - H / 2:.1f}" width="{w}" height="{H}" rx="8"/>'
                      f'<text x="{cx}" y="{cy + 5}" text-anchor="middle">{esc(nombre)}</text></g>')
    ancho = int(max(x + _ancho(n) / 2 for n, (x, y) in cajas.items()) + 20)
    alto = int(max(y for x, y in cajas.values()) + H / 2 + 20)
    leyenda = ('<div class="ley"><span><i class="lr"></i> composición (contiene, no existe sin el todo)</span>'
               '<span><i class="la"></i> asociación</span><span><i class="lh"></i> herencia (es-un)</span><span><i class="ld"></i> dependencia (usa)</span></div>')
    svg = f'<svg class="rel" viewBox="0 0 {ancho} {alto}" role="img" aria-label="Diagrama que se arma de a una relación">{"".join(partes)}</svg>'
    cuerpo = (f'<div class="dos"><div class="lienzo">{svg}{leyenda}</div>'
              f'<aside class="nota" aria-live="polite"><div class="vacio">Clic para agregar la primera relación.</div></aside></div>')
    notas = [dict(origen=a["o"], destino=a["d"], tipo=COLOR_RELACION[a["tipo"]], mo=a["mo"], md=a["md"], frase=a["frase"],
                  fuente=a["fuente"], porque=a["por_que"], codigo=a["codigo"],
                  otra=ALTERNATIVA.get((a["o"], a["d"]), "")) for a in p["aristas"]]
    return cuerpo, len(notas), notas


ROTULO = {"historia": "Situación", "sin": "Sin esta decisión (ejemplo hipotético)", "problema": "Qué sale mal",
          "con": "Con el proyecto (código real)", "conclusion": "Cómo se lo explico al profesor"}


def correr(codigo, ns):
    """Ejecuta el código como en una consola: muestra lo impreso y el valor de la última expresión.
    Devuelve (texto, hubo_error)."""
    import ast
    import contextlib
    import io
    buf = io.StringIO()
    arbol = ast.parse(codigo)
    error = False
    with contextlib.redirect_stdout(buf):
        try:
            for nodo in arbol.body:
                if isinstance(nodo, ast.Expr) and not (isinstance(nodo.value, ast.Call) and getattr(nodo.value.func, "id", "") == "print"):
                    valor = eval(compile(ast.Expression(nodo.value), "<ejemplo>", "eval"), ns)
                    if valor is not None:
                        print(repr(valor))
                else:
                    exec(compile(ast.Module([nodo], []), "<ejemplo>", "exec"), ns)
        except Exception as exc:  # noqa: BLE001 - se muestra al público tal cual
            error = True
            print(f"{type(exc).__name__}: {exc}")
    return buf.getvalue().rstrip("\n"), error


def paso_escenario(p):
    esc_ = ESCENARIOS[p["clave"]]
    ns = {"RAIZ": str(AQUI.parent)}
    exec(PREAMBULO, ns)
    partes = []
    for i, (clase, titulo, contenido) in enumerate(esc_["bloques"], 1):
        if clase in ("sin", "con"):
            salida, error = correr(contenido, ns)
            cuerpo = (f'<pre class="cd">{esc(contenido)}</pre>'
                      f'<pre class="out{" err" if error else ""}">{esc(salida) or "(sin salida)"}</pre>')
        else:
            cuerpo = f'<p>{md(contenido)}</p>'
        partes.append(f'<div class="bq b-{clase}" data-k="{i}"><div class="bh">{esc(ROTULO[clase])}{(' · <span>' + esc(titulo) + '</span>') if clase in ('sin', 'con') else ''}</div>{cuerpo}</div>')
    return f'<div class="escenario">{"".join(partes)}</div>', len(esc_["bloques"]), esc_["titulo"]


def construir():
    secciones, meta = [], []
    for idx, p in enumerate(PASOS):
        notas = None
        if p["tipo"] == "enunciado":
            cuerpo, n = paso_enunciado(p)
        elif p["tipo"] == "extraer":
            cuerpo, n = paso_extraer(p)
        elif p["tipo"] == "resumen":
            cuerpo, n = paso_resumen(p)
        elif p["tipo"] == "escenario":
            cuerpo, n, p["titulo"] = paso_escenario(p)
            p["titulo"] = "0 · " + p["titulo"]
        elif p["tipo"] == "relaciones":
            cuerpo, n, notas = paso_relaciones(p)
        else:
            cuerpo, n, notas = paso_codigo(p)
        titulo = f"{idx + 1} · " + p["titulo"].split(" · ", 1)[1]
        secciones.append(f'<section class="paso" id="p{idx}" data-tipo="{p["tipo"]}" hidden><h2>{esc(titulo)}</h2>{cuerpo}</section>')
        meta.append(dict(titulo=titulo, n=n, tipo=p["tipo"], clase=p.get("clase"), notas=notas))
    return "\n".join(secciones), meta


PLANTILLA = r"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>CRCE · Presentación</title>
<style>
:root{--bg:#f1f2f7;--ink:#161a2b;--mut:#5b6078;--ac:#4338ca;--ac2:#312e81;--rojo:#d11a2a;--card:#fff;--sh:0 1px 2px rgba(22,26,43,.06),0 8px 24px rgba(22,26,43,.08)}
*{box-sizing:border-box}html,body{height:100%;margin:0}
body{background:var(--bg);color:var(--ink);font:18px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif;display:flex;flex-direction:column;cursor:pointer;user-select:none}
header{display:flex;gap:12px;align-items:center;padding:10px 20px;background:#fff;box-shadow:0 1px 0 #e3e5ee;cursor:default}
header h1{font-size:15px;margin:0;color:var(--ac2);flex:1;font-weight:650}
header button,header select{font:inherit;font-size:14px;padding:6px 12px;border:1px solid #cfd2e3;border-radius:8px;background:#fff;color:var(--ink);cursor:pointer}
button:focus-visible,select:focus-visible{outline:3px solid var(--ac);outline-offset:2px}
#barra{height:4px;background:#dfe1ee}#barra i{display:block;height:100%;width:0;background:var(--ac);transition:width .25s}
main{flex:1;overflow:auto;padding:28px 6vw 12px}
h2{margin:0 0 18px;font-size:clamp(22px,2.6vw,32px);color:var(--ac2)}
.hoja{background:var(--card);border-radius:14px;box-shadow:var(--sh);padding:28px 36px;max-width:980px;font:clamp(19px,2.1vw,25px)/1.65 Georgia,serif}
.hoja p{margin:0 0 14px}.fuente{font:600 13px system-ui;color:var(--mut);margin-bottom:14px}
mark{background:transparent;color:inherit;padding:0 2px;border-radius:3px;transition:all .3s}
mark.on{background:#ffd9dc;color:var(--rojo);font-weight:700;box-shadow:inset 0 -3px 0 var(--rojo)}
.lista-x{display:grid;gap:10px;max-width:980px}
.tarjeta-x{display:none;grid-template-columns:1fr 40px 1fr;align-items:center;background:#fff;border-radius:12px;box-shadow:var(--sh);padding:12px 18px;border-left:5px solid var(--rojo)}
.tarjeta-x.on{display:grid;animation:ent .3s}
@keyframes ent{from{opacity:0;transform:translateX(-14px)}}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
.frase{color:var(--rojo);font-weight:600}.flecha{text-align:center;color:var(--mut)}.pieza b{color:var(--ac2)}.pieza small{display:block;color:var(--mut)}
.resumen{max-width:980px;padding:0;list-style:none;display:grid;gap:12px}.resumen li{display:none;background:#fff;border-radius:12px;box-shadow:var(--sh);padding:14px 20px;font-size:clamp(18px,2vw,23px)}
.resumen li.on{display:block;animation:ent .3s}code{font:.9em ui-monospace,Menlo,Consolas,monospace;background:#eceefb;padding:1px 6px;border-radius:5px}
.por-que{background:#e9e8fb;border-radius:10px;padding:10px 16px;margin-bottom:14px;color:var(--ac2);font-size:17px;max-width:1200px}
.dos{display:grid;grid-template-columns:minmax(0,1.5fr) minmax(280px,1fr);gap:18px;align-items:start}
.codigo{background:#1b1d33;color:#dfe2f7;border-radius:12px;padding:14px 0;font:15px/1.65 ui-monospace,Menlo,Consolas,monospace;box-shadow:var(--sh);overflow:auto;max-height:62vh;scroll-padding:40px}
.ruta{padding:0 16px 8px;color:#8f94c4;font-size:13px}
.l{display:flex;padding:0 16px;opacity:.38;transition:opacity .2s,background .2s;white-space:pre-wrap;word-break:break-word}.l .c{flex:1;padding-left:8px;text-indent:0}.l .n{width:44px;color:#6e73a8;flex:none;text-align:right;padding-right:14px}
.l.vista{opacity:.75}.l.act{opacity:1;background:#3b3f78;box-shadow:inset 4px 0 0 #ffb454}
.nota{background:#fff;border-radius:12px;box-shadow:var(--sh);padding:18px 20px;position:sticky;top:0;min-height:170px;max-height:calc(100vh - 230px);overflow:auto}
.nota .t{font:700 22px system-ui;color:var(--ac2)}.nota .q{margin:8px 0;font-size:17px}.nota .w{color:var(--mut);font-size:17px}.nota .w b{color:var(--rojo)}.vacio{color:var(--mut)}
footer{background:#fff;box-shadow:0 -1px 0 #e3e5ee;padding:8px 20px;display:flex;gap:8px;align-items:center;flex-wrap:wrap;font-size:13px;cursor:default;min-height:44px}
.chip{border:0;cursor:pointer;padding:3px 11px;border-radius:999px;background:#e9e8fb;color:var(--ac2);font:600 13px ui-monospace,Menlo,monospace}.chip.nuevo{background:var(--ac);color:#fff}
#estado{margin-left:auto;color:var(--mut)}
.fin{font-size:30px;color:var(--ac2)}
.escenario{display:grid;gap:12px;max-width:1100px}
.bq{display:none;background:#fff;border-radius:12px;box-shadow:var(--sh);padding:14px 18px;border-left:6px solid #9aa0c8}
.bq.on{display:block;animation:ent .3s}.bq p{margin:6px 0 0;font-size:19px}
.bh{font:700 12px system-ui;color:var(--mut);text-transform:none}.bh span{color:var(--ink);font-size:14px}
.b-sin{border-left-color:#e08a00}.b-problema{border-left-color:var(--rojo);background:#fff5f6}.b-problema .bh{color:var(--rojo)}
.b-con{border-left-color:#1f9d55}.b-conclusion{border-left-color:var(--ac);background:#eceafd}.b-conclusion p{font-weight:600;color:var(--ac2)}
pre.cd{margin:8px 0 0;background:#1b1d33;color:#dfe2f7;border-radius:8px 8px 0 0;padding:10px 14px;font:14px/1.5 ui-monospace,Menlo,Consolas,monospace;white-space:pre-wrap;user-select:text}
pre.out{margin:0;background:#0f1124;color:#8ff0b0;border-radius:0 0 8px 8px;padding:8px 14px;font:14px/1.5 ui-monospace,Menlo,Consolas,monospace;white-space:pre-wrap;user-select:text}
pre.out::before{content:"salida real";display:block;font:700 11px system-ui;color:#7a80ad;margin-bottom:3px}
pre.out.err{color:#ff9aa5}
.lienzo{background:#fff;border-radius:12px;box-shadow:var(--sh);padding:14px}
svg.rel{width:100%;height:auto;display:block}
svg.rel [data-k]{opacity:0;transition:opacity .35s}svg.rel [data-k].on{opacity:1}
.cj rect{fill:#eef0ff;stroke:var(--ac);stroke-width:1.6}.cj text{font:600 14px ui-monospace,Menlo,monospace;fill:var(--ac2)}
.arista{stroke:#7a80ad;stroke-width:1.8}.ar.cur .arista{stroke:var(--rojo);stroke-width:2.6}
.rombo{fill:#312e81;stroke:#312e81}.tri{fill:#fff;stroke:#312e81;stroke-width:1.8}.flecha-e{fill:none;stroke:#312e81;stroke-width:1.8}
.ar.cur .rombo{fill:var(--rojo);stroke:var(--rojo)}.ar.cur .tri,.ar.cur .flecha-e{stroke:var(--rojo)}
.mult{font:700 14px system-ui;fill:var(--rojo)}.etq{font:600 13px system-ui;fill:#444a73;paint-order:stroke;stroke:#fff;stroke-width:4px}
.ley{display:flex;gap:14px;flex-wrap:wrap;font-size:13px;color:var(--mut);margin-top:8px}.ley i{display:inline-block;width:18px;height:0;border-top:2px solid #312e81;vertical-align:middle;margin-right:5px}
.ley .ld{border-top-style:dashed}.ley .lr{border-top-width:5px}
pre.ej{margin:6px 0 10px;background:#1b1d33;color:#dfe2f7;border-radius:8px;padding:10px 12px;font:13px/1.45 ui-monospace,Menlo,Consolas,monospace;white-space:pre;overflow-x:auto;user-select:text}
.nota .dec{margin-top:10px;padding:10px 12px;background:#f3f2ff;border-left:4px solid var(--ac);border-radius:6px;font-size:15.5px;line-height:1.4}.nota .dh{font:700 12px system-ui;color:var(--ac2);margin-top:8px}.nota .dh:first-child{margin-top:0}.nota .e{font:700 13px system-ui;color:var(--mut);margin-top:12px}
.nota .fr{color:var(--rojo);font-weight:700}.nota .cod{margin-top:8px;font:14px ui-monospace,monospace;color:var(--ac2)}
</style></head><body>
<header><h1>CRCE · cómo se construyó el modelo</h1>
<select id="ir" aria-label="Ir a un paso"></select>
<button id="atras">← Atrás</button><button id="sig">Siguiente →</button><button id="fs" aria-label="Pantalla completa">Pantalla completa</button></header>
<div id="barra"><i></i></div>
<main id="escena">__PASOS__</main>
<footer><span>Modelo hasta ahora:</span><span id="mapa" style="display:flex;gap:6px;flex-wrap:wrap"></span><span id="estado"></span></footer>
<script>
const META=__META__;let i=0,k=0;
const $=s=>document.querySelector(s),pasos=[...document.querySelectorAll('.paso')];
const sel=$('#ir');META.forEach((m,x)=>sel.add(new Option(m.titulo,x)));
function mapaHasta(){const v=[];for(let x=0;x<=i;x++){const c=META[x].clase;if(c&&!v.includes(c))v.push(c)}return v}
function pintar(){
 pasos.forEach((p,x)=>p.hidden=x!==i);const p=pasos[i],m=META[i];
 if(m.tipo==='codigo'){
  const ls=p.querySelectorAll('.l');ls.forEach(l=>l.classList.remove('act','vista'));
  const cart=p.querySelector('.nota');
  if(k>0){const n=m.notas[k-1];for(let j=0;j<k-1;j++)ls[m.notas[j].linea].classList.add('vista');
   ls[n.linea].classList.add('act');const cd=p.querySelector('.codigo'),L=ls[n.linea];cd.scrollTo({top:Math.max(0,L.offsetTop-cd.clientHeight/2),behavior:'auto'});
   cart.innerHTML='<div class="t"></div><div class="q"></div><div class="w"></div>';
   cart.querySelector('.t').textContent=n.termino;cart.querySelector('.q').textContent=n.que;

   cart.querySelector('.w').innerHTML='<b>Por qué acá:</b> ';cart.querySelector('.w').append(n.porque);
   const dc=document.createElement('div');dc.className='dec';
   [['Problema',n.problema],['Otra opción que se descartó',n.otra],['Por qué se eligió esto',n.eleccion]].forEach(([a,b])=>{const h=document.createElement('div');h.className='dh';h.textContent=a;const t=document.createElement('div');t.textContent=b;dc.append(h,t)});
   cart.querySelector('.q').after(dc);
   if(n.ejemplo){const e1=document.createElement('div');e1.className='e';e1.textContent='Ejemplo';const pr=document.createElement('pre');pr.className='ej';pr.textContent=n.ejemplo;dc.after(e1,pr)}}
  else cart.innerHTML='<div class="vacio">Clic para ver línea por línea.</div>';
 }else if(m.tipo==='relaciones'){
  p.querySelectorAll('[data-k]').forEach(e=>{e.classList.toggle('on',+e.dataset.k<=k);e.classList.toggle('cur',+e.dataset.k===k)});
  const cart=p.querySelector('.nota');
  if(k>0){const r=m.notas[k-1];cart.innerHTML='';const add=(c,t)=>{const d=document.createElement('div');d.className=c;d.textContent=t;cart.append(d);return d};
   add('t',r.origen+' → '+r.destino);add('q',r.tipo+(r.mo||r.md?' · '+(r.mo||'')+' a '+(r.md||''):''));
   if(r.frase){const f=add('q','');const b=document.createElement('span');b.className='fr';b.textContent='«'+r.frase+'»';f.append(b,' '+r.fuente)}
   const w=add('w','');const bb=document.createElement('b');bb.textContent='Por qué: ';w.append(bb,r.porque);
   if(r.codigo)add('cod','En el código: '+r.codigo);
   if(r.otra){const dc=add('dec','');const h=document.createElement('div');h.className='dh';h.textContent='Otra opción que se descartó';const t=document.createElement('div');t.textContent=r.otra;dc.append(h,t)}}
  else cart.innerHTML='<div class="vacio">Clic para agregar la primera relación.</div>';
 }else{p.querySelectorAll('[data-k]').forEach(e=>e.classList.toggle('on',+e.dataset.k<=k))}
 const ch=mapaHasta();$('#mapa').innerHTML='';ch.forEach((c,x)=>{const s=document.createElement('button');s.title='Ver en el diagrama';s.onclick=ev=>{ev.stopPropagation();parent.postMessage({modo:'diagrama',clase:c},'*')};s.className='chip'+(x===ch.length-1&&m.clase&&k===0?' nuevo':'');s.textContent=c;$('#mapa').append(s)});
 $('#estado').textContent=`Paso ${i+1}/${META.length} · clic ${k}/${m.n}`;
 $('#barra i').style.width=((i+(m.n?k/m.n:1))/META.length*100)+'%';sel.value=i;
}
function enfocarUltimo(){const p=pasos[i];if(META[i].tipo==='escenario'&&k>0){const v=p.querySelectorAll('.bq.on');const u=v[v.length-1];if(u)u.scrollIntoView({block:'nearest',behavior:'auto'})}}
function sig(){if(k<META[i].n)k++;else if(i<META.length-1){i++;k=0}pintar();enfocarUltimo()}
function atras(){if(k>0)k--;else if(i>0){i--;k=META[i].n}pintar();enfocarUltimo()}
document.addEventListener('keydown',e=>{if(e.target.tagName==='SELECT')return;
 if([' ','ArrowRight','Enter','PageDown'].includes(e.key)){e.preventDefault();sig()}
 else if(['ArrowLeft','Backspace','PageUp'].includes(e.key)){e.preventDefault();atras()}
 else if(e.key==='f')fs();else if(e.key==='d'&&parent!==window)parent.postMessage({modo:'diagrama',clase:META[i].clase},'*');else if(e.key==='Home'){i=0;k=0;pintar()}});
document.addEventListener('click',e=>{if(e.target.closest('header,footer'))return;sig()});
$('#sig').onclick=e=>{e.stopPropagation();sig()};$('#atras').onclick=e=>{e.stopPropagation();atras()};
function fs(){document.fullscreenElement?document.exitFullscreen():document.documentElement.requestFullscreen()}
$('#fs').onclick=e=>{e.stopPropagation();fs()};
sel.onchange=()=>{i=+sel.value;k=0;pintar();sel.blur()};
pintar();
</script></body></html>"""


def main():
    cuerpo, meta = construir()
    salida = AQUI / "presentar.html"
    salida.write_text(PLANTILLA.replace("__PASOS__", cuerpo).replace("__META__", json.dumps(meta, ensure_ascii=False)), encoding="utf-8")
    print(f"{salida} · {len(meta)} pasos · {sum(m['n'] for m in meta)} clics")


if __name__ == "__main__":
    main()
