"""Recorrido general del backend: las seis preguntas, con datos reales del proyecto.

Qué problema resuelve · cómo está organizado · clases y componentes · cómo se comunican ·
cómo se procesan los datos · qué conceptos de POO se aplican y para qué (+ pruebas y preguntas).

Lo que se puede medir se mide sobre el código (módulos, errores, operaciones, pruebas, dependencias)
y lo que se muestra como «ejemplo real» se ejecuta con el dominio de verdad al generar la página.
"""
import ast
import html
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))


def esc(t):
    return html.escape(str(t), quote=False)


def code(t):
    return f"<code>{esc(t)}</code>"


def tags(lista, extra=""):
    return "".join(f'<span class="tag{extra}">{esc(t)}</span>' for t in lista)


# ───────────────────────── datos medidos sobre el código ─────────────────────────

CAPAS = [  # de abajo hacia arriba
    ("Base", ["catalogos", "errores", "valores", "historial"], "listas cerradas, errores, validaciones y registro"),
    ("Recursos", ["personal", "equipamiento", "vehiculos", "distribucion"], "lo que tiene una unidad"),
    ("Unidad y misión", ["unidad", "mision"], "se verifican entre sí"),
    ("Coordinación", ["aviso", "emergencia", "flota"], "procesos completos y consistencia"),
]
CAPA_DE = {m: i for i, (_, ms, _) in enumerate(CAPAS) for m in ms}

PRUEBAS = {  # respaldo si no se puede ejecutar pytest al generar (verificado: 204)
    "test_avisos.py": 18, "test_avisos_robustez.py": 15, "test_evaluacion_avisos.py": 19,
    "test_recursos.py": 31, "test_asignacion.py": 26, "test_ejecucion.py": 29,
    "test_emergencias.py": 37, "test_diseno.py": 29,
}
DESC_PRUEBAS = {
    "test_avisos.py": "Reglas R1 a R6 del aviso: cada prueba nombra la regla",
    "test_avisos_robustez.py": "Datos que nacen juntos y estado coherente",
    "test_evaluacion_avisos.py": "Aceptar origina una única emergencia; descartar",
    "test_recursos.py": "Personal, vehículos, equipos, unidades y flota",
    "test_asignacion.py": "Las condiciones de la unidad al asignar, en orden",
    "test_ejecucion.py": "Rechazar, iniciar, novedades, finalizar, reasignar y cancelar",
    "test_emergencias.py": "Prioridad, misiones, cierre e historial",
    "test_diseno.py": "Reglas de diseño sobre el código: sin isinstance ni type, solo biblioteca estándar, sin datetime.now",
}


def _correr_pruebas():
    """Ejecuta pytest de verdad: pruebas por archivo y cómo terminaron (None si no se pudo ejecutar)."""
    try:
        r = subprocess.run([sys.executable, "-m", "pytest", "-v", "-p", "no:cacheprovider", "-o", "addopts="], cwd=RAIZ,
                           capture_output=True, text=True, timeout=300)
        cuentas, resultados = defaultdict(int), defaultdict(int)
        for linea in r.stdout.splitlines():
            m = re.match(r"tests/(test_\w+\.py)::\S.*?\s(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS)\b", linea)
            if m:
                cuentas[m.group(1)] += 1
                resultados[m.group(2)] += 1
        if cuentas and set(cuentas) == set(PRUEBAS):
            return dict(cuentas), dict(resultados)
    except (OSError, subprocess.SubprocessError):
        pass
    print("AVISO: no pude ejecutar pytest; la diapositiva de pruebas no afirma el resultado (usá `uv run pytest`).")
    return dict(PRUEBAS), None


def medir():
    """Datos que se leen del código real."""
    from dominio import catalogos, historial
    modulos = sorted(p.stem for p in (RAIZ / "dominio").glob("*.py") if p.stem != "__init__")
    deps, solo_tipos = {}, set()
    for m in modulos:
        arbol = ast.parse((RAIZ / "dominio" / f"{m}.py").read_text(encoding="utf-8"))
        tipos = {n for nodo in ast.walk(arbol) if isinstance(nodo, ast.If)
                 and "TYPE_CHECKING" in ast.dump(nodo.test) for n in ast.walk(nodo)}
        reales = set()
        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.ImportFrom) and (nodo.module or "").startswith("dominio."):
                destino = nodo.module.split(".")[1]
                if nodo in tipos:
                    solo_tipos.add((m, destino))
                else:
                    reales.add(destino)
        deps[m] = reales
    # lo que se afirma de las capas se comprueba: nadie importa (de verdad) hacia arriba
    for m, ds in deps.items():
        for d in ds:
            assert CAPA_DE[d] <= CAPA_DE[m], f"{m} importa {d}, que está en una capa superior"
    errores = ast.parse((RAIZ / "dominio" / "errores.py").read_text(encoding="utf-8"))
    n_errores = sum(isinstance(n, ast.ClassDef) for n in errores.body)
    n_catalogos = sum(1 for n in vars(catalogos).values()
                      if isinstance(n, type) and issubclass(n, catalogos.Catalogo) and n is not catalogos.Catalogo)
    por_archivo, resultado = _correr_pruebas()
    return dict(modulos=modulos, deps=deps, solo_tipos=solo_tipos, n_errores=n_errores, n_catalogos=n_catalogos,
                n_operaciones=len(historial.Operacion), pruebas=por_archivo, n_pruebas=sum(por_archivo.values()),
                resultado_pruebas=resultado)


def ejemplo_aceptar():
    """Ejecuta el dominio de verdad: un aviso mal clasificado que el operador corrige al aceptarlo."""
    from dominio.aviso import Aviso
    from dominio.catalogos import Gravedad, TipoSituacion
    from dominio.errores import ErrorDeDominio
    from dominio.valores import Ubicacion
    reportado = datetime(2026, 11, 20, 10, 0)
    aceptado = datetime(2026, 11, 20, 10, 5)
    aviso = Aviso("rep-7", Ubicacion("Av. Colón 1200", "Córdoba"), TipoSituacion.INUNDACION, Gravedad.MEDIA,
                  "Agua hasta la vereda", reportado, aviso_id="av-1")
    tipo0, grav0 = aviso.tipo.value, aviso.gravedad_estimada.name.lower()
    ops_antes = [r.operacion.value for r in aviso.registros]
    emergencia = aviso.aceptar("op-1", TipoSituacion.INCENDIO, Gravedad.ALTA, aceptado)
    ops_aviso = [r.operacion.value for r in aviso.registros]
    try:
        aviso.aceptar("op-2", TipoSituacion.INCENDIO, Gravedad.ALTA, aceptado)
        rechazo = ("(no falló)", "")
    except ErrorDeDominio as e:
        rechazo = (type(e).__name__, str(e))
    # lo que afirma la diapositiva, comprobado contra el dominio real
    assert (aviso.tipo.value, aviso.gravedad_estimada.name.lower()) == (tipo0, grav0), "el aviso debe conservar lo reportado"
    assert [r.operacion.value for r in aviso.registros] == ops_aviso, "el segundo intento no debe agregar registros"
    assert len(ops_aviso) == len(ops_antes) + 1 and rechazo[0] == "AvisoNoPendiente"
    return dict(aviso_estado=aviso.estado.value, tipo0=tipo0, grav0=grav0,
                em_tipo=emergencia.tipo.value, em_gravedad=emergencia.gravedad.name.lower(), em_estado=emergencia.estado.value,
                aviso_ops=ops_aviso, em_ops=[r.operacion.value for r in emergencia.registros], rechazo=rechazo)


# ───────────────────────── diapositivas ─────────────────────────

def _flow(items):
    partes = []
    for i, x in enumerate(items):
        if i:
            partes.append('<span class="arrow">→</span>')
        partes.append(f'<div class="node">{esc(x)}</div>')
    return f'<div class="flow">{"".join(partes)}</div>'


def s_problema(m):
    return dict(eyebrow="01 · el problema que resuelve", titulo="Un centro que recibe avisos y decide quién responde", grande=True, html=f"""
<p class="lead">El CRCE recibe avisos de <strong>inundaciones, incendios y accidentes viales</strong>. Sus operadores los evalúan,
registran las emergencias y organizan <strong>misiones</strong> (evacuación, rescate o asistencia sanitaria) con las
<strong>unidades</strong> de sus bases operativas.</p>
{_flow(["Aviso", "Emergencia", "Misión", "Unidad"])}
<div class="callout">El backend es el <strong>núcleo de reglas</strong>: decide qué operaciones están permitidas, con qué recursos,
y deja constancia de cada una. No es una API ni un servidor: es un <strong>dominio en Python puro</strong>, sin librerías externas.</div>""")


def s_garantias(m):
    reglas = [
        ("Un aviso se evalúa una sola vez", "Nace pendiente. Aceptarlo origina una emergencia; descartarlo exige justificación. Después no admite más cambios.", ["Aviso", "State"]),
        ("Una unidad atiende solo lo que puede", "Debe estar habilitada, libre y tener el vehículo, el personal y el equipo que pide ese tipo de misión.", ["Unidad", "Mision"]),
        ("Nada está en dos lugares a la vez", "Una persona, un vehículo o un equipo pertenece a una sola unidad. Lo controla la Flota, porque una unidad sola no conoce a las demás.", ["Flota"]),
        ("Una emergencia se cierra con criterio", "Sin misiones sin concluir y con al menos una misión exitosa.", ["Emergencia"]),
        ("Todo deja constancia", "Cada operación relevante genera un Registro inmutable: quién, cuándo, qué y sobre qué.", ["Registro"]),
        ("Si falla, nada cambia", "Se valida y se arma todo antes de modificar: un rechazo no deja objetos a medio cambiar.", ["Fallar antes de modificar"]),
    ]
    cards = "".join(f'<div class="card"><h3>{esc(t)}</h3><p class="explain">{esc(d)}</p><div>{tags(g)}</div></div>' for t, d, g in reglas)
    return dict(eyebrow="01 · el problema que resuelve", titulo="Qué reglas hace cumplir el backend", html=f'<div class="grid3">{cards}</div>')


def s_repo(m):
    n_mod = len(m["modulos"])
    arbol = (f"ProyectoFinal-PP5/\n"
             f"├─ pyproject.toml    Python ≥ 3.13 · sin dependencias\n"
             f"├─ dominio/          {n_mod} módulos: el backend\n"
             f"├─ tests/            {len(m['pruebas'])} archivos · {m['n_pruebas']} pruebas\n"
             f"└─ docs/             presentación y diagramas,\n"
             f"                     generados del código real")
    return dict(eyebrow="02 · cómo está organizado", titulo="Un dominio, sus pruebas y la documentación", html=f"""
<div class="grid">
 <div class="card"><h3>El repositorio</h3><pre class="mini">{esc(arbol)}</pre></div>
 <div class="card"><h3>Qué hay y qué no hay</h3>
  <ul><li>Solo biblioteca estándar: lo verifica <code>test_diseno.py</code>.</li>
  <li><strong>pytest</strong> es la única dependencia, y solo para desarrollo.</li>
  <li>Cada módulo concentra una parte del problema; colaboran importándose entre sí.</li>
  <li>No hay servidor, base de datos ni interfaz en esta entrega: el alcance es el <strong>dominio y sus reglas</strong>. La persistencia y la API se construyen encima; <code>Aviso.restaurar</code> ya reconstruye un aviso guardado.</li></ul>
  <div class="callout">Las fechas entran como parámetro: el dominio nunca consulta el reloj, así las pruebas dan siempre el mismo resultado.</div></div>
</div>""")


def s_capas(m):
    filas = []
    for i in range(len(CAPAS) - 1, -1, -1):
        nombre, mods, desc = CAPAS[i]
        chips = "".join(f'<span class="mod">{esc(x)}</span>' for x in mods)
        filas.append(f'<div class="capa c{i}"><div class="cn"><b>{esc(nombre)}</b><small>{esc(desc)}</small></div><div class="cm">{chips}</div></div>')
    return dict(eyebrow="02 · cómo está organizado", titulo="Cada módulo solo conoce a los de su nivel o a los de abajo", html=f"""
<div class="capas">{"".join(filas)}</div>
<div class="callout"><strong>Unidad y Misión</strong> se necesitan: Misión importa a Unidad, y Unidad solo nombra a Misión para anotar tipos
(<code>TYPE_CHECKING</code>). En ejecución no hay ciclos de importación.</div>""")


def s_piezas(m):
    piezas = [
        ("Aviso", "entidad · State", "Registra lo que informa un reportante y se evalúa una sola vez.", "ubicación, tipo, gravedad estimada, notas, descarte"),
        ("Emergencia", "raíz de agregado · State", "Nace al aceptar un aviso. Coordina sus misiones y decide el cierre.", "tipo y gravedad confirmados, misiones"),
        ("Mision", "abstracta · State", "Un trabajo concreto para una unidad. Declara qué pide y cómo avanza.", "objetivo, estado, unidad asignada, novedades, resultado"),
        ("Unidad", "entidad · composición", "Jefe, personal, vehículo y equipo. Se compromete con una misión a la vez.", "dotación, vehículo, equipo, condición, misión"),
        ("Flota", "raíz de consistencia", "Conoce bases y unidades y evita que un recurso esté en dos unidades.", "bases y unidades"),
        ("Registro", "valor inmutable", "La constancia de cada operación: quién, cuándo, qué y sobre qué.", "actor, fecha, operación, recursos, detalle"),
    ]
    cards = "".join(
        f'<div class="card pieza"><h3><code>{n}</code></h3><span class="rol">{esc(r)}</span><p class="explain">{esc(d)}</p>'
        f'<p class="guarda"><b>Guarda:</b> {esc(g)}</p></div>' for n, r, d, g in piezas)
    return dict(eyebrow="03 · clases y componentes principales", titulo="Seis piezas llevan el negocio", html=f'<div class="grid3">{cards}</div>')


def s_resto(m):
    return dict(eyebrow="03 · clases y componentes principales", titulo="Lo que rodea a esas piezas", html=f"""
<div class="grid3">
 <div class="card"><h3>Recursos</h3>
  <ul><li><code>Persona</code>: competencias</li><li><code>Equipo</code>: categoría y condición</li>
  <li><code>Vehiculo</code> (abstracto): <code>TransportePersonas</code>, <code>VehiculoRescate</code>, <code>Ambulancia</code></li>
  <li><code>BaseOperativa</code>: dónde están las unidades</li></ul></div>
 <div class="card"><h3>Valores inmutables</h3>
  <p class="explain"><code>Ubicacion</code>, <code>Nota</code>, <code>Descarte</code>, <code>Novedad</code>, <code>Resultado</code>, <code>Registro</code> y <code>VistaMision</code>.</p>
  <p class="explain">Con <code>frozen=True</code> no se pueden modificar una vez validados.</p></div>
 <div class="card"><h3>Estados y soporte</h3>
  <ul><li><strong>13 estados</strong>: aviso (3), misión (5), emergencia (2) y condición de la unidad (3)</li>
  <li><code>_SinUnidad</code> / <code>_ConUnidad</code>: la unidad asignada</li>
  <li><strong>{m['n_catalogos']} catálogos</strong> Enum y <strong>{m['n_errores']} errores</strong> propios</li>
  <li><code>existe_distribucion()</code>: personas distintas por puesto</li></ul></div>
</div>""")


def s_mapa(m):
    return dict(eyebrow="04 · cómo se comunican", titulo="Quién le habla a quién", clase="Emergencia", html="""
<div class="mapa">
 <div class="nodo"><b>Aviso</b><small>entidad</small></div>
 <div class="lk"><span>origina</span><i>→</i></div>
 <div class="nodo"><b>Emergencia</b><small>raíz de agregado</small></div>
 <div class="lk"><span>contiene</span><i>→</i></div>
 <div class="nodo"><b>Mision</b><small>abstracta</small></div>
 <div class="lk"><span>asignada a</span><i>→</i></div>
 <div class="nodo"><b>Unidad</b><small>entidad</small></div>
 <div class="lk"><span>agrupa</span><i>←</i></div>
 <div class="nodo"><b>Flota</b><small>raíz de consistencia</small></div>
 <div class="abajo a3"><i>↑</i><span>historial</span><div class="nodo chico"><b>Registro</b><small>lo generan Aviso, Emergencia y Unidad</small></div></div>
 <div class="abajo a5"><i>↑</i><span>doble despacho</span><div class="nodo chico"><b>Vehiculo</b><small>responde si sirve</small></div></div>
 <div class="abajo a7"><i>↑</i><span>se compone de</span><div class="nodo chico"><b>Persona · Equipo</b><small>y el Vehiculo</small></div></div>
</div>
<div class="callout">Se hablan con <strong>mensajes</strong> (métodos), no con consultas de tipo. La Emergencia guarda el
<strong>id</strong> del aviso de origen (<code>aviso_id</code>), no una referencia a su objeto.</div>""")


def s_asignar(m):
    filas = [
        (0, "Operador", "op", "Emergencia.asignar_mision(mision_id, unidad, operador_id, fecha_hora)", "pide la asignación"),
        (1, "Emergencia", "em", "_estado.permitir_modificaciones()", "¿sigue abierta?"),
        (1, "Emergencia", "em", "Registro.de(…, Operacion.MISION_ASIGNADA, …)", "arma el registro, sin guardarlo"),
        (1, "Mision", "mi", "asignar(unidad)", "la emergencia delega"),
        (2, "Mision", "mi", "_estado.asignar()", "¿está pendiente?"),
        (2, "Unidad", "un", "comprometer(mision)", "verifica todo, en orden"),
        (3, "Unidad", "un", "_condicion.verificar_habilitada()  ·  _mision_id is None", "¿habilitada y libre?"),
        (3, "Vehiculo", "ve", "verificar_operativo()", "¿el vehículo sirve?"),
        (3, "Mision", "mi", "verificar_vehiculo(v)  →  v.verificar_rescate()", "doble despacho: el vehículo responde"),
        (3, "Mision", "mi", "verificar_personal(p)  →  existe_distribucion(puestos, p)", "personas distintas por puesto"),
        (3, "Mision", "mi", "verificar_equipamiento(unidad)", "el equipo operativo que pide"),
        (3, "Unidad", "un", "_mision_id = mision.id", "recién ahora se reserva"),
        (2, "Mision", "mi", "_asignacion y _estado cambian", "recién ahora cambia la misión"),
        (1, "Emergencia", "em", "_registros.append(registro)", "y queda el registro"),
    ]
    html_filas = "".join(
        f'<div class="q" style="--d:{d}"><span class="a {c}">{esc(a)}</span><code>{esc(t)}</code><em>{esc(n)}</em></div>'
        for d, a, c, t, n in filas)
    return dict(eyebrow="04 · cómo se comunican", titulo="Asignar una misión: la cadena de mensajes", clase="Mision", html=f"""
<div class="seq">{html_filas}</div>
<div class="callout">Si cualquier verificación lanza un error, la cadena se corta y <strong>nadie había cambiado nada</strong>:
primero se pregunta, y solo al final se modifica.</div>""")


def s_reglas_com(m):
    reglas = [
        ("Se pide, no se pregunta", "La misión no consulta de qué tipo es el vehículo: le dice «verificá» y el vehículo responde. Por eso el dominio no usa isinstance ni type.", ["Polimorfismo", "Doble despacho"]),
        ("Cada objeto cuida lo suyo", "Los datos salen como ids, tuplas o vistas de solo lectura. La emergencia entrega sus misiones como VistaMision: una foto que no se puede modificar, así nadie se saltea a la emergencia (por ejemplo, cancelando la misión desde afuera).", ["Encapsulamiento"]),
        ("La regla vive donde están los datos", "La unicidad entre unidades la cuida la Flota; el cierre lo cuida la Emergencia; qué pide cada misión, la Mision.", ["Raíz de agregado", "Responsabilidad"]),
        ("Todo hecho deja un Registro", "Aviso, Emergencia y Unidad arman un Registro por cada operación: quién, cuándo, qué y sobre qué recursos.", ["Trazabilidad"]),
    ]
    cards = "".join(f'<div class="card"><h3>{esc(t)}</h3><p class="explain">{esc(d)}</p><div>{tags(g)}</div></div>' for t, d, g in reglas)
    return dict(eyebrow="04 · cómo se comunican", titulo="Cuatro reglas de la comunicación", html=f'<div class="grid">{cards}</div>')


def s_camino(m):
    etapas = [("Entra", "parámetros simples: ids (str), catálogos (Enum) y la fecha (datetime) que llega de afuera"),
              ("Decide", "el estado (State) dice si la operación es posible"),
              ("Valida y construye", "los valores y objetos nuevos se arman y se validan sin tocar nada"),
              ("Confirma", "recién ahora se modifican los atributos y se agrega el registro"),
              ("Devuelve", "se entrega el resultado; lo demás se lee con propiedades de solo lectura, tuplas o vistas")]
    pipe = "".join(f'<div class="et"><b>{i + 1}</b><span>{esc(t)}</span></div>' + ('<span class="arrow">→</span>' if i < 4 else "")
                   for i, (t, _) in enumerate(etapas))
    lineas = [
        (1, "def aceptar(self, operador_id, tipo, gravedad, fecha_hora)"),
        (2, "siguiente = self._estado.aceptar()"),
        (3, "emergencia = Emergencia(self._id, …, operador_id)"),
        (3, "registro = Registro.de(operador_id, fecha_hora, Operacion.AVISO_ACEPTADO, …)"),
        (4, "self._estado = siguiente"),
        (4, "self._registros.append(registro)"),
        (5, "return emergencia"),
    ]
    cod = "".join(f'<div class="cl e{e}"><b>{e}</b><code>{esc(t)}</code></div>' for e, t in lineas)
    detalle = "".join(f'<li><b>{i + 1} · {esc(t)}:</b> {esc(d)}</li>' for i, (t, d) in enumerate(etapas))
    return dict(eyebrow="05 · cómo se procesan los datos", titulo="El camino de un dato: de la entrada al resultado", clase="Aviso", html=f"""
<div class="pipe">{pipe}</div>
<div class="grid">
 <div class="card"><h3>Aviso.aceptar(), resumido del código</h3><div class="codigo2">{cod}</div></div>
 <div class="card"><h3>Qué pasa en cada etapa</h3><ul class="etapas">{detalle}</ul></div>
</div>""")


def s_ejemplo(e):
    nombre, mensaje = e["rechazo"]

    def ops(lista):
        return ", ".join(f"<code>{esc(o)}</code>" for o in lista)
    n, k = len(e["aviso_ops"]), len(e["em_ops"])
    return dict(eyebrow="05 · cómo se procesan los datos", titulo="Ejemplo real: aceptar un aviso, etapa por etapa", clase="Aviso", html=f"""
<p class="lead corto">Un vecino reportó una <strong>inundación</strong> de gravedad media, pero el operador comprueba que es un
<strong>incendio</strong> grave. Así lo procesa <code>Aviso.aceptar()</code>, con las mismas cinco etapas del camino de un dato.</p>
<div class="ej">
 <div class="ets">
  <div class="ep"><b>1</b><div><p><span class="t">Entra:</span> el operador <code>op-1</code> acepta el aviso <code>av-1</code> y corrige su clasificación.</p>
   <pre class="mini">aviso.aceptar("op-1", TipoSituacion.INCENDIO,
              Gravedad.ALTA, fecha_hora)</pre></div></div>
  <div class="ep e2"><b>2</b><p><span class="t">Decide:</span> su estado es <strong>pendiente</strong>, así que permite aceptarlo.</p></div>
  <div class="ep e3"><b>3</b><p><span class="t">Valida y construye:</span> crea la <strong>Emergencia</strong> con los datos confirmados y arma el <strong>Registro</strong>.
   Si algo fuera inválido, falla acá y el aviso sigue intacto.</p></div>
  <div class="ep e4"><b>4</b><p><span class="t">Confirma:</span> recién ahora el aviso pasa a <strong>{esc(e['aviso_estado'])}</strong> y guarda su registro.</p></div>
  <div class="ep e5"><b>5</b><p><span class="t">Devuelve:</span> la emergencia nueva, <strong>{esc(e['em_estado'])}</strong>.</p></div>
 </div>
 <div class="card"><h3>Qué queda</h3>
  <ul>
   <li>Aviso <code>av-1</code>: <strong>{esc(e['aviso_estado'])}</strong>. Conserva lo que se reportó (<code>{esc(e['tipo0'])}&nbsp;·&nbsp;{esc(e['grav0'])}</code>).</li>
   <li>Emergencia <code>em-1</code>: <strong>{esc(e['em_estado'])}</strong>, con lo confirmado (<code>{esc(e['em_tipo'])}&nbsp;·&nbsp;{esc(e['em_gravedad'])}</code>).</li>
   <li>Registros: el aviso tiene {n} ({ops(e['aviso_ops'])}) y la emergencia, {k} ({ops(e['em_ops'])}).</li>
  </ul>
  <p class="muted chica"><code>em-1</code> abrevia el id de la emergencia: lo genera el sistema (UUID).</p></div>
</div>
<div class="card err banda"><div><h3>Segundo intento</h3>
 <p class="explain">Otro operador intenta aceptar el mismo aviso y la etapa 2 lo corta. No se crea otra emergencia y
 <strong>el aviso no cambia</strong>: sigue con {n} registros.</p></div>
 <pre class="mini">{esc(nombre)}:
«{esc(mensaje)}»</pre></div>""")


def s_vida(m):
    def st(x):
        return f'<span class="st">{esc(x)}</span>'

    def ar(x):
        return f'<span class="ar">{esc(x)} →</span>'
    filas = [
        ("Aviso", "operador", f"{st('pendiente')}{ar('aceptar')}{st('aceptado')}<span class='o'>o</span>{ar('descartar')}{st('descartado')}", ""),
        ("Emergencia", "supervisor", f"{st('abierta')}{ar('cerrar')}{st('cerrada')}", "solo si todas las misiones concluyeron y alguna fue exitosa"),
        ("Misión", "operador y jefe", f"{st('pendiente')}{ar('asignar')}{st('asignada')}{ar('iniciar')}{st('en ejecución')}{ar('finalizar')}{st('finalizada')}",
         "además: reasignar (sigue asignada) · rechazar (vuelve a pendiente) · cancelar (desde pendiente o asignada)"),
        ("Unidad", "quien la administra", f"{st('habilitada')}<span class='o'>·</span>{st('en mantenimiento')}<span class='o'>·</span>{st('fuera de servicio')}",
         "se cambia con declarar_en_mantenimiento(), declarar_fuera_de_servicio() y restablecer_servicio(); estar comprometida con una misión es otro dato"),
    ]
    html_filas = "".join(
        f'<div class="vida"><div class="vn"><b>{n}</b><small>{esc(q)}</small></div><div class="cad">{c}</div>'
        + (f'<p class="nota-v">{esc(x)}</p>' if x else "") + "</div>" for n, q, c, x in filas)
    return dict(eyebrow="05 · cómo se procesan los datos", titulo="Cómo cambian los datos: el ciclo de vida", clase="Mision", html=f"""
{html_filas}
<div class="callout">En el aviso, la emergencia y la misión, cada flecha es una operación que primero consulta al estado actual: lo que no figura se rechaza.</div>""")


POO1 = [
    ("Encapsulamiento", "atributos privados (<code>_estado</code>, <code>_misiones</code>), propiedades de solo lectura, tuplas", "Nadie cambia un objeto desde afuera: solo él decide cómo y cuándo cambia."),
    ("Abstracción", "<code>Mision</code>, <code>Vehiculo</code> y los estados (ABC con <code>@abstractmethod</code>)", "Fijan qué se puede pedir sin decir cómo. No existen «misiones genéricas»."),
    ("Herencia", "tres tipos de misión, tres categorías de vehículo, la familia de errores", "Reutilizar lo común y especializar lo propio."),
    ("Polimorfismo", "<code>mision.verificar_vehiculo(v)</code>, <code>estado.aceptar()</code>", "Mismo mensaje, respuesta según la clase: se evita preguntar por el tipo (sin <code>isinstance</code>)."),
    ("Composición", "<code>Unidad</code> (jefe, personal, vehículo, equipo), <code>Flota</code>, <code>Emergencia</code>", "Los objetos grandes se arman con objetos chicos y les delegan."),
    ("Delegación y doble despacho", "<code>Mision</code> → <code>vehiculo.verificar_*()</code>, <code>unidad.comprometer(mision)</code>", "La misión sabe qué pide y el vehículo qué puede: cada uno resuelve lo suyo."),
    ("Raíz de agregado", "<code>Emergencia</code> (misiones), <code>Flota</code> (unidades)", "Un solo punto de entrada que garantiza la consistencia de lo que contiene."),
]


def poo_html(filas):
    return '<div class="poo">' + "".join(
        f'<div class="fila"><span class="cp">{esc(c)}</span><span class="dn">{d}</span><span class="pq">{p}</span></div>' for c, d, p in filas) + "</div>"


def s_poo1(m):
    return dict(eyebrow="06 · conceptos de POO y para qué", titulo="Los conceptos que organizan el modelo", html=poo_html(POO1))


def s_poo2(m):
    filas = [
        ("State", "estados de Aviso, Mision y Emergencia; <code>_Condicion</code> de Unidad", "Cada estado decide qué operaciones admite: no hay un if por estado en cada método, y agregar un estado es agregar una clase."),
        ("Null Object", "<code>_SinUnidad</code> / <code>_ConUnidad</code> en la misión", "Evita None y comprobaciones: una misión sin unidad responde igual que una con unidad."),
        ("Objetos valor inmutables", "<code>Ubicacion</code>, <code>Nota</code>, <code>Persona</code>, <code>Registro</code> (<code>frozen=True</code>)", "Valores que no se alteran una vez validados; el historial no se reescribe."),
        ("Fallar antes de modificar", "<code>descartar</code>, <code>aceptar</code>, <code>comprometer</code>, <code>incorporar_unidad</code>", "Si algo falla, el objeto queda como estaba: se valida y arma todo antes del primer cambio."),
        ("Excepciones propias", f"<code>ErrorDeDominio</code> y {m['n_errores'] - 1} derivados; <code>UnidadOcupada</code> con herencia múltiple", "El motivo del rechazo viaja en el tipo del error."),
        ("Catálogos cerrados", f"{m['n_catalogos']} clases <code>Enum</code> sobre <code>Catalogo</code>", "Un valor fuera de la lista no se puede construir."),
        ("Dominio puro y verificable", "fechas por parámetro, solo biblioteca estándar, <code>test_diseno.py</code>", "Pruebas repetibles, sin reloj ni librerías, y el diseño se vigila con tests."),
    ]
    return dict(eyebrow="06 · conceptos de POO y para qué", titulo="Patrones y decisiones de diseño", html=poo_html(filas))


def s_pruebas(m):
    filas = "".join(
        f'<div class="fila"><code>{a}</code><span>{esc(DESC_PRUEBAS[a])}</span><b>{m["pruebas"][a]}</b></div>' for a in DESC_PRUEBAS)
    n, res = m["n_pruebas"], m["resultado_pruebas"]
    if res is None:      # no se pudo ejecutar pytest al generar: no se afirma nada
        resultado = '<div class="card"><h3>Para comprobarlo</h3><p class="explain">Ejecutá <code>uv run pytest</code>.</p></div>'
    elif res.get("FAILED", 0) + res.get("ERROR", 0) == 0 and res.get("PASSED", 0) == n:
        resultado = (f'<div class="card ok"><div class="gran">✔</div><h3>Pruebas exitosas</h3>'
                     f'<p class="explain"><strong>{n} de {n}</strong> pasaron.</p></div>')
    else:
        malas = n - res.get("PASSED", 0)
        resultado = (f'<div class="card err"><h3>Hay pruebas que no pasan</h3>'
                     f'<p class="explain"><strong>{malas} de {n}</strong> no pasaron: revisá <code>uv run pytest</code>.</p></div>')
    return dict(eyebrow="07 · cómo se verifica", titulo=f"{n} pruebas comprueban comportamiento y diseño", html=f"""
<div class="grid pr">
 <div class="card"><h3>Qué prueba cada archivo</h3><div class="pruebas">{filas}</div></div>
 {resultado}
</div>""")


def slides_generales():
    m = medir()
    e = ejemplo_aceptar()
    return [s_problema(m), s_garantias(m), s_repo(m), s_capas(m), s_piezas(m), s_resto(m), s_mapa(m), s_asignar(m),
            s_reglas_com(m), s_camino(m), s_ejemplo(e), s_vida(m), s_poo1(m), s_poo2(m), s_pruebas(m)], m


if __name__ == "__main__":
    s, m = slides_generales()
    print(len(s), "diapositivas", {k: v for k, v in m.items() if k not in ("deps", "modulos")})
