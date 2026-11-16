"""Genera docs/diagrama.html: diagramas del dominio donde cada clase, estado y
transición se puede clickear para ver su código REAL (leído con `ast`).

Uso, desde la raíz del repo:   python docs/diagrama_interactivo.py
Después abrí docs/diagrama.html en el navegador (o con Live Preview en VS Code).
Cada código trae un enlace «Abrir en VS Code» que salta al archivo y la línea.
"""

import ast
import html
import json
import textwrap
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]

# Columnas del diagrama de clases (x, [clases de arriba hacia abajo]). Cada clase: nombre -> (archivo, símbolo, estereotipo)
CLASES = {
    "Aviso": ("dominio/aviso.py", "Aviso", "entidad · State"),
    "Flota": ("dominio/flota.py", "Flota", "raíz de recursos"),
    "Persona": ("dominio/personal.py", "Persona", "valor inmutable"),
    "Equipo": ("dominio/equipamiento.py", "Equipo", "valor · condición"),
    "Emergencia": ("dominio/emergencia.py", "Emergencia", "raíz de agregado · State"),
    "Unidad": ("dominio/unidad.py", "Unidad", "entidad · State"),
    "Vehiculo": ("dominio/vehiculos.py", "Vehiculo", "abstracta"),
    "TransportePersonas": ("dominio/vehiculos.py", "TransportePersonas", ""),
    "VehiculoRescate": ("dominio/vehiculos.py", "VehiculoRescate", ""),
    "Ambulancia": ("dominio/vehiculos.py", "Ambulancia", ""),
    "Mision": ("dominio/mision.py", "Mision", "abstracta · State"),
    "Evacuacion": ("dominio/mision.py", "Evacuacion", ""),
    "Rescate": ("dominio/mision.py", "Rescate", ""),
    "AsistenciaSanitaria": ("dominio/mision.py", "AsistenciaSanitaria", ""),
    "Novedad": ("dominio/mision.py", "Novedad", "valor inmutable"),
    "Resultado": ("dominio/mision.py", "Resultado", "valor inmutable"),
    "Registro": ("dominio/historial.py", "Registro", "valor inmutable"),
}
ABSTRACTAS = {"Vehiculo", "Mision"}
COLUMNAS = [
    ["Aviso", "Flota", "Persona", "Equipo"],
    ["Emergencia", "Unidad", "Vehiculo", "TransportePersonas", "VehiculoRescate", "Ambulancia"],
    ["Mision", "Evacuacion", "Rescate", "AsistenciaSanitaria"],
    ["Registro", "Novedad", "Resultado"],
]
HERENCIA = {"Vehiculo": ["TransportePersonas", "VehiculoRescate", "Ambulancia"],
            "Mision": ["Evacuacion", "Rescate", "AsistenciaSanitaria"]}
HIJAS = {h for hs in HERENCIA.values() for h in hs}
# Relaciones: (origen, lado, desplazamiento, destino, lado, desplazamiento, corredor, etiqueta, tipo, mult. origen, mult. destino)
# lado: l/r/t/b. Desplazamiento: px desde la esquina de ese lado. Corredor: (columna, px) donde gira la línea, o "arriba".
# tipos: a asociación · c composición (rombo en el origen) · d dependencia
RELACIONES = [
    ("Aviso", "r", 30, "Emergencia", "l", 30, None, "origina (por id)", "a", "1", "0..1"),
    ("Emergencia", "r", 30, "Mision", "l", 30, None, "contiene", "c", "1", "0..*"),
    ("Flota", "r", 30, "Unidad", "l", 30, (0, 25), "agrupa", "c", "1", "0..*"),
    ("Unidad", "l", 70, "Persona", "r", 30, (0, 50), "dotación", "c", "1", "1..*"),
    ("Unidad", "l", 110, "Equipo", "r", 30, (0, 75), "equipamiento", "c", "1", "0..*"),
    ("Unidad", "b", 60, "Vehiculo", "t", 60, None, "vehículo", "c", "1", "1"),
    ("Mision", "l", 70, "Unidad", "r", 30, (1, 40), "asignada a", "a", "0..*", "0..1"),
    ("Mision", "l", 110, "Vehiculo", "r", 24, (1, 85), "doble despacho", "d", "", ""),
    ("Mision", "r", 30, "Novedad", "l", 30, (2, 70), "novedades", "c", "1", "0..*"),
    ("Mision", "r", 70, "Resultado", "l", 30, (2, 35), "resultado", "c", "1", "0..1"),
    ("Emergencia", "t", 100, "Registro", "t", 100, "arriba", "historial", "c", "1", "1..*"),
]
LINEA, ANCHO_CAR = 15, 6.8


def _tipo(n):
    return ast.unparse(n) if n is not None else ""


def _firma(f):
    args = [a.arg + (f": {_tipo(a.annotation)}" if a.annotation else "")
            for a in f.args.args if a.arg != "self"]
    txt = f"{f.name}({', '.join(args)})" + (f" : {_tipo(f.returns)}" if f.returns else "")
    return txt if len(txt) <= 58 else txt[:56] + "…)"


def miembros(archivo, simbolo):
    """(atributos, operaciones) leídos del código: campos de clase, self._x del __init__ y métodos públicos."""
    texto = (RAIZ / archivo).read_text(encoding="utf-8")
    cls = _buscar(ast.parse(texto), [simbolo])
    attrs, ops = [], []
    for n in cls.body:
        if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name) and "ClassVar" not in _tipo(n.annotation):
            attrs.append(f"+{n.target.id}: {_tipo(n.annotation)}")
        if isinstance(n, ast.FunctionDef) and n.name == "__init__":
            for m in ast.walk(n):
                t = None
                if isinstance(m, ast.AnnAssign):
                    t, ann = m.target, _tipo(m.annotation)
                elif isinstance(m, ast.Assign) and len(m.targets) == 1:
                    t, ann = m.targets[0], ""
                if (isinstance(t, ast.Attribute) and isinstance(t.value, ast.Name) and t.value.id == "self"):
                    nombre = t.attr.lstrip("_")
                    linea = f"{'-' if t.attr.startswith('_') else '+'}{nombre}" + (f": {ann}" if ann else "")
                    if not any(x.split(":")[0].lstrip("+-") == nombre for x in attrs):
                        attrs.append(linea)
        if isinstance(n, ast.FunctionDef) and not n.name.startswith("_"):
            decos = {_tipo(d) for d in n.decorator_list}
            if "property" in decos or any(d.endswith(".setter") for d in decos):
                continue
            ops.append(("«abs» " if "abstractmethod" in decos else "+") + _firma(n))
    return attrs, ops


def _recortar(lista, tope):
    return lista if len(lista) <= tope else lista[:tope - 1] + [f"… {len(lista) - tope + 1} más (ver código)"]


GAP_COL, SANGRIA = 150, 40


def disenar():
    """Posiciona las cajas: columnas con ancho propio; las clases hijas van sangradas bajo su padre."""
    cajas, colder = {}, []
    x = 20
    for col in COLUMNAS:
        y, maxw = 44, 0
        for nom in col:
            arch, sim, est = CLASES[nom]
            attrs, ops = miembros(arch, sim)
            attrs, ops = _recortar(attrs, 11), _recortar(ops, 11)
            filas = max(len(max(attrs + ops + [nom, est], key=len)), 14)
            w = min(max(190, filas * ANCHO_CAR + 20), 430)
            cab = 36 if est else 24
            h = cab + (len(attrs) * LINEA + 10) + (len(ops) * LINEA + 10)
            bx = x + (SANGRIA if nom in HIJAS else 0)
            cajas[nom] = dict(x=bx, y=y, w=w, h=h, cab=cab, attrs=attrs, ops=ops, est=est, sim=sim)
            y += h + (22 if nom in HIJAS or nom in HERENCIA else 40)
            maxw = max(maxw, w + (SANGRIA if nom in HIJAS else 0))
        colder.append(x + maxw)
        x += maxw + GAP_COL
    return cajas, colder


def _punto(c, lado, d):
    return {"l": (c["x"], c["y"] + d), "r": (c["x"] + c["w"], c["y"] + d),
            "t": (c["x"] + d, c["y"]), "b": (c["x"] + d, c["y"] + c["h"])}[lado]


def _ruta(a, lado_o, b, lado_d, corredor, colder):
    if corredor == "arriba":
        return [a, (a[0], 14), (b[0], 14), b]
    if lado_o in "lr" and lado_d in "lr":
        if corredor is None:
            return [a, b] if abs(a[1] - b[1]) < 1 else [a, ((a[0] + b[0]) / 2, a[1]), ((a[0] + b[0]) / 2, b[1]), b]
        m = colder[corredor[0]] + corredor[1]
        return [a, (m, a[1]), (m, b[1]), b]
    if abs(a[0] - b[0]) < 1:
        return [a, b]
    my = (a[1] + b[1]) / 2
    return [a, (a[0], my), (b[0], my), b]


def _mult(p, q, texto, p_es_origen):
    """Multiplicidad junto al extremo p; q es el siguiente punto de la ruta (da la dirección)."""
    dx, dy = q[0] - p[0], q[1] - p[1]
    if abs(dx) >= abs(dy):
        x, y, anc = p[0] + (7 if dx > 0 else -7), p[1] - 5, "start" if dx > 0 else "end"
    else:
        x, y, anc = p[0] + 7, p[1] + (14 if dy > 0 else -6), "start"
    return f'<text x="{x:.0f}" y="{y:.0f}" class="mu" text-anchor="{anc}">{texto}</text>'


def svg_clases(datos):
    cajas, colder = disenar()
    W = max(c["x"] + c["w"] for c in cajas.values()) + 20
    H = max(c["y"] + c["h"] for c in cajas.values()) + 20
    p = [f'<svg viewBox="0 0 {W:.0f} {H:.0f}" class="dg">',
         '<defs><marker id="f" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
         '<path d="M0 0L10 5L0 10z" fill="#4b5563"/></marker>'
         '<marker id="t" viewBox="0 0 12 12" refX="11" refY="6" markerWidth="12" markerHeight="12" orient="auto-start-reverse">'
         '<path d="M1 1L11 6L1 11z" fill="#fff" stroke="#4b5563" stroke-width="1.5"/></marker>'
         '<marker id="r" viewBox="0 0 14 10" refX="1" refY="5" markerWidth="13" markerHeight="9" orient="auto">'
         '<path d="M1 5L7 1L13 5L7 9z" fill="#4b5563"/></marker></defs>']
    lineas, textos = [], []
    # herencia: un tronco por jerarquía, con un solo triángulo en el padre
    for padre, hijas in HERENCIA.items():
        c = cajas[padre]
        tx = c["x"] + 18
        ult = cajas[hijas[-1]]["y"] + 14
        lineas.append(f'<path d="M{tx} {c["y"]+c["h"]} V{ult}" class="ln" marker-start="url(#t)"/>')
        for h in hijas:
            hc = cajas[h]
            lineas.append(f'<path d="M{tx} {hc["y"]+14} H{hc["x"]}" class="ln"/>')
    for o, lo, po, d, ld, pd, cor, et, tipo, mo, md in RELACIONES:
        a, b = _punto(cajas[o], lo, po), _punto(cajas[d], ld, pd)
        ruta = _ruta(a, lo, b, ld, cor, colder)
        dpath = "M" + " L".join(f"{x:.0f} {y:.0f}" for x, y in ruta)
        extra = {"a": ' marker-end="url(#f)"', "d": ' marker-end="url(#f)" stroke-dasharray="6 4"',
                 "c": ' marker-start="url(#r)" marker-end="url(#f)"'}[tipo]
        lineas.append(f'<path d="{dpath}" class="ln"{extra}/>')
        seg = max(zip(ruta, ruta[1:]), key=lambda s2: abs(s2[0][0] - s2[1][0]) + abs(s2[0][1] - s2[1][1]))
        mx, my = (seg[0][0] + seg[1][0]) / 2, (seg[0][1] + seg[1][1]) / 2
        horiz = abs(seg[0][1] - seg[1][1]) < 1
        textos.append(f'<text x="{mx+(0 if horiz else -6):.0f}" y="{my-(6 if horiz else -4):.0f}" '
                      f'class="et" text-anchor="{"middle" if horiz else "end"}">{et}</text>')
        if mo:
            textos.append(_mult(ruta[0], ruta[1], mo, True))
        if md:
            textos.append(_mult(ruta[-1], ruta[-2], md, False))
    p.extend(lineas)
    for nom, c in cajas.items():
        x, y, w = c["x"], c["y"], c["w"]
        dash = ' stroke-dasharray="5 3"' if nom in ABSTRACTAS else ""
        g = [f'<g class="nodo" data-k="{html.escape(c["sim"])}" tabindex="0">',
             f'<rect x="{x}" y="{y}" width="{w}" height="{c["h"]}" rx="6"{dash}/>']
        if c["est"]:
            g.append(f'<text x="{x+w/2}" y="{y+14}" text-anchor="middle" class="sb">«{c["est"]}»</text>')
        g.append(f'<text x="{x+w/2}" y="{y+c["cab"]-8}" text-anchor="middle" class="nm{" ab" if nom in ABSTRACTAS else ""}">{nom}</text>')
        ya = y + c["cab"]
        g.append(f'<line x1="{x}" y1="{ya}" x2="{x+w}" y2="{ya}" class="sep"/>')
        for i, t in enumerate(c["attrs"]):
            g.append(f'<text x="{x+8}" y="{ya+LINEA*(i+1)-1}" class="mb">{html.escape(t)}</text>')
        yo = ya + len(c["attrs"]) * LINEA + 10
        g.append(f'<line x1="{x}" y1="{yo}" x2="{x+w}" y2="{yo}" class="sep"/>')
        for i, t in enumerate(c["ops"]):
            g.append(f'<text x="{x+8}" y="{yo+LINEA*(i+1)-1}" class="mb">{html.escape(t)}</text>')
        g.append('</g>')
        p.append("".join(g))
    p.extend(textos)
    p.append("</svg>")
    return "".join(p)


# Estados de la misión: nombre -> clase en mision.py, x, y
ESTADOS = {
    "Pendiente": ("_Pendiente", 60, 120), "Asignada": ("_Asignada", 270, 120),
    "En ejecución": ("_EnEjecucion", 480, 120), "Finalizada": ("_Finalizada", 690, 120),
    "Cancelada": ("_Cancelada", 270, 300),
}
# origen, destino, operación (método de Mision y del estado de origen)
TRANSICIONES = [
    ("Pendiente", "Asignada", "asignar"), ("Asignada", "Asignada", "reasignar"),
    ("Asignada", "Pendiente", "rechazar"), ("Asignada", "En ejecución", "iniciar"),
    ("En ejecución", "Finalizada", "finalizar"), ("Pendiente", "Cancelada", "cancelar"),
    ("Asignada", "Cancelada", "cancelar"),
]


def _buscar(arbol, partes):
    actual = arbol
    for p in partes:
        actual = next((h for h in getattr(actual, "body", [])
                       if isinstance(h, (ast.ClassDef, ast.FunctionDef)) and h.name == p), None)
        if actual is None:
            return None
    return actual


def codigo(archivo: str, simbolo: str):
    texto = (RAIZ / archivo).read_text(encoding="utf-8")
    nodo = _buscar(ast.parse(texto), simbolo.split("."))
    if nodo is None:
        return None
    ini = (nodo.decorator_list[0].lineno if nodo.decorator_list else nodo.lineno)
    cuerpo = textwrap.dedent("\n".join(texto.splitlines()[ini - 1:nodo.end_lineno]))
    return {"archivo": archivo, "simbolo": simbolo, "linea": ini, "fin": nodo.end_lineno,
            "doc": ast.get_docstring(nodo) or "", "codigo": cuerpo,
            "abs": str((RAIZ / archivo))}


def clip(r, hacia):
    x, y, w, h = r
    cx, cy = x + w / 2, y + h / 2
    dx, dy = hacia[0] - cx, hacia[1] - cy
    if dx == 0 and dy == 0:
        return cx, cy
    t = min((w / 2) / abs(dx) if dx else 1e9, (h / 2) / abs(dy) if dy else 1e9)
    return cx + dx * t, cy + dy * t


def svg_estados(datos):
    W, H = 130, 44
    p = ['<svg viewBox="0 0 880 420" class="dg"><defs><marker id="g" viewBox="0 0 10 10" refX="9" refY="5" '
         'markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10z" fill="#6b7280"/></marker></defs>']
    pos = {k: (v[1], v[2]) for k, v in ESTADOS.items()}
    for o, d, op in TRANSICIONES:
        (x1, y1), (x2, y2) = pos[o], pos[d]
        clave = f"Mision.{op}"
        if o == d:
            p.append(f'<g class="trans" data-k="{clave}" data-k2="{ESTADOS[o][0]}.{op}">'
                     f'<path d="M{x1+30} {y1} C{x1+30} {y1-55} {x1+100} {y1-55} {x1+100} {y1}" fill="none" '
                     f'stroke="#6b7280" stroke-width="1.5" marker-end="url(#g)"/>'
                     f'<text x="{x1+65}" y="{y1-48}" text-anchor="middle" class="et">{op}</text></g>')
            continue
        a = clip((x1, y1, W, H), (x2 + W / 2, y2 + H / 2)); b = clip((x2, y2, W, H), (x1 + W / 2, y1 + H / 2))
        off = {("Asignada", "Pendiente"): 9, ("Pendiente", "Asignada"): -9}.get((o, d), 0)
        p.append(f'<g class="trans" data-k="{clave}" data-k2="{ESTADOS[o][0]}.{op}">'
                 f'<line x1="{a[0]:.0f}" y1="{a[1]+off:.0f}" x2="{b[0]:.0f}" y2="{b[1]+off:.0f}" stroke="transparent" stroke-width="14"/>'
                 f'<line x1="{a[0]:.0f}" y1="{a[1]+off:.0f}" x2="{b[0]:.0f}" y2="{b[1]+off:.0f}" stroke="#6b7280" '
                 f'stroke-width="1.5" marker-end="url(#g)"/>'
                 f'<text x="{(a[0]+b[0])/2:.0f}" y="{(a[1]+b[1])/2-6+off*2:.0f}" text-anchor="middle" class="et">{op}</text></g>')
    for k, (cls, x, y) in ESTADOS.items():
        p.append(f'<g class="nodo" data-k="{cls}" tabindex="0"><rect x="{x}" y="{y}" width="{W}" height="{H}" rx="22"/>'
                 f'<text x="{x+W/2}" y="{y+27}" text-anchor="middle" class="nm">{k}</text></g>')
    p.append("</svg>")
    return "".join(p)


PLANTILLA = """<!doctype html><html lang="es"><meta charset="utf-8"><title>CRCE · diagramas vinculados al código</title>
<style>
*{box-sizing:border-box}body{margin:0;font:14px/1.5 system-ui,sans-serif;color:#111827;background:#f9fafb}
header{padding:12px 20px;background:#111827;color:#fff;display:flex;gap:16px;align-items:center}
header h1{font-size:16px;margin:0;flex:1}
button.tab{background:none;border:1px solid #4b5563;color:#fff;padding:5px 12px;border-radius:6px;cursor:pointer}
button.tab.on{background:#2563eb;border-color:#2563eb}
main{display:grid;grid-template-columns:minmax(600px,1.9fr) minmax(380px,1fr);height:calc(100vh - 53px)}
#izq{padding:12px;overflow:auto;border-right:1px solid #e5e7eb}
.dg{width:100%;height:auto}.ln{fill:none;stroke:#4b5563;stroke-width:1.4}.dg rect{fill:#fff;stroke:#6b7280;stroke-width:1.3}
.nm{font-weight:600;font-size:13px;fill:#111827}.sb{font-size:11px;fill:#6b7280}.mu{font-size:10.5px;fill:#374151;paint-order:stroke;stroke:#f9fafb;stroke-width:3px}.mb{font:11px ui-monospace,Menlo,monospace;fill:#1f2937}.sep{stroke:#6b7280;stroke-width:1}.ab{font-style:italic}.et{font-size:11px;fill:#4b5563;paint-order:stroke;stroke:#f9fafb;stroke-width:4px}
.nodo,.trans{cursor:pointer}.nodo:hover rect,.nodo.sel rect{fill:#dbeafe;stroke:#2563eb;stroke-width:2}
.trans:hover line,.trans.sel line,.trans:hover path,.trans.sel path{stroke:#2563eb!important;stroke-width:3}
.trans:hover text,.trans.sel text{fill:#2563eb;font-weight:700}
#der{padding:16px 20px;overflow:auto;background:#fff}
#der h2{margin:0 0 2px;font-size:18px}.meta{color:#6b7280;font-size:12px;margin-bottom:10px}
pre{background:#0f172a;color:#e2e8f0;padding:14px;border-radius:8px;overflow:auto;font:12.5px/1.55 ui-monospace,Menlo,monospace}
.k{color:#c084fc}.s{color:#86efac}.c{color:#94a3b8}.d{color:#fbbf24}
.doc{background:#eff6ff;border-left:3px solid #2563eb;padding:8px 12px;margin:0 0 10px;white-space:pre-wrap}
a.vs{display:inline-block;margin:0 8px 10px 0;padding:5px 10px;background:#2563eb;color:#fff;border-radius:6px;text-decoration:none;font-size:12px}
.vacio{color:#6b7280}
</style>
<header><h1>CRCE · clickeá un elemento para ver su código</h1>
<button class="tab on" data-t="c">Modelo de clases</button><button class="tab" data-t="e">Estados de la misión</button></header>
<main><div id="izq"><div id="c">@@CLASES@@</div><div id="e" hidden>@@ESTADOS@@</div></div>
<div id="der"><p class="vacio">Clickeá una clase, un estado o una flecha (transición).<br>
Punteada = clase abstracta · ◆ composición · ▷ herencia · ⇢ dependencia (consulta).</p></div></main>
<script>
const D=@@DATOS@@;
const der=document.getElementById('der');
function esc(s){return s.replace(/&/g,'&amp;').replace(/</g,'&lt;')}
function resaltar(c){
 const re=/(#.*$)|(f?"[^"\\n]*"|f?'[^'\\n]*')|(^\\s*@[\\w.]+)|\\b(class|def|return|raise|if|else|elif|for|in|not|and|or|is|None|True|False|from|import|self|with|lambda)\\b/gm;
 let o='',u=0,m;while((m=re.exec(c))){o+=esc(c.slice(u,m.index));
  const cl=m[1]?'c':m[2]?'s':m[3]?'d':'k';o+='<span class='+cl+'>'+esc(m[0])+'</span>';u=re.lastIndex}
 return o+esc(c.slice(u))}
function bloque(k,titulo){const d=D[k];if(!d)return '<p class=vacio>No encontré '+k+'</p>';
 return '<h3>'+titulo+'</h3><div class=meta>'+d.archivo+' · líneas '+d.linea+'–'+d.fin+'</div>'+
 '<a class=vs href="vscode://file/'+d.abs+':'+d.linea+'">Abrir en VS Code</a>'+
 (d.doc?'<div class=doc>'+esc(d.doc)+'</div>':'')+'<pre>'+resaltar(d.codigo)+'</pre>'}
document.querySelectorAll('.nodo').forEach(n=>n.onclick=()=>{
 document.querySelectorAll('.sel').forEach(x=>x.classList.remove('sel'));n.classList.add('sel');
 const k=n.dataset.k;der.innerHTML='<h2>'+k+'</h2>'+bloque(k,'Definición')});
document.querySelectorAll('.trans').forEach(n=>n.onclick=()=>{
 document.querySelectorAll('.sel').forEach(x=>x.classList.remove('sel'));n.classList.add('sel');
 const op=n.dataset.k.split('.')[1];der.innerHTML='<h2>Transición «'+op+'»</h2>'+
 bloque(n.dataset.k,'La misión delega en su estado (Mision.'+op+')')+
 bloque(n.dataset.k2,'El estado de origen decide ('+n.dataset.k2+')')});
document.querySelectorAll('.tab').forEach(b=>b.onclick=()=>{
 document.querySelectorAll('.tab').forEach(x=>x.classList.toggle('on',x===b));
 document.getElementById('c').hidden=b.dataset.t!='c';document.getElementById('e').hidden=b.dataset.t!='e'});
</script></html>"""


def main():
    pedidos = {(a, s) for a, s, _ in CLASES.values()}
    pedidos |= {("dominio/mision.py", c) for c, *_ in ESTADOS.values()}
    for o, _, op in TRANSICIONES:
        pedidos |= {("dominio/mision.py", f"Mision.{op}"), ("dominio/mision.py", f"{ESTADOS[o][0]}.{op}")}
    datos = {}
    for arch, sim in sorted(pedidos):
        d = codigo(arch, sim)
        if d is None:
            print(f"AVISO: no encontré {sim} en {arch}")
            continue
        datos[sim] = d
    # claves de clases de estado y de métodos de estado viven en mision.py (los _Estado de otros módulos no se pisan)
    out = (PLANTILLA.replace("@@CLASES@@", svg_clases(datos)).replace("@@ESTADOS@@", svg_estados(datos))
           .replace("@@DATOS@@", json.dumps(datos).replace("</", "<\\/")))
    destino = RAIZ / "docs" / "diagrama.html"
    destino.write_text(out, encoding="utf-8")
    print(f"Listo: {destino} ({len(datos)} símbolos vinculados)")


if __name__ == "__main__":
    main()
