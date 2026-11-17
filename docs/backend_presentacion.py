"""Presentación del backend con la estética de «backend1» (oscura, un tema por diapositiva).

Una lista inicial permite elegir qué presentar:
  · «Recorrido general»: las seis preguntas (problema, organización, clases, comunicación, datos, POO);
  · los 13 archivos del dominio en 7 grupos, del primero que se escribió al último que se armó.
Cada archivo tiene una ficha (qué contiene y con quién se comunica) y sus diapositivas de código,
con una nota por línea o construcción. Todo lo explicado sale de guion_archivos.py y del código real.

Genera docs/backend_presentacion.html.  Uso: python3 docs/backend_presentacion.py
"""
import html
import json
import re
import sys
import textwrap
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import backend_general as bg  # noqa: E402
import backend_meta as bm  # noqa: E402
import guion_archivos as ga  # noqa: E402

RAIZ = AQUI.parent
SALIDA = AQUI / "backend_presentacion.html"


def esc(t):
    return html.escape(str(t), quote=False)


def md(t):
    """**negrita** y `código`. El código se aparta primero: un `**detalle` no se toma como negrita."""
    codigos = []
    t = re.sub(r"`(.+?)`", lambda m: codigos.append(m.group(1)) or f"\x00{len(codigos) - 1}\x00", t)
    t = re.sub(r"\*\*(.+?)\*\*", lambda m: f"<strong>{m.group(1)}</strong>", esc(t))
    return re.sub(r"\x00(\d+)\x00", lambda m: f"<code>{esc(codigos[int(m.group(1))])}</code>", t)


def bloques(t):
    """Texto de una nota en bloques: párrafos separados por línea en blanco,
    listas con «- » y pasos numerados con «1. »."""
    salida = []
    for parrafo in t.strip().split("\n\n"):
        if parrafo.strip().startswith("```"):   # dibujo o código: se respeta tal cual
            cuerpo = parrafo.strip().strip("`").strip("\n")
            salida.append(f'<pre class="mini">{esc(cuerpo)}</pre>')
            continue
        lineas = [l.strip() for l in parrafo.strip().split("\n") if l.strip()]
        if all(l.startswith("|") for l in lineas):   # tabla: | a | b |, la 2.ª fila separa el encabezado
            filas = [[c.strip() for c in l.strip("|").split("|")] for l in lineas if not set(l) <= set("|-: ")]
            cab, *resto = filas
            salida.append('<table class="mini"><thead><tr>' + "".join(f"<th>{md(c)}</th>" for c in cab) + "</tr></thead><tbody>"
                          + "".join("<tr>" + "".join(f"<td>{md(c)}</td>" for c in f) + "</tr>" for f in resto) + "</tbody></table>")
            continue
        if all(l.startswith("- ") for l in lineas):
            salida.append("<ul>" + "".join(f"<li>{md(l[2:])}</li>" for l in lineas) + "</ul>")
        elif all(re.match(r"\d+\. ", l) for l in lineas):
            salida.append("<ol>" + "".join(f"<li>{md(l.split('. ', 1)[1])}</li>" for l in lineas) + "</ol>")
        else:
            salida.append(f"<p>{md(' '.join(lineas))}</p>")
    return "".join(salida)


# ───────────────────────── código: líneas visibles, colores y alcance de cada nota ─────────────────────────

def sin_comentarios(lineas):
    """Líneas a ocultar (docstrings y comentarios sueltos) y líneas limpias, para ver solo código."""
    import ast, io, tokenize
    texto = textwrap.dedent("\n".join(lineas))
    ocultas, limpias = set(), list(lineas)
    try:
        for nodo in ast.walk(ast.parse(texto)):
            cuerpo = getattr(nodo, "body", None)
            if isinstance(cuerpo, list) and cuerpo and isinstance(cuerpo[0], ast.Expr) \
                    and isinstance(getattr(cuerpo[0], "value", None), ast.Constant) and isinstance(cuerpo[0].value.value, str):
                ocultas.update(range(cuerpo[0].lineno - 1, cuerpo[0].end_lineno))
        for t in tokenize.generate_tokens(io.StringIO(texto).readline):
            if t.type == tokenize.COMMENT:
                i = t.start[0] - 1
                col = len(limpias[i]) - len(texto.split("\n")[i]) + t.start[1]
                antes = limpias[i][:col].rstrip()
                if antes.strip():
                    limpias[i] = antes
                else:
                    ocultas.add(i)
    except (SyntaxError, tokenize.TokenError):
        return _sin_comentarios_simple(lineas)
    for i in sorted(ocultas):
        if i + 1 < len(lineas) and not limpias[i + 1].strip():
            ocultas.add(i + 1)
    return ocultas, limpias


def _sin_comentarios_simple(lineas):
    """Respaldo para fragmentos que no son Python completo (por ejemplo, métodos de una clase y una función suelta)."""
    ocultas, limpias, dentro = set(), list(lineas), False
    for i, l in enumerate(lineas):
        t = l.strip()
        if dentro:
            ocultas.add(i)
            dentro = '"""' not in t
        elif t.startswith('"""'):
            ocultas.add(i)
            dentro = not (len(t) > 3 and t.endswith('"""'))
        elif t.startswith("#"):
            ocultas.add(i)
        else:
            m = re.match(r"^(.*?\S)\s{2,}#\s.*$", l)
            if m and m.group(1).count('"') % 2 == 0 and m.group(1).count("'") % 2 == 0:
                limpias[i] = m.group(1)
    for i in sorted(ocultas):
        if i + 1 < len(lineas) and not limpias[i + 1].strip():
            ocultas.add(i + 1)
    return ocultas, limpias


PALABRAS = ("def class return if elif else for in not is None True False raise from import with try except finally lambda "
            "yield pass and or while as assert del global nonlocal async await").split()
TOKEN = re.compile(r"""(?P<s>f?"[^"\n]*"|f?'[^'\n]*')|(?P<d>@\w+)|(?P<k>\b(?:%s)\b)|(?P<n>\b\d+\b)""" % "|".join(PALABRAS))


def colorear(linea):
    salida, pos = [], 0
    for m in TOKEN.finditer(linea):
        salida.append(esc(linea[pos:m.start()]))
        clase = m.lastgroup
        salida.append(f'<span class="t{clase}">{esc(m.group())}</span>')
        pos = m.end()
    salida.append(esc(linea[pos:]))
    return "".join(salida) or " "


def alcance(limpias, ocultas, i):
    """Última línea de la construcción que empieza en la línea i (paréntesis o corchetes sin cerrar)."""
    abiertos, j = 0, i
    while j < len(limpias):
        if j not in ocultas:
            s = re.sub(r'f?"[^"\n]*"|f?\'[^\'\n]*\'', "", limpias[j]).split("#")[0]
            abiertos += sum(s.count(c) for c in "([{") - sum(s.count(c) for c in ")]}")
            if abiertos <= 0 and not limpias[j].rstrip().endswith("\\"):
                break
        j += 1
    return min(j, len(limpias) - 1)


def diapositiva_codigo(p):
    ini_l, fin_l = p["lineas"]
    todas = (RAIZ / p["archivo"]).read_text(encoding="utf-8").split("\n")
    lineas = textwrap.dedent("\n".join(todas[ini_l - 1:fin_l])).split("\n")
    ocultas, limpias = sin_comentarios(lineas)
    pos, ubic = 0, []
    for aguja, *_ in p["notas"]:
        i = next((x for x in range(pos, len(lineas)) if aguja in lineas[x] and x not in ocultas), None)
        if i is None:
            i = next((x for x in range(len(lineas)) if aguja in lineas[x] and x not in ocultas), None)
        if i is None:
            raise SystemExit(f"Nota sin línea: {aguja!r} en {p['archivo']}::{p['simbolo']}")
        ubic.append(i)
        pos = i
    filas = "".join(
        f'<div class="l"{" hidden" if i in ocultas else ""}><span class="n">{ini_l + i}</span>'
        f'<span class="c">{colorear(limpias[i])}</span></div>' for i in range(len(lineas)))
    notas = []
    for (aguja, titulo, que, para, _), i in zip(p["notas"], ubic):
        notas.append(dict(a=i, b=alcance(limpias, ocultas, i), t=esc(titulo), q=bloques(que), p=bloques(para) if para else ""))
    etiquetas, para_que, clase = bm.PASOS[p["simbolo"]]
    return dict(filas=filas, notas=notas, tags=etiquetas, para=md(para_que), por_que=md(p["por_que"]), clase=clase,
                rango=(ini_l, fin_l))


# ───────────────────────── fichas de archivo ─────────────────────────

def titulo_paso(p):
    titulo = p["titulo"].split(" · ", 1)[1]
    titulo = titulo.split(": ", 1)[1] if ": " in titulo else titulo
    if not re.search(r"[_.()]", titulo.split()[0]):
        titulo = titulo[:1].upper() + titulo[1:]
    return titulo


def ficha(archivo, medidas, pasos=()):
    f = bm.FICHAS[archivo]
    modulo = archivo[:-3]
    usa = sorted(medidas["deps"][modulo])
    usan = sorted(m for m, ds in medidas["deps"].items() if modulo in ds)
    solo_tipos = {d for (m, d) in medidas["solo_tipos"] if m == modulo}
    usan_tipos = {m for (m, d) in medidas["solo_tipos"] if d == modulo}

    def chips(lista, tipos=()):
        if not lista and not tipos:
            return '<span class="muted">—</span>'
        return "".join(f'<span class="mod">{esc(x)}</span>' for x in lista) + "".join(
            f'<span class="mod tipo" title="solo para anotar tipos">{esc(x)}*</span>' for x in sorted(tipos))
    contiene = "".join(f'<li><code>{esc(n)}</code><span>{esc(d)}</span></li>' for n, d in f["contiene"])
    nota_tipos = ('<p class="muted chica">* solo para anotar tipos (<code>TYPE_CHECKING</code>): no es una importación real.</p>'
                  if solo_tipos or usan_tipos else "")
    sigue = ""
    if len(pasos) > 1:   # qué se va a detallar en las diapositivas que siguen
        sigue = ('<div class="sigue"><span class="eti">A continuación se detalla</span>'
                 + "".join(f'<span class="paso"><b>{i + 1}</b>{esc(t)}</span>' for i, t in enumerate(pasos)) + '</div>')
    resp = f["resp"].replace("{usan}", str(len(usan))).replace("{total}", str(len(medidas["modulos"])))
    cuerpo = f"""
<p class="lead corto">{esc(resp)}</p>{sigue}
<div class="grid">
 <div class="card"><h3>Qué contiene</h3><ul class="cont">{contiene}</ul></div>
 <div class="card"><h3>Se comunica con</h3>
  <p class="rel"><b>Usa</b>{chips(usa, solo_tipos)}</p>
  <p class="rel"><b>Lo usan</b>{chips(usan, usan_tipos)}</p>{nota_tipos}
  <h3>Conceptos POO</h3><div>{bg.tags(f['poo'])}</div>
  <div class="callout">{esc(f['para'])}</div></div>
</div>"""
    return dict(k="ficha", archivo=archivo, titulo=f["titulo"], html=cuerpo, clase=f["clase"])


# ───────────────────────── armado ─────────────────────────

def construir():
    generales, medidas = bg.slides_generales()
    slides, grupos = [], []

    def agregar(s, g):
        s["g"] = g
        slides.append(s)
        return len(slides) - 1

    # grupo 0: recorrido general
    idx = []
    for s in generales:
        s["k"] = "general"
        s["archivo"] = None
        idx.append(agregar(s, 0))
    grupos.append(dict(titulo="Recorrido general", desc="Las seis preguntas: qué problema resuelve, cómo está organizado, qué clases usa, "
                       "cómo se comunican, cómo se procesan los datos y qué conceptos de POO aplica.",
                       archivos=[], slides=idx, entradas={}))

    # grupos 1..7: archivos
    for g, gr in enumerate(ga.GRUPOS):
        idx, entradas = [], {}
        for archivo in gr["archivos"]:
            pasos = [p for p in ga.P if p["grupo"] == g and p["archivo"] == "dominio/" + archivo]
            fi = ficha(archivo, medidas, [titulo_paso(p) for p in pasos])
            fi["eyebrow"] = f"{g + 1:02d} · dominio/{archivo}"
            pos = agregar(fi, g + 1)
            idx.append(pos)
            entradas[archivo] = pos
            for p in pasos:
                d = diapositiva_codigo(p)
                s = dict(k="codigo", archivo=archivo, titulo=titulo_paso(p), clase=d["clase"], d=d,
                         eyebrow=f"{g + 1:02d} · dominio/{archivo} · líneas {d['rango'][0]}–{d['rango'][1]}")
                idx.append(agregar(s, g + 1))
        grupos.append(dict(titulo=gr["titulo"], desc=gr["desc"], archivos=gr["archivos"], slides=idx, entradas=entradas))
    return slides, grupos


def ver(clase):
    return f'<button class="ver" data-c="{esc(clase)}" hidden>◇ Ver en el diagrama</button>' if clase else ""


ICONOS = {   # íconos de línea, 24×24, dibujados con el color del texto
    1: '<path d="M12 3 3 8l9 5 9-5-9-5Z"/><path d="m3 13 9 5 9-5"/>',
    2: '<path d="M12 4 2.5 20h19L12 4Z"/><path d="M12 10v4"/><path d="M12 17h.01"/>',
    3: '<path d="M6 16v-5a6 6 0 0 1 12 0v5l1.5 2h-15L6 16Z"/><path d="M10 20a2 2 0 0 0 4 0"/>',
    4: '<path d="M3 6h11v10H3z"/><path d="M14 10h4l3 3v3h-7"/><circle cx="7" cy="17.5" r="1.8"/><circle cx="17" cy="17.5" r="1.8"/>',
    5: '<circle cx="9" cy="8" r="3"/><path d="M3.5 19a5.5 5.5 0 0 1 11 0"/><circle cx="17" cy="9" r="2.4"/><path d="M15.5 14.2A4.5 4.5 0 0 1 21 19"/>',
    6: '<path d="M5 21V4"/><path d="M5 4h11l-2 4 2 4H5"/>',
    7: '<path d="M7 18v-5a5 5 0 0 1 10 0v5"/><path d="M5 18h14v3H5z"/><path d="M12 3v2M4.5 6l1.4 1.4M19.5 6l-1.4 1.4"/>',
}
# columnas del menú: los grupos en el orden en que se construyó el código, de izquierda a derecha
COLUMNAS = [("Fundamentos", [1, 2]), ("Avisos y recursos", [3, 4, 5]), ("Coordinación", [6, 7])]

FUENTES_MENU = [(400, "montserrat-latin-400-normal"), (500, "montserrat-latin-500-normal"),
                (600, "montserrat-latin-600-normal"), (700, "montserrat-latin-700-normal")]


def fuentes_menu():
    """Montserrat incrustada en el HTML: el menú se ve igual sin internet."""
    import base64
    return "".join(
        f'@font-face{{font-family:"Montserrat";font-weight:{peso};font-style:normal;font-display:swap;'
        f'src:url(data:font/woff2;base64,{base64.b64encode((AQUI / "fuentes" / (nombre + ".woff2")).read_bytes()).decode()}) format("woff2")}}\n'
        for peso, nombre in FUENTES_MENU)


def menu_html(slides, grupos):
    """La vista de inicio: tres columnas de grupos y, debajo, el recorrido general y el proceso."""
    def item(g):
        gr = grupos[g]
        archivos = "".join(f'<button class="fch" data-g="{g}" data-f="{esc(a)}">{esc(a)}</button>' for a in gr["archivos"])
        return (f'<div class="gr" data-g="{g}" tabindex="0" role="button" title="{len(gr["slides"])} diapositivas">'
                f'<svg viewBox="0 0 24 24" aria-hidden="true">{ICONOS[g]}</svg>'
                f'<div><b><span class="nro">{g}</span>{esc(gr["titulo"])}</b>'
                f'<span class="desc">{esc(gr["desc"])}</span><span class="arch">{archivos}</span></div></div>')
    columnas = "".join(f'<div class="col"><h3>{esc(t)}</h3>{"".join(item(g) for g in gs)}</div>' for t, gs in COLUMNAS)
    extra = ('<p class="extra"><button class="preg" data-s="{}">Recorrido general</button>'
             '<button class="preg" id="proceso">Cómo se llegó a este diseño</button></p>').format(grupos[0]["slides"][0])
    return f'<div class="mega">{columnas}</div>{extra}'


def pagina(slides, grupos):
    secciones, meta = [], []
    for n, s in enumerate(slides):
        grande = " grande" if s.get("grande") else ""
        if s["k"] == "codigo":
            d = s["d"]
            secciones.append(
                f'<section class="slide cod" data-i="{n}" hidden><div class="eyebrow">{esc(s["eyebrow"])}</div><h2>{esc(s["titulo"])}</h2>'
                f'<div class="dos"><div class="codigo"><div class="filas">{d["filas"]}</div></div>'
                f'<aside class="nota card" aria-live="polite"><div class="zz"></div></aside></div></section>')
            meta.append(dict(g=s["g"], k="codigo", a=s["archivo"], c=s["clase"], t=s["titulo"], n=len(d["notas"]),
                             notas=d["notas"], tags=d["tags"], para=d["para"], por_que=d["por_que"]))
        else:
            secciones.append(
                f'<section class="slide gen{grande}" data-i="{n}" hidden><div class="eyebrow"><span>{esc(s["eyebrow"])}</span>{ver(s.get("clase"))}</div>'
                f'<h{1 if grande else 2}>{esc(s["titulo"])}</h{1 if grande else 2}>{s["html"]}</section>')
            meta.append(dict(g=s["g"], k=s["k"], a=s.get("archivo"), c=s.get("clase"), t=s["titulo"], n=0))
    total = len(slides)
    tarjetas = []
    for g, gr in enumerate(grupos):
        n = len(gr["slides"])
        if g == 0:
            tarjetas.append(
                f'<div class="gr gen" data-g="0" tabindex="0" role="button"><span class="num">★</span><div><b>{esc(gr["titulo"])}</b>'
                f'<span class="desc">{esc(gr["desc"])}</span></div><small>{n} diapositivas</small></div>')
            continue
        chips = "".join(f'<button class="fch" data-g="{g}" data-f="{esc(a)}">{esc(a)}</button>' for a in gr["archivos"])
        tarjetas.append(
            f'<div class="gr" data-g="{g}" tabindex="0" role="button"><span class="num">{g}</span><div><b>{esc(gr["titulo"])}</b>'
            f'<span class="arch">{chips}</span><span class="desc">{esc(gr["desc"])}</span></div><small>{n} diapositivas</small></div>')
    grupos_js = [dict(titulo=gr["titulo"], archivos=gr["archivos"], slides=gr["slides"], entradas=gr["entradas"]) for gr in grupos]
    pagina_html = PLANTILLA
    for clave, valor in (("%%SECCIONES%%", "\n".join(secciones)), ("%%MENU%%", menu_html(slides, grupos)),
                         ("%%FUENTES_MENU%%", fuentes_menu()), ("%%META%%", json.dumps(meta, ensure_ascii=False)),
                         ("%%GRUPOS%%", json.dumps(grupos_js, ensure_ascii=False)), ("%%TOTAL%%", str(total))):
        pagina_html = pagina_html.replace(clave, valor)
    return pagina_html


PLANTILLA = r"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<script>if(parent!==window)document.documentElement.classList.add('emb')</script>
<title>CRCE · Backend</title>
<style>
:root{--bg:#0b1020;--panel:#121a2d;--panel2:#18243b;--text:#eef3ff;--muted:#9eacc6;--accent:#71d5c3;--line:#2a3854;--code:#080d18;--gold:#f3c969;--blue:#7cb7ff;--lila:#b9a7ff;--soft:#c5d0e4}
*{box-sizing:border-box}html,body{margin:0;width:100%;height:100%;background:var(--bg);color:var(--text);font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
.deck{height:100%;display:flex;flex-direction:column}
.top{height:52px;flex:none;padding:0 4vw;display:flex;align-items:center;justify-content:space-between;gap:16px;border-bottom:1px solid var(--line);color:var(--muted);font-size:13px;letter-spacing:.04em;white-space:nowrap}
html.emb .top{padding-left:64px}
.top span{overflow:hidden;text-overflow:ellipsis}
.top select{background:var(--panel2);color:var(--text);border:1px solid var(--line);border-radius:9px;padding:6px 10px;font:inherit;font-size:13px;max-width:min(46vw,520px)}
main{flex:1;min-height:0;display:flex;justify-content:center;padding:2.2vh 4vw;overflow:hidden;position:relative}
.slide{display:none;width:min(1360px,100%);min-height:0;max-height:100%}
.slide.active{display:flex;flex-direction:column;justify-content:center;animation:in .22s ease}
.slide.cod.active{justify-content:flex-start}
@keyframes in{from{opacity:.4;transform:translateY(8px)}to{opacity:1;transform:none}}
@media (prefers-reduced-motion:reduce){.slide.active{animation:none}}
.eyebrow{color:var(--accent);font-size:13px;font-weight:700;letter-spacing:.15em;text-transform:uppercase;margin-bottom:10px;display:flex;justify-content:space-between;align-items:center;gap:12px}
h1{font-size:clamp(32px,4.6vw,62px);line-height:1.04;letter-spacing:-.04em;margin:0 0 16px}
h2{font-size:clamp(24px,3vw,42px);line-height:1.1;letter-spacing:-.035em;margin:0 0 clamp(10px,2vh,20px)}
.lead{font-size:clamp(16px,1.7vw,21px);line-height:1.5;color:var(--soft);max-width:900px;margin:0 0 6px}
.lead.corto{max-width:1000px;font-size:clamp(15px,1.45vw,19px);margin-bottom:clamp(8px,1.6vh,16px)}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:clamp(12px,1.6vw,22px);align-items:start}
.grid3,.tres{display:grid;grid-template-columns:repeat(3,1fr);gap:clamp(12px,1.4vw,20px);align-items:stretch}
.card{background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:clamp(14px,1.6vw,22px)}
.card h3{margin:0 0 10px;font-size:clamp(15px,1.3vw,18px)}
.card h3:not(:first-child){margin-top:14px}
.muted{color:var(--muted)}.chica{font-size:12.5px;margin:8px 0 0}
.explain{font-size:clamp(14.5px,1.3vw,18px);line-height:1.55;color:var(--soft);margin:0 0 8px}.explain strong{color:var(--text)}
ul{margin:6px 0 0;padding-left:20px;color:var(--soft);line-height:1.55;font-size:clamp(14.5px,1.3vw,18px)}li{margin:4px 0}
code{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;color:#bce9df;font-size:.93em}
.tag{display:inline-block;color:var(--accent);border:1px solid #32665e;border-radius:99px;padding:4px 10px;font-size:12px;font-weight:700;margin:0 6px 6px 0}
.callout{border-left:3px solid var(--accent);padding:10px 14px;background:#10242a;border-radius:0 10px 10px 0;color:#cdebe5;margin-top:14px;font-size:clamp(14.5px,1.3vw,18px);line-height:1.5}
.flow{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin:18px 0 6px}.node{background:var(--panel2);border:1px solid var(--line);border-radius:12px;padding:13px 18px;font-weight:650;font-size:clamp(15px,1.4vw,19px)}.arrow{color:var(--accent);font-size:20px}
pre.mini{margin:6px 0 0;background:var(--code);border:1px solid #26334b;border-radius:10px;padding:12px 14px;overflow:auto;color:#e6edf8;font:clamp(11.5px,1vw,13.5px)/1.55 ui-monospace,SFMono-Regular,Menlo,monospace;white-space:pre}
/* piezas */
.pieza h3{margin-bottom:2px}.pieza h3 code{font-size:1.15em;color:var(--accent)}.rol{display:block;font-size:12px;color:var(--gold);margin:0 0 8px}
.guarda{font-size:13px;color:var(--muted);margin:6px 0 0;line-height:1.45}.guarda b{color:var(--soft)}
/* capas */
.capas{display:flex;flex-direction:column;gap:clamp(6px,1.2vh,12px)}
.capa{display:grid;grid-template-columns:minmax(150px,250px) 1fr;gap:16px;align-items:center;background:var(--panel);border:1px solid var(--line);border-left:4px solid var(--accent);border-radius:14px;padding:clamp(8px,1.4vh,14px) 18px}
.capa.c1{border-left-color:var(--blue)}.capa.c2{border-left-color:var(--gold)}.capa.c3{border-left-color:var(--lila)}
.cn b{display:block;font-size:clamp(15px,1.4vw,18px)}.cn small{color:var(--muted);font-size:12.5px}
.mod{display:inline-block;margin:3px 8px 3px 0;padding:6px 12px;border-radius:9px;background:var(--panel2);border:1px solid var(--line);font:600 clamp(12.5px,1.1vw,14.5px) ui-monospace,Menlo,monospace;color:#bce9df}
.mod.tipo{border-style:dashed;color:var(--muted)}
/* mapa */
.mapa{display:grid;grid-template-columns:1fr auto 1fr auto 1fr auto 1fr auto 1fr;align-items:center;row-gap:8px;margin:6px 0 4px}
.nodo{background:var(--panel2);border:1px solid var(--line);border-radius:14px;padding:clamp(14px,3vh,30px) 8px;text-align:center}
.nodo b{display:block;font-size:clamp(15px,1.6vw,22px)}.nodo small{display:block;color:var(--muted);font-size:clamp(11.5px,.95vw,13px);margin-top:3px}
.nodo.chico{padding:8px 6px;border-style:dashed}.nodo.chico b{font-size:clamp(13px,1.15vw,15px)}
.lk{display:flex;flex-direction:column;align-items:center;color:var(--accent);font-size:clamp(11.5px,1vw,13.5px);padding:0 8px;text-align:center;line-height:1.2}.lk i{font-style:normal;font-size:20px}
.abajo{grid-row:2;display:flex;flex-direction:column;align-items:center;gap:2px;color:var(--accent);font-size:clamp(11.5px,1vw,13.5px);margin-top:10px;text-align:center}.abajo i{font-style:normal;font-size:18px;line-height:1}
.a3{grid-column:3}.a5{grid-column:5}.a7{grid-column:7}
/* cadena de mensajes */
.seq{display:flex;flex-direction:column;gap:2px}
.q{display:flex;align-items:center;gap:10px;padding:clamp(2px,.5vh,5px) 0 clamp(2px,.5vh,5px) calc(var(--d)*clamp(14px,1.8vw,26px));font-size:clamp(12px,1.2vw,16.5px);white-space:nowrap;min-width:0}
.q .a{flex:none;width:clamp(78px,7.5vw,100px);text-align:center;border-radius:7px;padding:2px 0;font-weight:700;font-size:.86em;color:#0b1020}
.a.op{background:#9eacc6}.a.em{background:var(--accent)}.a.mi{background:var(--gold)}.a.un{background:var(--lila)}.a.ve{background:#8fe3a0}
.q code{color:#e6edf8;overflow:hidden;text-overflow:ellipsis}.q em{color:var(--muted);font-style:normal;overflow:hidden;text-overflow:ellipsis}
.q em::before{content:"· "}
/* camino de un dato */
.pipe{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin:0 0 clamp(10px,2vh,18px)}
.et{display:flex;gap:8px;align-items:center;background:var(--panel2);border:1px solid var(--line);border-radius:12px;padding:8px 14px;font-weight:650;font-size:clamp(13px,1.2vw,16px)}
.et b{display:inline-grid;place-items:center;width:22px;height:22px;border-radius:50%;background:var(--accent);color:#0b1020;font-size:12px}
.codigo2{display:flex;flex-direction:column;gap:4px}.cl{display:flex;gap:10px;align-items:baseline;padding:6px 10px;border-radius:8px;border-left:3px solid var(--line);background:var(--code)}
.cl b{flex:none;display:inline-grid;place-items:center;width:20px;height:20px;border-radius:50%;font-size:11px;color:#0b1020;background:var(--muted)}
.cl code{color:#e6edf8;font-size:clamp(11px,1vw,13.5px);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.cl.e2{border-left-color:var(--accent)}.cl.e2 b{background:var(--accent)}.cl.e3{border-left-color:var(--gold)}.cl.e3 b{background:var(--gold)}
.cl.e4{border-left-color:var(--lila)}.cl.e4 b{background:var(--lila)}.cl.e5{border-left-color:var(--blue)}.cl.e5 b{background:var(--blue)}
.etapas{list-style:none;padding:0}.etapas li{margin:0 0 9px;font-size:clamp(13px,1.15vw,15.5px);line-height:1.45}.etapas b{color:var(--text)}
/* ejemplo real, etapa por etapa */
.ej{display:grid;grid-template-columns:1.35fr 1fr;gap:clamp(12px,1.4vw,20px);align-items:start;margin-bottom:clamp(8px,1.4vh,14px)}
.ets{display:flex;flex-direction:column;gap:clamp(5px,.9vh,8px)}
.ep{--c:var(--muted);display:grid;grid-template-columns:22px 1fr;gap:0 12px;align-items:start;background:var(--panel);border:1px solid var(--line);border-left:3px solid var(--c);border-radius:12px;padding:clamp(6px,1vh,10px) 14px}
.ep>b{display:inline-grid;place-items:center;width:22px;height:22px;border-radius:50%;background:var(--c);color:#0b1020;font-size:12px;margin-top:1px}
.ep p{margin:0;font-size:clamp(13.5px,1.2vw,16.5px);line-height:1.45;color:var(--soft)}.ep p strong{color:var(--text)}.ep .t{color:var(--c);font-weight:700}
.ep.e2{--c:var(--accent)}.ep.e3{--c:var(--gold)}.ep.e4{--c:var(--lila)}.ep.e5{--c:var(--blue)}
.ep pre.mini{margin:6px 0 0;font-size:clamp(11px,1vw,13px);padding:8px 12px}
.card.err{border-color:#6b3340;background:#1a1322}.card.err h3{color:#ff9aa8}
.pr{align-items:stretch}
.card.ok{border-color:#2f6b57;background:#0f221f;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;gap:6px}
.card.ok h3{margin:0;color:#8fe3a0;font-size:clamp(18px,1.8vw,24px)}.card.ok .explain{margin:0;font-size:clamp(15px,1.4vw,19px)}
.gran{display:grid;place-items:center;width:clamp(56px,6vw,84px);height:clamp(56px,6vw,84px);border-radius:50%;background:#8fe3a0;color:#0b1020;font-size:clamp(30px,3.4vw,48px);font-weight:800;margin-bottom:6px}
.sigue{display:flex;flex-wrap:wrap;align-items:center;gap:6px 8px;margin:0 0 clamp(8px,1.4vh,14px)}
.sigue .eti{color:var(--muted);font-size:13px;margin-right:4px}
.sigue .paso{display:inline-flex;gap:7px;align-items:center;background:var(--panel2);border:1px solid var(--line);border-radius:99px;padding:3px 12px 3px 4px;font-size:clamp(12px,1.05vw,14px);color:var(--soft)}
.sigue .paso b{display:inline-grid;place-items:center;width:20px;height:20px;border-radius:50%;background:var(--accent);color:#0b1020;font-size:11px}
.banda{display:grid;grid-template-columns:1fr auto;gap:6px 22px;align-items:center}.banda h3{margin:0 0 4px}.banda .explain{margin:0}.banda pre.mini{margin:0}
/* ciclo de vida */
.vida{display:grid;grid-template-columns:clamp(110px,13vw,170px) 1fr;gap:4px 16px;align-items:center;background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:clamp(8px,1.3vh,13px) 18px;margin-bottom:clamp(6px,1.1vh,10px)}
.vn b{display:block;font-size:clamp(15px,1.4vw,18px)}.vn small{color:var(--muted);font-size:12px}
.cad{display:flex;flex-wrap:wrap;gap:6px 8px;align-items:center}
.st{background:var(--panel2);border:1px solid #32665e;color:#bce9df;border-radius:99px;padding:4px 12px;font-weight:650;font-size:clamp(13px,1.2vw,16px)}
.ar{color:var(--gold);font:600 clamp(11.5px,1vw,14px) ui-monospace,Menlo,monospace}.o{color:var(--muted);font-size:13px}
.nota-v{grid-column:2;margin:0;font-size:clamp(12px,1vw,14px);color:var(--muted)}
/* conceptos de POO */
.poo{display:flex;flex-direction:column;gap:clamp(5px,.9vh,9px)}
.poo .fila{display:grid;grid-template-columns:clamp(130px,15vw,200px) 1.3fr 1.4fr;gap:16px;align-items:center;padding:clamp(6px,1.1vh,11px) 16px;background:var(--panel);border:1px solid var(--line);border-radius:12px}
.cp{color:var(--accent);font-weight:750;font-size:clamp(14.5px,1.4vw,19px)}.dn{font-size:clamp(12.5px,1.15vw,15.5px);color:var(--soft);line-height:1.4}.pq{font-size:clamp(13px,1.2vw,16.5px);color:#e4ecff;line-height:1.4}
/* pruebas */
.pruebas .fila{display:grid;grid-template-columns:minmax(150px,230px) 1fr 36px;gap:10px;padding:6px 0;border-bottom:1px solid var(--line);font-size:clamp(12.5px,1.15vw,15px);align-items:baseline;color:var(--soft)}
.pruebas .fila:last-child{border-bottom:0}.pruebas b{text-align:right;color:var(--accent)}
/* ficha */
.cont{list-style:none;padding:0;margin:0}.cont li{display:grid;grid-template-columns:minmax(0,1fr);gap:1px;padding:6px 0;border-bottom:1px solid var(--line);margin:0}.cont li:last-child{border-bottom:0}
.cont code{color:var(--accent);font-weight:600}.cont span{color:var(--soft);font-size:clamp(12.5px,1.1vw,14.5px)}
.rel{margin:0 0 8px;display:flex;flex-wrap:wrap;align-items:center;gap:2px 0}.rel b{width:74px;color:var(--muted);font-size:12.5px;font-weight:600}
/* código */
.dos{display:grid;grid-template-columns:minmax(0,1.15fr) minmax(0,1fr);gap:clamp(12px,1.6vw,22px);flex:1;min-height:0;align-items:start;grid-template-rows:minmax(0,1fr)}
.codigo{background:var(--code);border:1px solid #26334b;border-radius:12px;padding:12px 6px 12px 4px;overflow:auto;max-height:100%;font:14px/1.6 ui-monospace,SFMono-Regular,Menlo,monospace;min-width:0}
.l{display:flex;white-space:pre;padding-right:12px;overflow:hidden}.l[hidden]{display:none}
.n{flex:none;width:3.4em;text-align:right;color:#475674;padding-right:1.2em;user-select:none}
.c{flex:1;color:#e6edf8}
.tk{color:var(--blue)}.ts{color:var(--gold)}.td{color:var(--lila)}.tn{color:#f2a07b}
.l.act{background:rgba(113,213,195,.14);box-shadow:inset 3px 0 0 var(--accent)}
.codigo.foco .l:not(.act){opacity:.5}
.dos.apilado{grid-template-columns:minmax(0,1fr);grid-template-rows:auto minmax(0,1fr)}
.nota{max-height:100%;overflow:hidden;min-width:0}.nota .zz{width:100%}
.apilado .nota{padding:12px 16px}.apilado .nota .pista{display:none}
.apilado .nota h3{font-size:clamp(15px,1.4vw,19px);margin:0 0 5px}.apilado .nota .q2{font-size:clamp(13.5px,1.2vw,16px);line-height:1.45;margin-bottom:5px}
.apilado .nota h4{margin:6px 0 3px}.apilado .nota .tags{margin-top:4px}.apilado .nota .callout{margin-top:0}
.apilado .nota .zz{columns:2 320px;column-gap:28px}.apilado .nota .zz>*{break-inside:avoid}.apilado .nota .zz>.rot{column-span:all}.apilado .nota .zz>h3:first-of-type{margin-top:0}
.rot{display:flex;justify-content:space-between;align-items:center;color:var(--muted);font-size:12px;letter-spacing:.05em;margin-bottom:8px}
.dots span{display:inline-block;width:7px;height:7px;border-radius:50%;background:var(--line);margin-left:4px}.dots span.on{background:var(--accent)}
.nota h3{font-size:clamp(17px,1.6vw,22px);margin:0 0 8px;letter-spacing:-.01em}
.nota .q2{font-size:clamp(14.5px,1.3vw,17.5px);line-height:1.55;color:var(--soft);margin:0 0 8px}.nota .q2 strong{color:var(--text)}
.nota .q2 p{margin:0 0 .55em}.nota .q2 p:last-child{margin-bottom:0}
.nota .q2 pre.mini{font:600 .78em/1.45 ui-monospace,SFMono-Regular,Menlo,monospace;color:var(--accent);background:rgba(0,0,0,.25);border:1px solid var(--line);border-radius:8px;padding:.6em .8em;margin:.2em 0 .7em;white-space:pre;overflow-x:auto}
.nota .q2 table.mini{border-collapse:collapse;width:100%;font-size:.8em;margin:.2em 0 .6em}.nota .q2 table.mini th,.nota .q2 table.mini td{border:1px solid var(--line);padding:.3em .45em;text-align:left;vertical-align:top}.nota .q2 table.mini th{color:var(--gold);font-weight:700;background:rgba(255,255,255,.03)}
.nota .q2 ul,.nota .q2 ol{margin:.2em 0 .55em;padding-left:1.25em}.nota .q2 li{margin:.25em 0}.nota .q2 li::marker{color:var(--accent);font-weight:700}
.nota h4{margin:10px 0 4px;font-size:13px;color:var(--gold);font-weight:700}
.nota .tags{margin-top:8px}.nota .pista{color:var(--muted);font-size:12.5px;margin:10px 0 0}
.ver{background:none;border:1px solid var(--line);color:var(--accent);border-radius:8px;padding:3px 9px;font-size:11.5px;font-weight:650;cursor:pointer;letter-spacing:0;text-transform:none}.ver[hidden]{display:none}
.ver:hover{border-color:var(--accent)}
/* pie */
.bottom{height:64px;flex:none;border-top:1px solid var(--line);display:flex;align-items:center;justify-content:space-between;padding:0 4vw;color:var(--muted);font-size:13px;gap:12px}
.controls{display:flex;gap:8px;align-items:center}
button{background:var(--panel2);border:1px solid var(--line);color:var(--text);padding:9px 14px;border-radius:9px;cursor:pointer;font-weight:650;font:inherit;font-size:14px;font-weight:650}
button:hover{border-color:var(--accent)}button:disabled{opacity:.4;cursor:default}button:focus-visible,.gr:focus-visible{outline:3px solid var(--gold);outline-offset:2px}
.count{min-width:70px;text-align:center}
/* lista */
#lista{display:none;width:min(1360px,100%);overflow:auto;align-self:stretch;padding:0 4px}
#lista.on{display:block}
#lista h1{font-size:clamp(28px,3.6vw,48px);margin-bottom:8px}#lista .lead{margin-bottom:clamp(10px,2vh,18px)}
.gr{display:grid;grid-template-columns:auto 1fr;gap:4px 14px;align-items:start;background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:clamp(12px,1.8vh,18px) 18px;cursor:pointer;position:relative;min-width:0}
.gr:hover{border-color:var(--accent)}.gr.visto{border-color:#32665e}.gr.visto::after{content:"visto";position:absolute;right:14px;top:10px;color:var(--accent);font-size:11px;font-weight:700}
.gr .num{display:inline-grid;place-items:center;width:32px;height:32px;border-radius:50%;background:var(--accent);color:#0b1020;font-weight:800;font-size:15px}
.gr b{display:block;font-size:clamp(15px,1.35vw,18px);margin-bottom:4px}
.gr .arch{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:4px}
.fch{padding:3px 9px;border-radius:7px;font:600 12px ui-monospace,Menlo,monospace;color:#bce9df;background:var(--panel2)}
.gr .desc{display:block;color:var(--muted);font-size:clamp(12.5px,1.05vw,14px);line-height:1.4}
.gr small{grid-column:2;color:var(--muted);font-size:11.5px}
.gr.gen{margin-bottom:clamp(10px,1.6vh,16px);border-color:#32665e;background:#10242a;grid-template-columns:auto 1fr auto;align-items:center}
.gr.gen .num{background:var(--gold)}.gr.gen small{grid-column:3;font-size:12px}
.grs{display:grid;grid-template-columns:repeat(auto-fit,minmax(290px,1fr));gap:clamp(10px,1.4vw,16px)}
.aparte{margin:14px 0 4px;color:var(--muted);font-size:13px}.aparte button{padding:5px 11px;font-size:12.5px;color:var(--soft)}
@media (max-width:980px){.grid,.tres,.grid3,.ej,.banda{grid-template-columns:1fr}}
@media (max-width:640px){.top select{display:none}}
@media (max-height:900px){#lista .lead{display:none}}
@media (max-height:720px){h2{font-size:clamp(22px,2.6vw,30px);margin-bottom:8px}.eyebrow{margin-bottom:4px;font-size:12px}.cont li{padding:4px 0}.sigue{margin-bottom:6px}.sigue .paso{padding:2px 10px 2px 3px}.lead.corto{margin-bottom:6px}}
@media (max-height:720px){.gr .desc{display:none}.gr{padding:10px 16px}}
%%FUENTES_MENU%%
/* ── vista de inicio (menú): mismos colores que las diapositivas, Montserrat, columnas por tema ── */
body.modo-lista .top,body.modo-lista .bottom{font-family:"Montserrat",sans-serif;letter-spacing:0}
body.modo-lista .top span:first-child{color:var(--text);font-weight:600;letter-spacing:.12em}
#lista{font-family:"Montserrat",system-ui,sans-serif;color:var(--text);max-width:1320px}
#lista h1{font:600 clamp(26px,2.4vw,34px)/1.15 "Montserrat",sans-serif;letter-spacing:-.015em;color:var(--text);margin:clamp(6px,1.5vh,18px) 0 6px}
#lista .lead{font:400 clamp(14px,1.05vw,16px)/1.5 "Montserrat",sans-serif;color:var(--muted);max-width:760px;margin:0 0 clamp(14px,2.4vh,26px)}
.mega{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));border:1px solid var(--line);border-radius:16px;background:var(--panel);overflow:hidden}
.mega .col{padding:clamp(18px,3.2vh,34px) clamp(12px,1.6vw,24px) clamp(14px,2.4vh,26px)}
.mega .col+.col{border-left:1px solid var(--line)}
.mega h3{font:600 15px/1.2 "Montserrat",sans-serif;color:var(--accent);margin:0 0 clamp(8px,1.6vh,16px);padding-left:14px}
#lista .gr{display:grid;grid-template-columns:24px minmax(0,1fr);gap:0 12px;align-items:start;background:none;border:0;border-radius:12px;
  padding:clamp(10px,1.6vh,15px) 14px;margin-bottom:clamp(2px,.6vh,8px);cursor:pointer;color:var(--text);box-shadow:none;position:relative}
#lista .gr:hover,#lista .gr:focus-visible{background:var(--panel2);outline:none}
#lista .gr:focus-visible{box-shadow:0 0 0 2px var(--accent)}
#lista .gr svg{width:23px;height:23px;margin-top:1px;fill:none;stroke:var(--text);stroke-width:1.75;stroke-linecap:round;stroke-linejoin:round}
#lista .gr>div{display:block}
#lista .gr b{display:flex;align-items:baseline;gap:7px;font:600 clamp(15.5px,1.25vw,18px)/1.25 "Montserrat",sans-serif;margin:0 0 4px;color:var(--text)}
#lista .gr .nro{color:var(--muted);font-weight:500}
#lista .gr .desc{display:block;font:400 clamp(13px,1vw,15px)/1.45 "Montserrat",sans-serif;color:var(--muted);margin:0}
#lista .gr .arch{display:flex;flex-wrap:wrap;gap:2px 12px;margin-top:6px}
#lista .fch{background:none;border:0;padding:0;font:500 12.5px/1.4 "Montserrat",sans-serif;color:#bce9df;cursor:pointer}
#lista .fch:hover{text-decoration:underline;color:var(--text)}
#lista .gr.visto::after{content:"Visto";position:static;grid-column:2;justify-self:start;margin-top:6px;font:600 11px/1 "Montserrat",sans-serif;color:var(--bg);background:var(--accent);border-radius:99px;padding:4px 8px}
.extra{display:flex;gap:28px;margin:clamp(10px,1.8vh,18px) 0 0}
.preg{background:none;border:0;padding:4px 0;font:500 clamp(14px,1.05vw,15.5px)/1.3 "Montserrat",sans-serif;color:var(--muted);cursor:pointer;border-radius:0}
.preg:hover{color:var(--text);text-decoration:underline;border:0}
.preg:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
@media (max-width:1100px){.mega{grid-template-columns:repeat(2,minmax(0,1fr))}.mega .col+.col{border-left:0}}
@media (max-width:640px){.mega{grid-template-columns:1fr}}
@media (max-height:900px){#lista .gr .arch{display:none}}
@media (max-height:760px){#lista .lead{display:none}#lista .gr .desc{font-size:13px}}
</style></head>
<body>
<div class="deck">
<header class="top"><span>CRCE · CENTRO REGIONAL DE COORDINACIÓN DE EMERGENCIAS</span><select id="salto" aria-label="Ir a una diapositiva" hidden></select><span id="ctx">POO V · BACKEND</span></header>
<main id="main">
<section id="lista" class="on">
 <h1>Elegí qué presentar</h1>
 <p class="lead">Cada grupo explica el código de sus archivos, en el orden en que se construyó.</p>
 %%MENU%%
</section>
%%SECCIONES%%
</main>
<footer class="bottom"><span id="pista">← → o Espacio para avanzar · Esc vuelve a la lista · D abre el diagrama · F pantalla completa</span>
<div class="controls"><button id="lista-b" hidden>Lista</button><button id="prev" disabled>Anterior</button><span class="count" id="count"></span><button id="next" disabled>Siguiente</button></div></footer>
</div>
<script>
const META=%%META%%,GRUPOS=%%GRUPOS%%;
const $=s=>document.querySelector(s),slides=[...document.querySelectorAll('.slide')],emb=parent!==window;
let i=-1,k=0,G=null,gi=-1;const vistos=new Set();
function mostrarLista(){i=-1;k=0;G=null;gi=-1;pintar()}
function entrar(g,desde){gi=g;G=GRUPOS[g].slides;i=desde===undefined?G[0]:desde;k=0;pintar()}
function pintar(){
 const enLista=i<0;$('#lista').classList.toggle('on',enLista);document.body.classList.toggle('modo-lista',enLista);
 slides.forEach((s,x)=>{s.hidden=x!==i;s.classList.toggle('active',x===i)});
 $('#lista-b').hidden=enLista;$('#salto').hidden=enLista||innerWidth<=640;
 $('#prev').disabled=enLista;$('#next').disabled=enLista;
 document.querySelectorAll('.gr').forEach(e=>e.classList.toggle('visto',vistos.has(+e.dataset.g)));
 if(emb)parent.postMessage({tema:enLista?'claro':'oscuro'},'*');
 if(enLista){$('#prev').textContent='Anterior';$('#next').textContent='Siguiente';$('#count').textContent='';$('#ctx').textContent='POO V · BACKEND';$('#pista').textContent='Elegí una tarjeta o un archivo · F pantalla completa';return}
 vistos.add(gi);
 const p=G.indexOf(i),m=META[i];
 $('#ctx').textContent='POO V · BACKEND · '+GRUPOS[gi].titulo;
 $('#count').textContent=(p+1)+' / '+G.length;
 $('#pista').textContent='← → o Espacio para avanzar · Esc vuelve a la lista'+(emb?' · D abre el diagrama':'')+' · F pantalla completa';
 $('#next').textContent=p===G.length-1&&(m.k!=='codigo'||k===m.n)?'Volver a la lista':'Siguiente';
 $('#prev').textContent=p===0&&(m.k!=='codigo'||k===0)?'Volver a la lista':'Anterior';
 const sel=$('#salto');if(sel.dataset.g!==String(gi)){sel.innerHTML='';G.forEach((x,y)=>{const o=document.createElement('option');o.value=x;o.textContent=(y+1)+' · '+(META[x].a&&META[x].k==='ficha'?META[x].a+': ':'')+META[x].t;sel.append(o)});sel.dataset.g=gi}
 sel.value=i;
 if(m.k==='codigo')pintarCodigo();else ajustarSlide();
}
function pintarCodigo(){
 const s=slides[i],m=META[i],cd=s.querySelector('.codigo'),ls=[...cd.querySelectorAll('.l')],z=s.querySelector('.zz');
 ls.forEach(l=>l.classList.remove('act'));cd.classList.toggle('foco',k>0);
 const mk=(t,c,h)=>{const d=document.createElement(t);if(c)d.className=c;if(h!==undefined)d.innerHTML=h;return d};
 z.innerHTML='';
 const dots=mk('span','dots','');for(let x=0;x<m.n;x++)dots.append(mk('span',x<k?'on':'',''));
 const rot=mk('div','rot','');rot.append(mk('span','',k===0?'Resumen':'Nota '+k+' de '+m.n),dots);
 if(m.c&&emb){const b=mk('button','ver','◇ Ver en el diagrama');b.onclick=e=>{e.stopPropagation();verDiagrama()};rot.insertBefore(b,dots)}
 z.append(rot);
 if(k===0){
  z.append(mk('h3','','¿Qué hace?'),mk('p','q2',m.por_que),mk('h4','','Conceptos POO'));
  const t=mk('div','tags','');m.tags.forEach(x=>t.append(mk('span','tag',x)));z.append(t);
  z.append(mk('div','callout','<strong>Para qué:</strong> '+m.para),mk('p','pista','→ para ver el código '+(m.n===1?'explicado':'línea por línea ('+m.n+' notas)')));
 }else{
  const n=m.notas[k-1];
  for(let x=n.a;x<=n.b;x++)if(ls[x])ls[x].classList.add('act');
  z.append(mk('h3','',n.t),mk('div','q2',n.q));
  if(n.p){z.append(mk('h4','','¿Para qué sirve?'),mk('div','q2',n.p))}
  const t=mk('div','tags','');m.tags.forEach(x=>t.append(mk('span','tag',x)));z.append(t);
 }
 ajustarCodigo();
}
function ajustarCodigo(){
 const s=slides[i];if(!s||!s.classList.contains('cod'))return;
 const cd=s.querySelector('.codigo'),dos=s.querySelector('.dos'),nota=s.querySelector('.nota');
 const ls=[...cd.querySelectorAll('.l:not([hidden])')],tot=dos.clientWidth;
 const largo=Math.max(...ls.map(l=>l.querySelector('.c').textContent.length+6));
 const meta=Math.min(15,Math.max(12,innerHeight*.021));
 const cabe=()=>ls.every(l=>l.scrollWidth<=l.clientWidth+1);
 const fit=()=>{let px=meta;cd.style.fontSize=px+'px';while(!cabe()&&px>7){px-=.5;cd.style.fontSize=px+'px'}return px};
 dos.classList.remove('apilado');cd.style.maxHeight='';nota.style.maxHeight='';
 dos.style.gridTemplateColumns=Math.min(tot*.62,Math.max(tot*.48,largo*.602*Math.min(meta,12.5)+40))+'px minmax(0,1fr)';
 let px=fit();
 if(px<11){dos.classList.add('apilado');dos.style.gridTemplateColumns='minmax(0,1fr)';px=fit();
  const z=nota.querySelector('.zz');z.style.zoom=1;nota.style.maxHeight='none';
  const H=dos.clientHeight,gap=parseFloat(getComputedStyle(dos).rowGap)||0,tarjeta=Math.min(z.scrollHeight+parseFloat(getComputedStyle(nota).paddingTop)*2+2,H*.5);
  cd.style.maxHeight=Math.max(H*.3,H-tarjeta-gap)+'px'}
 const act=cd.querySelector('.l.act');if(act)cd.scrollTo({top:Math.max(0,act.offsetTop-cd.clientHeight/2),behavior:'auto'});else cd.scrollTo({top:0});
 const lib=dos.getBoundingClientRect().bottom-nota.getBoundingClientRect().top;nota.style.maxHeight=Math.max(130,lib)+'px';
 ajustarNota();
}
function ajustarNota(){
 const n=slides[i].querySelector('.nota'),z=n&&n.querySelector('.zz');if(!z)return;
 z.style.zoom=1;n.style.overflowY='hidden';let zm=1;
 const pad=parseFloat(getComputedStyle(n).paddingTop)*2,lim=(parseFloat(n.style.maxHeight)||n.clientHeight)-2;
 const ocupa=()=>z.getBoundingClientRect().height+pad;   // alto real, ya con el zoom aplicado
 while(ocupa()>lim&&zm>.7){zm-=.04;z.style.zoom=zm}
 if(ocupa()>lim)n.style.overflowY='auto';
}
function ajustarSlide(){
 const s=slides[i];if(!s)return;s.style.zoom=1;const mn=$('#main'),cs=getComputedStyle(mn);
 const ah=mn.clientHeight-parseFloat(cs.paddingTop)-parseFloat(cs.paddingBottom),aw=mn.clientWidth-parseFloat(cs.paddingLeft)-parseFloat(cs.paddingRight);
 for(let t=0;t<3;t++){const r=s.getBoundingClientRect(),h=s.scrollHeight*(parseFloat(s.style.zoom)||1),w=s.scrollWidth*(parseFloat(s.style.zoom)||1);
  const f=Math.min(1,ah/Math.max(h,1),aw/Math.max(w,1));if(f>=.999)break;s.style.zoom=Math.max(.55,(parseFloat(s.style.zoom)||1)*f*.995)}
}
function verDiagrama(){const c=META[i]&&META[i].c;if(emb)parent.postMessage(c?{modo:'diagrama',clase:c}:{modo:'diagrama'},'*')}
function sig(){
 if(i<0)return;const m=META[i];
 if(m.k==='codigo'&&k<m.n){k++;pintar();return}
 const p=G.indexOf(i);if(p<G.length-1){i=G[p+1];k=0;pintar()}else mostrarLista();
}
function atras(){
 if(i<0)return;const m=META[i];
 if(m.k==='codigo'&&k>0){k--;pintar();return}
 const p=G.indexOf(i);if(p>0){i=G[p-1];const a=META[i];k=a.k==='codigo'?a.n:0;pintar()}else mostrarLista();   // vuelve a la última nota: el mismo camino que sig(), al revés
}
function fs(){document.fullscreenElement?document.exitFullscreen():document.documentElement.requestFullscreen&&document.documentElement.requestFullscreen()}
document.addEventListener('keydown',e=>{
 if(e.target.tagName==='SELECT'||e.ctrlKey||e.metaKey||e.altKey)return;
 if(e.target.closest&&e.target.closest('.gr')&&e.key==='Enter')return;
 const t=e.key.toLowerCase();
 if([' ','ArrowRight','Enter','PageDown'].includes(e.key)){e.preventDefault();sig()}
 else if(['ArrowLeft','Backspace','PageUp'].includes(e.key)){e.preventDefault();atras()}
 else if(e.key==='Escape'||t==='l'){if(i>=0)mostrarLista()}
 else if(t==='f')fs();
 else if(t==='d')verDiagrama();
 else if(t==='m'&&emb)parent.postMessage({menu:true},'*');
 else if(e.key==='Home'&&i>=0){i=G[0];k=0;pintar()}
 else if(e.key==='End'&&i>=0){i=G[G.length-1];k=META[i].k==='codigo'?META[i].n:0;pintar()}
});
$('#next').onclick=sig;$('#prev').onclick=atras;$('#lista-b').onclick=mostrarLista;
$('#salto').onchange=e=>{i=+e.target.value;k=0;pintar();e.target.blur()};
document.querySelectorAll('.preg[data-s]').forEach(b=>b.addEventListener('click',()=>entrar(0,+b.dataset.s)));
document.querySelectorAll('.gr').forEach(c=>{
 c.addEventListener('click',e=>{const f=e.target.closest('.fch');const g=+c.dataset.g;entrar(g,f?GRUPOS[g].entradas[f.dataset.f]:undefined)});
 c.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();e.stopPropagation();entrar(+c.dataset.g)}});
});
document.querySelectorAll('.ver[data-c]').forEach(b=>{if(emb){b.hidden=false;b.onclick=e=>{e.stopPropagation();parent.postMessage({modo:'diagrama',clase:b.dataset.c},'*')}}});
$('#proceso').onclick=()=>{if(emb)parent.postMessage({modo:'proceso'},'*');else location.href='presentar.html'};
addEventListener('resize',()=>{if(i<0)return;if(META[i].k==='codigo')ajustarCodigo();else ajustarSlide()});
mostrarLista();
</script></body></html>
"""


def main():
    slides, grupos = construir()
    SALIDA.write_text(pagina(slides, grupos), encoding="utf-8")
    cl = sum(m["n"] for m in [dict(n=len(s["d"]["notas"])) for s in slides if s["k"] == "codigo"])
    print(f"{SALIDA.name} · {len(slides)} diapositivas · {cl} notas de código · {len(grupos)} grupos")


if __name__ == "__main__":
    main()
