"""Genera docs/diagrama.html: diagramas del dominio vinculados al código REAL.

Cada clase, atributo, operación, estado y transición se puede clickear (o activar con
el teclado) para ver su código, y tiene un botón «Ver en VS Code» que salta al archivo
y la línea. Todo se lee con `ast`, así que el diagrama no se desfasa del código.

Uso, desde la raíz del repo:   python3 docs/diagrama_interactivo.py
Después abrí docs/diagrama.html en el navegador.
"""

import ast
import html
import json
import textwrap
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]

# nombre mostrado -> (archivo, símbolo, estereotipo)
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
# (origen, lado, desplazamiento, destino, lado, desplazamiento, corredor, etiqueta, tipo, mult. origen, mult. destino)
# lado: l/r/t/b · corredor: (columna, px) donde gira la línea, o "arriba" · tipo: a asociación, c composición, d dependencia
RELACIONES = [
    ("Aviso", "r", 30, "Emergencia", "l", 30, None, "origina (por id)", "a", "1", "0..1"),
    ("Emergencia", "r", 30, "Mision", "l", 30, None, "contiene", "c", "1", "0..*"),
    ("Flota", "r", 30, "Unidad", "l", 30, (0, 40), "agrupa", "c", "1", "0..*"),
    ("Unidad", "l", 70, "Persona", "r", 30, (0, 110), "dotación", "c", "1", "1..*"),
    ("Unidad", "l", 110, "Equipo", "r", 30, (0, 180), "equipamiento", "c", "1", "0..*"),
    ("Unidad", "b", 60, "Vehiculo", "t", 60, None, "vehículo", "c", "1", "1"),
    ("Mision", "l", 70, "Unidad", "r", 30, (1, 60), "asignada a", "a", "0..*", "0..1"),
    ("Mision", "l", 110, "Vehiculo", "r", 24, (1, 160), "doble despacho", "d", "", ""),
    ("Mision", "r", 30, "Novedad", "l", 30, (2, 50), "novedades", "c", "1", "0..*"),
    ("Mision", "r", 70, "Resultado", "l", 30, (2, 140), "resultado", "c", "1", "0..1"),
    ("Emergencia", "t", 100, "Registro", "t", 100, "arriba", "historial", "c", "1", "1..*"),
]
TIPOS_REL = {"a": "se asocia con", "c": "contiene", "d": "consulta a"}
ESTADOS = {
    "Pendiente": ("_Pendiente", 60, 130), "Asignada": ("_Asignada", 290, 130),
    "En ejecución": ("_EnEjecucion", 520, 130), "Finalizada": ("_Finalizada", 750, 130),
    "Cancelada": ("_Cancelada", 290, 320),
}
TRANSICIONES = [
    ("Pendiente", "Asignada", "asignar"), ("Asignada", "Asignada", "reasignar"),
    ("Asignada", "Pendiente", "rechazar"), ("Asignada", "En ejecución", "iniciar"),
    ("En ejecución", "Finalizada", "finalizar"), ("Pendiente", "Cancelada", "cancelar"),
    ("Asignada", "Cancelada", "cancelar"),
]
# Reglas del Avance 1, tal como figuran en el enunciado (id, texto, fuente)
REGLAS = [
    ("R1", "Un aviso nace pendiente, con ubicación, tipo de situación, gravedad estimada, descripción, reportante y fecha y hora de registro.", "§2.1, §7.1"),
    ("R2", "Mientras el aviso está pendiente se le pueden agregar notas de texto. Cada nota conserva autor, fecha y hora.", "§2.1"),
    ("R3", "Agregar una nota no cambia ningún dato original del aviso.", "§2.1"),
    ("R4", "Descartar exige una justificación que no esté vacía. El aviso descartado conserva esa justificación y su fecha.", "§2.2, §7.1"),
    ("R5", "Un aviso que ya no está pendiente (descartado o aceptado) rechaza nuevas notas y nuevas evaluaciones. Un segundo descarte también se rechaza.", "§7.1"),
    ("R6", "Una operación rechazada no deja cambios: falla antes de modificar el objeto.", "§9"),
]
# Enunciado del TP: poné el PDF en docs/enunciado.pdf. Cada sección apunta a su página.
ENUNCIADO = "enunciado.pdf"
# sección -> (página, altura del título en puntos desde el borde superior de la página, título)
SECCIONES = {"2.1": (1, 524, "Reportantes institucionales"), "2.2": (2, 114, "Operadores de coordinación"),
             "3": (3, 161, "Tipos de situaciones de emergencia"), "4": (3, 587, "Niveles de gravedad"),
             "7.1": (8, 364, "Avisos"), "9": (10, 360, "Seguridad y trazabilidad")}
FUENTES_REGLAS = ["dominio/aviso.py", "dominio/errores.py"]
ARCHIVOS_TESTS_REGLAS = ["tests/test_avisos.py", "tests/test_avisos_robustez.py"]
LINEA, ANCHO_CAR, GAP_COL, SANGRIA = 26, 8.1, 240, 44


# ───────────────────────── lectura del código ─────────────────────────

def _tipo(n):
    return ast.unparse(n) if n is not None else ""


def _buscar(arbol, partes):
    actual = arbol
    for p in partes:
        actual = next((h for h in getattr(actual, "body", [])
                       if isinstance(h, (ast.ClassDef, ast.FunctionDef)) and h.name == p), None)
        if actual is None:
            return None
    return actual


def _entrada(archivo, ini, fin, simbolo, titulo, doc=""):
    lineas = (RAIZ / archivo).read_text(encoding="utf-8").splitlines()
    return {"archivo": archivo, "simbolo": simbolo, "titulo": titulo, "linea": ini, "fin": fin, "doc": doc,
            "codigo": textwrap.dedent("\n".join(lineas[ini - 1:fin])), "abs": str(RAIZ / archivo)}


def codigo(archivo, simbolo, titulo=None):
    arbol = ast.parse((RAIZ / archivo).read_text(encoding="utf-8"))
    nodo = _buscar(arbol, simbolo.split("."))
    if nodo is None:
        return None
    ini = nodo.decorator_list[0].lineno if nodo.decorator_list else nodo.lineno
    return _entrada(archivo, ini, nodo.end_lineno, simbolo, titulo or simbolo, ast.get_docstring(nodo) or "")


def _firma(f):
    args = [a.arg + (f": {_tipo(a.annotation)}" if a.annotation else "")
            for a in f.args.args if a.arg != "self"]
    return f"{f.name}({', '.join(args)})" + (f" : {_tipo(f.returns)}" if f.returns else "")


def _corto(txt, tope=60):
    return txt if len(txt) <= tope else txt[:tope - 1] + "…"


def _firma_caja(f):
    """Firma resumida para la caja: solo nombres de parámetros (la completa está en el tooltip y en el panel)."""
    nombres = [a.arg for a in f.args.args if a.arg != "self"]
    if len(nombres) > 3:
        nombres = nombres[:3] + ["…"]
    ret = _tipo(f.returns)
    return f"{f.name}({', '.join(nombres)})" + (f" : {ret}" if ret and ret != "None" else "")


def miembros(archivo, simbolo, datos):
    """Atributos y operaciones de una clase, leídos del código. Registra su código en `datos`.
    Devuelve ([(texto, clave, completo)], [(texto, clave, completo)])."""
    arbol = ast.parse((RAIZ / archivo).read_text(encoding="utf-8"))
    cls = _buscar(arbol, [simbolo])
    attrs, ops, vistos = [], [], set()

    def attr(nombre, privado, ann, nodo):
        if nombre in vistos:
            return
        vistos.add(nombre)
        completo = f"{'-' if privado else '+'}{nombre}" + (f": {ann}" if ann else "")
        clave = f"{simbolo}#{nombre}"
        datos[clave] = _entrada(archivo, nodo.lineno, nodo.end_lineno, f"{simbolo}.{nombre}",
                                f"Atributo {completo} de {simbolo}")
        attrs.append((_corto(completo), clave, completo))

    for n in cls.body:
        if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name) and "ClassVar" not in _tipo(n.annotation):
            attr(n.target.id, False, _tipo(n.annotation), n)
        if isinstance(n, ast.FunctionDef) and n.name == "__init__":
            for m in ast.walk(n):
                t, ann = None, ""
                if isinstance(m, ast.AnnAssign):
                    t, ann = m.target, _tipo(m.annotation)
                elif isinstance(m, ast.Assign) and len(m.targets) == 1:
                    t = m.targets[0]
                if isinstance(t, ast.Attribute) and isinstance(t.value, ast.Name) and t.value.id == "self":
                    attr(t.attr.lstrip("_"), t.attr.startswith("_"), ann, m)
        if isinstance(n, ast.FunctionDef) and not n.name.startswith("_"):
            decos = {_tipo(d) for d in n.decorator_list}
            if "property" in decos or any(d.endswith(".setter") for d in decos):
                continue
            clave = f"{simbolo}.{n.name}"
            datos[clave] = codigo(archivo, clave, f"Operación {n.name} de {simbolo}")
            pre = "«abs» " if "abstractmethod" in decos else "+"
            ops.append((_corto(pre + _firma_caja(n)), clave, pre + _firma(n)))
    return attrs, ops


# ───────────────────────── geometría ─────────────────────────

def disenar(datos):
    cajas, colder, x = {}, [], 20
    for col in COLUMNAS:
        y, maxw = 56, 0
        for nom in col:
            arch, sim, est = CLASES[nom]
            attrs, ops = miembros(arch, sim, datos)
            filas = max(len(max([t for t, *_ in attrs + ops] + [nom, est], key=len)), 14)
            w = min(max(230, filas * ANCHO_CAR + 32), 520)
            cab = 46 if est else 34
            h = cab + len(attrs) * LINEA + 20 + len(ops) * LINEA + 20
            bx = x + (SANGRIA if nom in HIJAS else 0)
            cajas[nom] = dict(x=bx, y=y, w=w, h=h, cab=cab, attrs=attrs, ops=ops, est=est, sim=sim, arch=arch)
            y += h + (34 if nom in HIJAS or nom in HERENCIA else 60)
            maxw = max(maxw, w + (SANGRIA if nom in HIJAS else 0))
        colder.append(x + maxw)
        x += maxw + GAP_COL
    return cajas, colder


def clip(r, hacia):
    x, y, w, h = r
    cx, cy = x + w / 2, y + h / 2
    dx, dy = hacia[0] - cx, hacia[1] - cy
    if dx == 0 and dy == 0:
        return cx, cy
    t = min((w / 2) / abs(dx) if dx else 1e9, (h / 2) / abs(dy) if dy else 1e9)
    return cx + dx * t, cy + dy * t


def _punto(c, lado, d):
    return {"l": (c["x"], c["y"] + d), "r": (c["x"] + c["w"], c["y"] + d),
            "t": (c["x"] + d, c["y"]), "b": (c["x"] + d, c["y"] + c["h"])}[lado]


def _ruta(a, lado_o, b, lado_d, corredor, colder):
    if corredor == "arriba":
        return [a, (a[0], 18), (b[0], 18), b]
    if lado_o in "lr" and lado_d in "lr":
        if corredor is None:
            return [a, b] if abs(a[1] - b[1]) < 1 else [a, ((a[0] + b[0]) / 2, a[1]), ((a[0] + b[0]) / 2, b[1]), b]
        m = colder[corredor[0]] + corredor[1]
        return [a, (m, a[1]), (m, b[1]), b]
    if abs(a[0] - b[0]) < 1:
        return [a, b]
    my = (a[1] + b[1]) / 2
    return [a, (a[0], my), (b[0], my), b]


def _mult(p, q, texto, n=""):
    dx, dy = q[0] - p[0], q[1] - p[1]
    if abs(dx) >= abs(dy):
        x, y, anc = p[0] + (10 if dx > 0 else -10), p[1] - 8, "start" if dx > 0 else "end"
    else:
        x, y, anc = p[0] + 10, p[1] + (18 if dy > 0 else -8), "start"
    return f'<text x="{x:.0f}" y="{y:.0f}" class="mu" data-n="{n}" text-anchor="{anc}">{texto}</text>'


def vscode(d):
    return f"vscode://file/{d['abs']}:{d['linea']}"


def svg_clases(cajas, colder, datos):
    W = max(c["x"] + c["w"] for c in cajas.values()) + 24
    H = max(c["y"] + c["h"] for c in cajas.values()) + 24
    p = [f'<svg viewBox="0 0 {W:.0f} {H:.0f}" class="dg" id="svgc" data-w="{W:.0f}" role="group" '
         f'aria-label="Diagrama de clases del CRCE. Usá Tab para recorrer las clases.">',
         '<defs><marker id="f" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
         '<path d="M0 0L10 5L0 10z" class="mk"/></marker>'
         '<filter id="sh" x="-8%" y="-6%" width="116%" height="120%"><feDropShadow dx="0" dy="1" stdDeviation="1" flood-color="#171a23" flood-opacity=".10"/>'
         '<feDropShadow dx="0" dy="6" stdDeviation="7" flood-color="#171a23" flood-opacity=".10"/></filter>'
         '<marker id="t" viewBox="0 0 12 12" refX="11" refY="6" markerWidth="12" markerHeight="12" orient="auto-start-reverse">'
         '<path d="M1 1L11 6L1 11z" class="mkh"/></marker>'
         '<marker id="r" viewBox="0 0 14 10" refX="1" refY="5" markerWidth="13" markerHeight="9" orient="auto">'
         '<path d="M1 5L7 1L13 5L7 9z" class="mk"/></marker></defs>']
    lineas, textos = [], []
    for padre, hijas in HERENCIA.items():
        c = cajas[padre]
        tx = c["x"] + 18
        lineas.append(f'<path d="M{tx} {c["y"]+c["h"]} V{cajas[hijas[-1]]["y"]+14}" class="ln" data-n="{padre} {" ".join(hijas)}" marker-start="url(#t)"/>')
        for h in hijas:
            lineas.append(f'<path d="M{tx} {cajas[h]["y"]+14} H{cajas[h]["x"]}" class="ln" data-n="{padre} {h}"/>')
    for o, lo, po, d, ld, pd, cor, et, tipo, mo, md in RELACIONES:
        a, b = _punto(cajas[o], lo, po), _punto(cajas[d], ld, pd)
        ruta = _ruta(a, lo, b, ld, cor, colder)
        extra = {"a": ' marker-end="url(#f)"', "d": ' marker-end="url(#f)" stroke-dasharray="6 4"',
                 "c": ' marker-start="url(#r)" marker-end="url(#f)"'}[tipo]
        lineas.append(f'<path d="M{" L".join(f"{x:.0f} {y:.0f}" for x, y in ruta)}" class="ln" data-n="{o} {d}"{extra}/>')
        seg = max(zip(ruta, ruta[1:]), key=lambda s: abs(s[0][0] - s[1][0]) + abs(s[0][1] - s[1][1]))
        mx, my = (seg[0][0] + seg[1][0]) / 2, (seg[0][1] + seg[1][1]) / 2
        horiz = abs(seg[0][1] - seg[1][1]) < 1
        textos.append(f'<text x="{mx:.0f}" y="{my+4:.0f}" class="et" data-n="{o} {d}" text-anchor="middle">{et}</text>')
        if mo:
            textos.append(_mult(ruta[0], ruta[1], mo, f"{o} {d}"))
        if md:
            textos.append(_mult(ruta[-1], ruta[-2], md, f"{o} {d}"))
    p.extend(lineas)
    for nom, c in cajas.items():
        x, y, w, sim = c["x"], c["y"], c["w"], c["sim"]
        d = datos[sim]
        abst = nom in ABSTRACTAS
        desc = (f"{nom}, {'clase abstracta, ' if abst else ''}{c['est'] or 'clase'}. "
                f"{len(c['attrs'])} atributos y {len(c['ops'])} operaciones. "
                "Enter muestra el código, flecha abajo recorre sus miembros, V abre VS Code.")
        raiz = "raíz" in c["est"]
        g = [f'<g class="nodo{" raiz" if raiz else ""}" data-k="{html.escape(sim)}" tabindex="0" role="button" aria-label="{html.escape(desc)}">',
             f'<rect class="puente" x="{x}" y="{y-24}" width="{w}" height="24"/>',
             f'<rect class="box{" abs" if abst else ""}" x="{x}" y="{y}" width="{w}" height="{c["h"]}" rx="9"/>']
        g.append(f'<path class="{"cabraiz" if raiz else "cab"}" d="M{x} {y+c["cab"]} V{y+9} Q{x} {y} {x+9} {y} H{x+w-9} Q{x+w} {y} {x+w} {y+9} V{y+c["cab"]} Z"/>')
        if c["est"]:
            g.append(f'<text x="{x+w/2}" y="{y+16}" text-anchor="middle" class="sb">«{c["est"]}»</text>')
        g.append(f'<text x="{x+w/2}" y="{y+c["cab"]-9}" text-anchor="middle" class="nm{" it" if abst else ""}">{nom}</text>')
        ya = y + c["cab"]
        g.append(f'<line x1="{x}" y1="{ya}" x2="{x+w}" y2="{ya}" class="sep"/>')
        for i, (txt, clave, completo) in enumerate(c["attrs"]):
            ry = ya + 10 + LINEA * i
            g.append(f'<g class="mi" data-k="{html.escape(clave)}" tabindex="-1" role="button" '
                     f'aria-label="Atributo {html.escape(completo)}"><title>{html.escape(completo)}</title>'
                     f'<rect class="hit" x="{x+2}" y="{ry}" width="{w-4}" height="{LINEA}"/>'
                     f'<text x="{x+10}" y="{ry+LINEA-8}" class="mb">{html.escape(txt)}</text></g>')
        yo = ya + len(c["attrs"]) * LINEA + 20
        g.append(f'<line x1="{x}" y1="{yo}" x2="{x+w}" y2="{yo}" class="sep"/>')
        for i, (txt, clave, completo) in enumerate(c["ops"]):
            ry = yo + 10 + LINEA * i
            g.append(f'<g class="mi" data-k="{html.escape(clave)}" tabindex="-1" role="button" '
                     f'aria-label="Operación {html.escape(completo)}"><title>{html.escape(completo)}</title>'
                     f'<rect class="hit" x="{x+2}" y="{ry}" width="{w-4}" height="{LINEA}"/>'
                     f'<text x="{x+10}" y="{ry+LINEA-8}" class="mb">{html.escape(txt)}</text></g>')
        g.append(f'<a class="vs" href="{vscode(d)}" aria-label="Abrir {nom} en VS Code, línea {d["linea"]}">'
                 f'<rect x="{x+w-126}" y="{y-22}" width="126" height="22" rx="5"/>'
                 f'<text x="{x+w-63}" y="{y-7}" text-anchor="middle">Ver en VS Code ↗</text></a>')
        g.append('</g>')
        p.append("".join(g))
    p.extend(textos)
    p.append("</svg>")
    return "".join(p)


def svg_estados(datos):
    W, H = 150, 48
    p = ['<svg viewBox="0 0 960 460" class="dg" id="svge" data-w="960" role="group" '
         'aria-label="Diagrama de estados de la misión. Tab recorre estados y transiciones.">'
         '<defs><marker id="g" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
         '<path d="M0 0L10 5L0 10z" class="mk"/></marker>'
         '<filter id="sh2" x="-10%" y="-20%" width="120%" height="160%"><feDropShadow dx="0" dy="1" stdDeviation="1" flood-color="#171a23" flood-opacity=".10"/>'
         '<feDropShadow dx="0" dy="6" stdDeviation="7" flood-color="#171a23" flood-opacity=".10"/></filter></defs>']
    pos = {k: (v[1], v[2]) for k, v in ESTADOS.items()}
    for o, d, op in TRANSICIONES:
        (x1, y1), (x2, y2) = pos[o], pos[d]
        clave, clave2 = f"Mision.{op}", f"{ESTADOS[o][0]}.{op}"
        aria = f"Transición {op}: de {o} a {d}. Enter muestra el código."
        if o == d:
            p.append(f'<g class="trans" data-k="{clave}" data-k2="{clave2}" tabindex="0" role="button" aria-label="{aria}">'
                     f'<path d="M{x1+35} {y1} C{x1+35} {y1-62} {x1+115} {y1-62} {x1+115} {y1}" class="ln" marker-end="url(#g)"/>'
                     f'<text x="{x1+75}" y="{y1-60}" text-anchor="middle" class="et2">{op}</text></g>')
            continue
        a = clip((x1, y1, W, H), (x2 + W / 2, y2 + H / 2))
        b = clip((x2, y2, W, H), (x1 + W / 2, y1 + H / 2))
        off = {("Asignada", "Pendiente"): 10, ("Pendiente", "Asignada"): -10}.get((o, d), 0)
        p.append(f'<g class="trans" data-k="{clave}" data-k2="{clave2}" tabindex="0" role="button" aria-label="{aria}">'
                 f'<line x1="{a[0]:.0f}" y1="{a[1]+off:.0f}" x2="{b[0]:.0f}" y2="{b[1]+off:.0f}" stroke="transparent" stroke-width="18"/>'
                 f'<line x1="{a[0]:.0f}" y1="{a[1]+off:.0f}" x2="{b[0]:.0f}" y2="{b[1]+off:.0f}" class="ln" marker-end="url(#g)"/>'
                 f'<text x="{(a[0]+b[0])/2:.0f}" y="{(a[1]+b[1])/2-8+off*2:.0f}" text-anchor="middle" class="et2">{op}</text></g>')
    for k, (cls, x, y) in ESTADOS.items():
        d = datos[cls]
        p.append(f'<g class="nodo" data-k="{cls}" tabindex="0" role="button" aria-label="Estado {k}. Enter muestra el código de {cls}.">'
                 f'<rect class="box est" x="{x}" y="{y}" width="{W}" height="{H}" rx="24"/>'
                 f'<text x="{x+W/2}" y="{y+30}" text-anchor="middle" class="nm">{k}</text></g>')
    p.append("</svg>")
    return "".join(p)


def citas_de_reglas(datos):
    """Busca qué clases/métodos citan cada regla (R1..R6) en su docstring y qué tests la prueban.
    Registra su código en `datos` y devuelve {regla: {"codigo": [(clave, rotulo)], "tests": [(clave, rotulo)]}}."""
    import re
    citas = {r: {"codigo": [], "tests": []} for r, *_ in REGLAS}
    for archivo in FUENTES_REGLAS:
        arbol = ast.parse((RAIZ / archivo).read_text(encoding="utf-8"))

        def visitar(nodo, prefijo=""):
            for h in getattr(nodo, "body", []):
                if isinstance(h, (ast.ClassDef, ast.FunctionDef)):
                    simbolo = prefijo + h.name
                    doc = ast.get_docstring(h) or ""
                    for r in sorted(set(re.findall(r"\bR([1-6])\b", doc))):
                        clave = simbolo if simbolo in datos else f"{archivo}::{simbolo}"
                        if clave not in datos:
                            datos[clave] = codigo(archivo, simbolo, simbolo)
                        citas[f"R{r}"]["codigo"].append((clave, simbolo))
                    if isinstance(h, ast.ClassDef):
                        visitar(h, simbolo + ".")
        visitar(arbol)
    for archivo in ARCHIVOS_TESTS_REGLAS:
        arbol = ast.parse((RAIZ / archivo).read_text(encoding="utf-8"))
        for h in arbol.body:
            if isinstance(h, ast.FunctionDef):
                for r in sorted(set(re.findall(r"(?:^|_)r([1-6])(?=_)", h.name))):
                    clave = f"test::{h.name}"
                    datos[clave] = codigo(archivo, h.name, h.name)
                    citas[f"R{r}"]["tests"].append((clave, h.name))
    return citas


def enlaces_seccion(fuente):
    """'§2.2, §7.1' -> enlaces que abren el enunciado en la página de cada sección."""
    import re
    partes = []
    for sec in re.findall(r"§(\d+(?:\.\d+)?)", fuente):
        pag, y, titulo = SECCIONES.get(sec, (1, 0, ""))
        destino = f"{ENUNCIADO}#page={pag}&zoom=100,0,{max(y - 40, 0)}"
        partes.append(f'<a class="sec" href="{destino}" target="_blank" rel="noopener" '
                      f'title="{html.escape(titulo)} · abre el enunciado en la página {pag}" '
                      f'aria-label="Sección {sec}, {html.escape(titulo)}. Abre el enunciado en la página {pag}">§{sec}</a>')
    return ", ".join(partes)


def vista_reglas(citas):
    o = ['<section class="reglas" aria-labelledby="h-reglas"><h2 id="h-reglas">Reglas de negocio (Avance 1)</h2>',
         '<p class="meta">Para citarlas: «R4 (§2.2, §7.1)». Cada sección abre el enunciado en su página. Cada regla lleva el código que la hace cumplir y los tests que la prueban.</p>']
    for rid, texto, fuente in REGLAS:
        c = citas[rid]
        o.append(f'<article class="regla" id="{rid}"><h3><span class="rid">{rid}</span> <span class="fte">Sección {enlaces_seccion(fuente)}</span></h3>'
                 f'<p>{html.escape(texto)}</p>')
        if c["codigo"]:
            o.append('<p class="rotulo">Código</p><ul class="chips">' + "".join(
                f'<li><button class="lk" data-k="{html.escape(k)}">{html.escape(r)}</button></li>' for k, r in dict.fromkeys(c["codigo"])) + '</ul>')
        if c["tests"]:
            o.append(f'<details><summary>{len(c["tests"])} {"test" if len(c["tests"]) == 1 else "tests"}</summary><ul class="chips">' + "".join(
                f'<li><button class="lk" data-k="{html.escape(k)}">{html.escape(r)}</button></li>' for k, r in c["tests"]) + '</ul></details>')
        o.append('</article>')
    o.append('<p class="meta">El tipo de situación y la gravedad son catálogos cerrados (§3 y §4): un valor fuera del catálogo no puede llegar a un aviso.</p></section>')
    return "".join(o)


def vista_lista(cajas, datos):
    """Alternativa en texto del diagrama (para lectores de pantalla y para quien prefiera listas)."""
    o = ['<p>Misma información que el diagrama, en forma de lista. Cada elemento es un botón que muestra su código.</p>']
    for nom, c in cajas.items():
        d = datos[c["sim"]]
        o.append(f'<section class="cls"><h3><button class="lk" data-k="{html.escape(c["sim"])}">{nom}</button> '
                 f'<a class="btn" href="{vscode(d)}" aria-label="Abrir {nom} en VS Code">Ver en VS Code ↗</a></h3>')
        if c["est"]:
            o.append(f'<p class="meta">{c["est"]}{" · abstracta" if nom in ABSTRACTAS else ""} · {d["archivo"]}</p>')
        for titulo, lista in (("Atributos", c["attrs"]), ("Operaciones", c["ops"])):
            if lista:
                o.append(f'<h4>{titulo}</h4><ul>' + "".join(
                    f'<li><button class="lk" data-k="{html.escape(k)}">{html.escape(full)}</button></li>'
                    for _, k, full in lista) + '</ul>')
        o.append('</section>')
    o.append('<section class="cls"><h3>Relaciones</h3><ul>')
    for ori, _, _, dst, _, _, _, et, tipo, mo, md in RELACIONES:
        card = f" ({mo} → {md})" if mo or md else ""
        o.append(f'<li>{ori} {TIPOS_REL[tipo]} {dst}: «{et}»{card}</li>')
    for padre, hijas in HERENCIA.items():
        o.append(f'<li>{", ".join(hijas)} {"heredan" if len(hijas) > 1 else "hereda"} de {padre}</li>')
    o.append('</ul></section>')
    return "".join(o)


PLANTILLA = r"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>CRCE · diagramas vinculados al código</title>
<style>
:root{--bg:#f1f2f7;--card:#fff;--fg:#171a23;--mut:#4c5466;--lin:#566075;--acc:#4338ca;--accdk:#312e81;--mark:#dfe3fb;--marksoft:#eef0fd;--foco:#c2410c;--cabbg:#eceefa;--gut:#f4f5fa;--pt:#c9cde0;
--sh1:0 1px 2px rgba(23,26,35,.07),0 4px 14px rgba(23,26,35,.07);--sh2:0 2px 4px rgba(23,26,35,.08),0 12px 28px rgba(23,26,35,.12)}
*{box-sizing:border-box}html,body{height:100%}
body{margin:0;font:16px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif;color:var(--fg);background:var(--bg);display:flex;flex-direction:column}
.skip{position:absolute;left:8px;top:-60px;background:var(--card);color:var(--fg);padding:10px 14px;border:2px solid var(--acc);z-index:99;border-radius:8px}
.skip:focus{top:8px}
header{background:var(--card);padding:10px 20px;display:flex;flex-wrap:wrap;gap:10px 20px;align-items:center;box-shadow:var(--sh1);position:relative;z-index:3}
header h1{font-size:17px;font-weight:700;letter-spacing:-.01em;margin:0;flex:1 1 260px}
header h1 small{display:block;font-weight:400;font-size:13px;color:var(--mut);letter-spacing:0}
[role=tablist]{display:flex;gap:2px;padding:4px;background:#e4e6f0;border-radius:12px}
button,.btn,a.btn{font:inherit;cursor:pointer}
.tab{min-height:38px;padding:5px 16px;border:0;border-radius:9px;background:transparent;color:var(--mut);font-weight:500}
.tab:hover{color:var(--fg)}
.tab[aria-selected=true]{background:var(--card);color:var(--fg);font-weight:600;box-shadow:0 1px 3px rgba(23,26,35,.22)}
.tool{min-height:38px;padding:5px 14px;border-radius:10px;border:1.5px solid var(--pt);background:var(--card);color:var(--fg);font-weight:500}
.tool:hover{border-color:var(--acc);color:var(--acc)}
.tool[aria-pressed=true]{background:var(--fg);border-color:var(--fg);color:#fff}
:focus-visible{outline:3px solid var(--foco);outline-offset:2px}
main{flex:1;min-height:0;display:grid;grid-template-columns:minmax(0,1.5fr) minmax(400px,1fr)}
@media(max-width:900px){main{grid-template-columns:1fr;grid-auto-rows:minmax(300px,1fr)}}
#izq{display:flex;flex-direction:column;min-height:0;position:relative}
.barra{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:12px 14px 0;padding:8px 10px;background:var(--card);border-radius:14px;box-shadow:var(--sh1);position:relative;z-index:2}
.barra .z{min-width:52px;text-align:center;font-weight:600;font-variant-numeric:tabular-nums}
.barra .sep2{width:1px;height:24px;background:var(--pt);margin:0 4px}
.barra input{min-height:38px;width:220px;max-width:100%;padding:5px 12px;border-radius:10px;border:1.5px solid var(--pt);font:inherit;background:var(--bg);color:var(--fg)}
.barra input:focus{border-color:var(--acc);background:var(--card)}
.barra .ayuda{color:var(--mut);font-size:13px;margin-left:auto}
#lienzo{flex:1;overflow:auto;padding:22px 22px 40px;cursor:grab;background-color:var(--bg);background-image:radial-gradient(var(--pt) 1.2px,transparent 1.2px);background-size:24px 24px}
#lienzo.arr{cursor:grabbing;user-select:none}
.vista[hidden]{display:none}
.dg{display:block;height:auto}
.dg .box{fill:var(--card);stroke:var(--lin);stroke-width:1.2;filter:url(#sh)}.dg .box.abs{stroke-dasharray:6 4}.dg .box.est{filter:url(#sh2);stroke:var(--acc);stroke-width:2}.nodo:hover>.box.est,.nodo.sel>.box.est{fill:var(--mark)}
.dg .puente{fill:transparent}
.cab{fill:var(--cabbg)}.cabraiz{fill:var(--accdk)}.raiz .nm,.raiz .sb{fill:#fff}
.nm{font-weight:700;font-size:16px;fill:var(--fg)}.it{font-style:italic}.sb{font-size:13px;fill:var(--mut)}
.mb{font:13px ui-monospace,"SF Mono",Menlo,Consolas,monospace;fill:var(--fg)}
.sep{stroke:var(--pt);stroke-width:1}
.et,.et2{fill:var(--fg);font-size:13px;font-weight:600;paint-order:stroke;stroke:#f1f2f7;stroke-width:8px;stroke-linejoin:round}.et2{font-size:14px}
.mu{font-size:13px;font-weight:600;fill:var(--fg);paint-order:stroke;stroke:#f1f2f7;stroke-width:5px}
.ln{fill:none;stroke:var(--lin);stroke-width:1.5}.mk{fill:var(--lin)}.mkh{fill:var(--card);stroke:var(--lin);stroke-width:1.5}
.nodo,.trans,.mi{cursor:pointer;outline:none}
.mi .hit{fill:transparent}.mi:hover .hit{fill:var(--marksoft)}
.mi.sel .hit{fill:var(--mark)}.mi.sel .mb{font-weight:700}
.mi.q .hit{fill:#fde68a}.nodo.q>.box{stroke:var(--acc);stroke-width:2.5}
.mi:focus .hit{fill:var(--marksoft);stroke:var(--foco);stroke-width:2.5}
.nodo>.box{transition:stroke .12s}
.nodo:hover>.box{stroke:var(--acc);stroke-width:2}
.nodo.sel>.box{stroke:var(--acc);stroke-width:3}
.nodo:focus>.box{stroke:var(--foco);stroke-width:4}
.dim{opacity:.22}.dim.nodo:hover,.dim.nodo:focus{opacity:1}
path.ln.rel{stroke:var(--acc);stroke-width:2.6}
.trans:hover .ln,.trans.sel .ln{stroke:var(--acc);stroke-width:4}
.trans:focus .ln{stroke:var(--foco);stroke-width:4}
.trans:hover .et2,.trans:focus .et2,.trans.sel .et2{fill:var(--acc)}
.vs{opacity:0;pointer-events:none;cursor:pointer}
.vs rect{fill:var(--acc);stroke:var(--card);stroke-width:1.5}.vs text{fill:#fff;font:600 12px system-ui,sans-serif}
.vs:hover rect{fill:var(--accdk)}
.nodo:hover>.vs,.nodo:focus-within>.vs,.nodo.sel>.vs{opacity:1;pointer-events:auto}
.vs:focus-visible rect{stroke:var(--foco);stroke-width:3}
#der{display:flex;flex-direction:column;min-height:0;background:var(--card);box-shadow:-10px 0 30px rgba(23,26,35,.08);position:relative;z-index:1}
#panel{flex:1;overflow:auto;padding:20px 26px 32px}
#panel:focus{outline:3px solid var(--foco);outline-offset:-3px}
#panel h2{margin:2px 0 6px;font-size:24px;letter-spacing:-.015em;line-height:1.2}#panel h3{margin:22px 0 6px;font-size:15px;font-weight:700}
.mig{font-size:13px;color:var(--mut)}
.chip{display:inline-block;padding:1px 10px;border-radius:999px;background:var(--mark);color:var(--accdk);font-size:13px;font-weight:600;margin-right:6px}
.meta{color:var(--mut);font-size:14px;margin:0 0 8px}
.acciones{display:flex;flex-wrap:wrap;gap:8px;margin:8px 0 14px}
a.btn,button.btn{display:inline-flex;align-items:center;min-height:40px;padding:6px 18px;border-radius:10px;background:var(--acc);color:#fff;border:0;text-decoration:none;font-weight:600;box-shadow:0 1px 2px rgba(23,26,35,.25)}
a.btn:hover,button.btn:hover{background:var(--accdk)}
.doc{background:var(--marksoft);border-left:4px solid var(--acc);border-radius:0 10px 10px 0;padding:10px 14px;margin:0 0 14px;white-space:pre-wrap}
pre{background:var(--card);color:var(--fg);padding:10px 0;border-radius:12px;overflow:auto;font:13.5px/1.65 ui-monospace,"SF Mono",Menlo,Consolas,monospace;margin:0;box-shadow:var(--sh1);border:1px solid var(--pt)}
pre .l{display:block;padding:0 16px 0 0;white-space:pre}
pre .l::before{content:attr(data-n);display:inline-block;width:3.4em;padding-right:1em;margin-right:1em;text-align:right;color:#59627a;background:var(--gut);border-right:1px solid var(--pt);user-select:none}
.k{font-weight:700;color:var(--accdk)}.s{color:#14532d}.c{color:#59627a;font-style:italic}.d{color:#8a3b00}
.rels{list-style:none;margin:0;padding:0;display:grid;gap:6px}
.rels button{width:100%;display:flex;gap:10px;align-items:baseline;text-align:left;padding:8px 12px;border-radius:10px;border:1.5px solid var(--pt);background:var(--card);color:var(--fg)}
.rels button:hover{border-color:var(--acc);box-shadow:var(--sh1)}
.rels .v{color:var(--mut);font-size:14px}.rels .n{font-weight:700}.rels .c2{margin-left:auto;color:var(--mut);font-size:13px}
#estado{position:absolute;left:-9999px}
.vacio{color:var(--mut)}
#lista{max-width:780px}
.reglas{margin-bottom:22px}.reglas h2{font-size:20px;margin:0 0 4px}
.regla{background:var(--card);border-radius:14px;box-shadow:var(--sh1);padding:12px 18px;margin:10px 0;border-left:5px solid var(--acc)}
.regla h3{margin:0 0 4px;font-size:15px;display:flex;gap:10px;align-items:baseline}.regla .rid{font-size:20px;font-weight:800;color:var(--accdk)}.regla .fte{color:var(--mut);font-weight:500;font-size:14px}.regla a.sec{color:var(--accdk);font-weight:700;text-decoration:none;padding:1px 7px;border-radius:6px;background:var(--mark)}.regla a.sec:hover{background:var(--acc);color:#fff}
.regla p{margin:0 0 6px}.regla .rotulo{font-size:13px;color:var(--mut);font-weight:700;margin:6px 0 2px}
.chips{list-style:none;margin:0;padding:0;display:flex;flex-wrap:wrap;gap:4px 14px}.regla details{margin-top:4px}.regla summary{cursor:pointer;color:var(--mut);font-size:14px;font-weight:600}
#lista .cls{background:var(--card);border-radius:14px;box-shadow:var(--sh1);padding:10px 16px;margin-bottom:12px}#lista h3{margin:6px 0;font-size:17px}#lista h4{margin:8px 0 2px;font-size:14px;color:var(--mut)}
#lista ul{margin:0;padding-left:20px}.lk{background:none;border:0;padding:3px 8px;margin-left:-8px;border-radius:6px;color:var(--fg);text-align:left;text-decoration:none;font:13.5px ui-monospace,Menlo,monospace}
.lk:hover{color:var(--accdk);background:var(--marksoft)}
#lista h3 .lk{font:700 17px system-ui}#lista .btn{min-height:32px;font-size:14px;margin-left:8px}
@media(prefers-reduced-motion:no-preference){.vs{transition:opacity .12s}.dim,path.ln{transition:opacity .18s,stroke .18s}#panel>*{animation:entra .22s ease-out both}@keyframes entra{from{opacity:0;transform:translateY(6px)}}}
</style></head><body>
<a class="skip" href="#panel">Saltar al panel de código</a>
<header><h1>CRCE · modelo de dominio<small>Cada elemento está vinculado a su código real</small></h1>
<div role="tablist" aria-label="Vistas">
<button class="tab" role="tab" id="t-c" aria-controls="v-c" aria-selected="true">Modelo de clases</button>
<button class="tab" role="tab" id="t-e" aria-controls="v-e" aria-selected="false" tabindex="-1">Estados de la misión</button>
<button class="tab" role="tab" id="t-l" aria-controls="v-l" aria-selected="false" tabindex="-1">Vista en lista</button></div>
</header>
<main>
<section id="izq" aria-label="Diagrama">
<div class="barra" role="toolbar" aria-label="Zoom del diagrama">
<button class="tool" id="zm" aria-label="Alejar">−</button><span class="z" id="zv" aria-live="polite">100 %</span>
<button class="tool" id="zp" aria-label="Acercar">+</button>
<button class="tool" id="zf">Ajustar al ancho</button><button class="tool" id="z1">100 %</button>
<span class="sep2" aria-hidden="true"></span>
<input id="q" type="search" placeholder="Buscar clase o método" aria-label="Buscar clase, atributo u operación. Enter salta al primer resultado">
<button class="tool" id="sf" hidden>Quitar enfoque</button>
<span class="ayuda">Arrastrá para mover · Ctrl + rueda: zoom</span></div>
<div id="lienzo" tabindex="0" aria-label="Área del diagrama (desplazable)">
<div class="vista" id="v-c" role="tabpanel" aria-labelledby="t-c">@@CLASES@@</div>
<div class="vista" id="v-e" role="tabpanel" aria-labelledby="t-e" hidden>@@ESTADOS@@</div>
<div class="vista" id="v-l" role="tabpanel" aria-labelledby="t-l" hidden><div id="lista">@@LISTA@@</div></div>
</div></section>
<aside id="der" aria-label="Código del elemento seleccionado">
<div id="panel" tabindex="-1"><h2>Elegí un elemento</h2>
<p class="vacio">Clickeá (o con el teclado, Enter) una clase, un atributo, una operación, un estado o una flecha de transición para ver su código real.
Al pasar el mouse por una clase aparece la pestañita <strong>Ver en VS Code</strong>.</p>
<p class="meta">Teclado: Tab recorre las clases · ↓ entra a sus atributos y operaciones · ↑ ↓ se mueven · Enter muestra el código · V abre VS Code · Esc vuelve a la clase.</p>
<p class="meta">Encabezado oscuro = raíz de agregado · borde punteado = clase abstracta · ◆ composición · ▷ herencia · ⇢ dependencia.</p></div>
<div id="estado" role="status" aria-live="polite"></div></aside></main>
<script>
const D=@@DATOS@@;
const REL=@@REL@@;
const $=s=>document.querySelector(s),$$=s=>[...document.querySelectorAll(s)];
const panel=$('#panel'),estado=$('#estado');
const esc=s=>s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
function resaltar(c,n0){
 const re=/(#.*$)|(f?"[^"\n]*"|f?'[^'\n]*')|(^\s*@[\w.]+)|\b(class|def|return|raise|if|else|elif|for|in|not|and|or|is|None|True|False|from|import|self|with|lambda)\b/gm;
 let o='',u=0,m;while((m=re.exec(c))){o+=esc(c.slice(u,m.index));
  o+='<span class='+(m[1]?'c':m[2]?'s':m[3]?'d':'k')+'>'+esc(m[0])+'</span>';u=re.lastIndex}
 o+=esc(c.slice(u));
 return o.split('\n').map((l,i)=>'<span class="l" data-n="'+(n0+i)+'">'+(l||' ')+'</span>').join('')}
function vsc(d){return 'vscode://file/'+d.abs+':'+d.linea}
function bloque(k,titulo){const d=D[k];if(!d)return '<p class="vacio">No encontré '+esc(k)+' en el código.</p>';
 return '<h3>'+esc(titulo||d.titulo)+'</h3><p class="meta">'+esc(d.archivo)+' · líneas '+d.linea+'–'+d.fin+'</p>'+
 '<div class="acciones"><a class="btn" href="'+vsc(d)+'">Ver en VS Code ↗</a></div>'+
 (d.doc?'<div class="doc">'+esc(d.doc)+'</div>':'')+'<pre tabindex="0" aria-label="Código de '+esc(d.simbolo)+'">'+resaltar(d.codigo,d.linea)+'</pre>'}
function marcar(el){$$('.sel').forEach(x=>x.classList.remove('sel'));if(el)el.classList.add('sel')}
const reducido=matchMedia('(prefers-reduced-motion:reduce)').matches;
const claseDe=k=>k.split(/[.#]/)[0];
function limpiarEnfoque(){$$('#svgc .dim,#svgc .rel').forEach(e=>e.classList.remove('dim','rel'));$('#sf').hidden=true}
function enfocar(c){limpiarEnfoque();const nodo=$('#svgc .nodo[data-k="'+c+'"]');if(!nodo)return;
 const rel=new Set([c]);
 $$('#svgc [data-n]').forEach(e=>{const n=e.dataset.n.split(' '),on=n.includes(c);e.classList.toggle('rel',on&&e.tagName==='path');e.classList.toggle('dim',!on);if(on)n.forEach(x=>rel.add(x))});
 $$('#svgc .nodo').forEach(n=>n.classList.toggle('dim',!rel.has(n.dataset.k)));$('#sf').hidden=false}
function centrar(el){const r=el.getBoundingClientRect(),l=len.getBoundingClientRect();
 const arriba=r.height>l.height*.8?40:Math.max(40,(l.height-r.height)/2);
 len.scrollTo({left:len.scrollLeft+r.left-l.left-Math.max(30,(l.width-r.width)/2),top:len.scrollTop+r.top-l.top-arriba,behavior:reducido?'auto':'smooth'})}
addEventListener('message',e=>{const m=e.data||{};if(m.irAClase)irAClase(m.irAClase)});
addEventListener('keydown',e=>{if(e.target.closest&&e.target.closest('input,textarea'))return;if(e.key==='p'&&parent!==window)parent.postMessage({modo:'presentacion'},'*')});
function irAClase(c){irA($('#t-c'));const n=$('#svgc .nodo[data-k="'+c+'"]');if(!n)return;
 mostrar(n);centrar(n);n.focus({preventScroll:true})}
const TXT={a:'se asocia con',c:'contiene',d:'consulta a',h:'hereda de'};
function relaciones(c){const r=REL.filter(x=>x.o===c||x.d===c);if(!r.length)return '';
 return '<h3>Se relaciona con</h3><ul class="rels">'+r.map(x=>{const sale=x.o===c,otro=sale?x.d:x.o;
  const v=x.tipo==='h'?(sale?'hereda de':'es heredada por'):(sale?(x.et||TXT[x.tipo]):(x.et?x.et+' (entrante)':'recibe de'));
  const card=(x.mo||x.md)?(sale?x.mo+' → '+x.md:x.md+' ← '+x.mo):'';
  return '<li><button class="lk-rel" data-ir="'+esc(otro)+'"><span class="v">'+esc(v)+'</span><span class="n">'+esc(otro)+'</span><span class="c2">'+esc(card)+'</span></button></li>'}).join('')+'</ul>'}
function mostrar(el){
 marcar(el.closest('.mi,.trans,.nodo'));
 let h;
 if(el.dataset.k2!==undefined){const op=el.dataset.k.split('.')[1];
  h='<h2>Transición «'+esc(op)+'»</h2>'+bloque(el.dataset.k,'La misión delega en su estado (Mision.'+op+')')+bloque(el.dataset.k2,'El estado de origen decide ('+el.dataset.k2+')');
  estado.textContent='Mostrando la transición '+op}
 else{const k=el.dataset.k,d=D[k],c=claseDe(k),esCl=!/[.#]/.test(k),enDiag=!!$('#svgc .nodo[data-k="'+c+'"]');
  const tipo=k.includes('#')?'Atributo':k.includes('.')?'Operación':'Clase';
  const ruta=d?esc(d.archivo)+(enDiag?' › '+esc(c):'')+(esCl?'':' › '+esc(k.split(/[.#]/)[1])):'';
  h='<div class="mig">'+ruta+'</div><h2>'+esc(d?d.simbolo:k)+'</h2><div><span class="chip">'+tipo+'</span></div>'+bloque(k)+(enDiag?relaciones(c):'');
  estado.textContent='Mostrando el código de '+(d?d.titulo:k);
  if(enDiag)enfocar(c)}
 panel.innerHTML=h;panel.scrollTop=0}
document.addEventListener('click',e=>{
 if(e.target.closest('.vs'))return;
 const lk=e.target.closest('.lk');if(lk){mostrar({dataset:{k:lk.dataset.k},closest:()=>null});return}
 const ir=e.target.closest('[data-ir]');if(ir){irAClase(ir.dataset.ir);return}
 if(e.target.id==='sf'){limpiarEnfoque();marcar(null);return}
 const el=e.target.closest('.mi')||e.target.closest('.trans')||e.target.closest('.nodo');
 if(el&&!dragged){mostrar(el);return}
 if(!dragged&&e.target.closest('#svgc')&&e.target.closest('svg')===e.target){limpiarEnfoque();marcar(null)}});
function miembros(n){return [...n.querySelectorAll('.mi')]}
document.addEventListener('keydown',e=>{
 const t=e.target;
 if(e.key==='/'&&t.tagName!=='INPUT'){e.preventDefault();$('#q').focus();return}
 if(e.key==='Escape'&&(t.id==='q'||!$('#sf').hidden)&&!t.closest('.mi')){$('#q').value='';buscar('');limpiarEnfoque();marcar(null);return}
 if(t.closest&&t.closest('.vs'))return;
 const mi=t.closest&&t.closest('.mi'),nodo=t.closest&&t.closest('.nodo'),tr=t.closest&&t.closest('.trans');
 const cur=mi||tr||nodo;
 if(cur&&(e.key==='Enter'||e.key===' ')){e.preventDefault();mostrar(cur);return}
 if(cur&&(e.key==='v'||e.key==='V')){const d=D[cur.dataset.k];if(d){location.href=vsc(d)}return}
 if(mi){const l=miembros(nodo),i=l.indexOf(mi);
  if(e.key==='ArrowDown'){e.preventDefault();(l[i+1]||mi).focus()}
  else if(e.key==='ArrowUp'){e.preventDefault();(l[i-1]||nodo).focus()}
  else if(e.key==='Escape'||e.key==='ArrowLeft'){e.preventDefault();nodo.focus()}
  return}
 if(nodo&&e.key==='ArrowDown'){const l=miembros(nodo);if(l.length){e.preventDefault();l[0].focus()}return}
 if(t.tagName==='INPUT'||t.tagName==='BUTTON'&&e.key!=='+'&&e.key!=='-'&&e.key!=='0')return;
 if(e.key==='+'||e.key==='=')zoom(z*1.2);else if(e.key==='-')zoom(z/1.2);else if(e.key==='0')zoom(1)});
/* buscador */
function buscar(t){t=t.trim().toLowerCase();$$('#svgc .q').forEach(e=>e.classList.remove('q'));limpiarEnfoque();
 if(!t){estado.textContent='';return}
 const ms=$$('#svgc .mi').filter(m=>m.textContent.toLowerCase().includes(t)),ns=$$('#svgc .nodo').filter(n=>n.dataset.k.toLowerCase().includes(t));
 ms.forEach(m=>m.classList.add('q'));ns.forEach(n=>n.classList.add('q'));
 const keep=new Set([...ms.map(m=>m.closest('.nodo')),...ns]);
 $$('#svgc .nodo').forEach(n=>n.classList.toggle('dim',!keep.has(n)));$$('#svgc [data-n]').forEach(e=>e.classList.add('dim'));
 $('#sf').hidden=false;estado.textContent=(ms.length+ns.length)+' resultados para '+t}
$('#q').addEventListener('input',e=>{if($('#t-c').getAttribute('aria-selected')!=='true')irA($('#t-c'));buscar(e.target.value)});
$('#q').addEventListener('keydown',e=>{if(e.key==='Enter'){const p=$('#svgc .mi.q')||$('#svgc .nodo.q');if(p){mostrar(p);centrar(p.closest('.nodo')||p)}}});
/* zoom y arrastre */
let z=1;const len=$('#lienzo');
function svgActivo(){return $$('.vista:not([hidden]) svg.dg')[0]}
function zoom(v,centro){const s=svgActivo();if(!s)return;
 const a=z;z=Math.max(.3,Math.min(3,v));
 const cx=len.scrollLeft+len.clientWidth/2,cy=len.scrollTop+len.clientHeight/2;
 s.style.width=(+s.dataset.w*z)+'px';
 len.scrollLeft=cx*z/a-len.clientWidth/2;len.scrollTop=cy*z/a-len.clientHeight/2;
 $('#zv').textContent=Math.round(z*100)+' %'}
$('#zp').onclick=()=>zoom(z*1.2);$('#zm').onclick=()=>zoom(z/1.2);$('#z1').onclick=()=>zoom(1);
$('#zf').onclick=()=>{const s=svgActivo();if(s)zoom((len.clientWidth-30)/+s.dataset.w)};
len.addEventListener('wheel',e=>{if(e.ctrlKey||e.metaKey){e.preventDefault();zoom(e.deltaY<0?z*1.1:z/1.1)}},{passive:false});
let dragged=false,p0=null;
len.addEventListener('pointerdown',e=>{if(e.button!==0||e.target.closest('.nodo,.trans,.mi,.vs,button,a,pre'))return;
 p0={x:e.clientX,y:e.clientY,l:len.scrollLeft,t:len.scrollTop};dragged=false});
window.addEventListener('pointermove',e=>{if(!p0)return;
 const dx=e.clientX-p0.x,dy=e.clientY-p0.y;if(Math.abs(dx)+Math.abs(dy)>4){dragged=true;len.classList.add('arr')}
 if(dragged){len.scrollLeft=p0.l-dx;len.scrollTop=p0.t-dy}});
window.addEventListener('pointerup',()=>{p0=null;len.classList.remove('arr');setTimeout(()=>dragged=false,0)});
/* pestañas */
const tabs=$$('.tab');
function irA(t){tabs.forEach(b=>{const on=b===t;b.setAttribute('aria-selected',on);b.tabIndex=on?0:-1;
 $('#'+b.getAttribute('aria-controls')).hidden=!on});
 const s=svgActivo();$('.barra').style.display=s?'flex':'none';$('#q').hidden=t.id!=='t-c';if(t.id!=='t-c'){$('#q').value='';limpiarEnfoque()}if(s)zoom(z)}
tabs.forEach((b,i)=>{b.onclick=()=>irA(b);b.onkeydown=e=>{
 const j=e.key==='ArrowRight'?(i+1)%3:e.key==='ArrowLeft'?(i+2)%3:-1;if(j>=0){e.preventDefault();tabs[j].focus();irA(tabs[j])}}});
zoom(1);
</script></body></html>"""


def main():
    datos = {}
    cajas, colder = disenar(datos)
    for nom, (arch, sim, _) in CLASES.items():
        datos[sim] = codigo(arch, sim, f"Clase {nom}")
    pedidos = {c for c, *_ in ESTADOS.values()}
    for c in pedidos:
        datos[c] = codigo("dominio/mision.py", c, f"Estado {c}")
    for o, _, op in TRANSICIONES:
        datos[f"Mision.{op}"] = datos.get(f"Mision.{op}") or codigo("dominio/mision.py", f"Mision.{op}", f"Mision.{op}")
        datos[f"{ESTADOS[o][0]}.{op}"] = codigo("dominio/mision.py", f"{ESTADOS[o][0]}.{op}", f"{ESTADOS[o][0]}.{op}")
    faltan = [k for k, v in datos.items() if v is None]
    for k in faltan:
        print(f"AVISO: no encontré {k}")
        del datos[k]
    citas = citas_de_reglas(datos)
    rel = [dict(o=o, d=d, et=et, tipo=t, mo=mo, md=md) for o, _, _, d, _, _, _, et, t, mo, md in RELACIONES]
    rel += [dict(o=h, d=pa, et="hereda de", tipo="h", mo="", md="") for pa, hs in HERENCIA.items() for h in hs]
    out = (PLANTILLA.replace("@@REL@@", json.dumps(rel, ensure_ascii=False)).replace("@@CLASES@@", svg_clases(cajas, colder, datos))
           .replace("@@ESTADOS@@", svg_estados(datos)).replace("@@LISTA@@", vista_reglas(citas) + vista_lista(cajas, datos))
           .replace("@@DATOS@@", json.dumps(datos).replace("</", "<\\/")))
    destino = RAIZ / "docs" / "diagrama.html"
    destino.write_text(out, encoding="utf-8")
    print(f"Listo: {destino} ({len(datos)} elementos vinculados)")
    if not (RAIZ / "docs" / ENUNCIADO).exists():
        print(f"AVISO: falta docs/{ENUNCIADO}. Copiá ahí el PDF del enunciado para que los enlaces de sección lo abran.")


if __name__ == "__main__":
    main()
