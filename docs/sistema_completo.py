"""Sección «Sistema completo»: lo que rodea al dominio para la entrega final, y la interfaz en uso.

Dos grupos del menú:
1. Plataforma: qué exige la entrega final y dónde se cumple, Keycloak, Docker, configuración, API y pruebas.
2. La interfaz en uso: el recorrido de PV19 con capturas reales, paso por paso.

Las capturas están en docs/img/sistema/ (GitHub Pages las sirve junto a la página).
"""
import html
import re

IMG = "img/sistema/"


def esc(t):
    return html.escape(str(t), quote=False)


def md(t):
    t = esc(t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    return re.sub(r"`(.+?)`", r"<code>\1</code>", t)


def foto(archivo, alt, pie=None, clase=""):
    pie_html = f"<figcaption>{md(pie)}</figcaption>" if pie else ""
    return (f'<figure class="sc-foto {clase}"><img src="{IMG}{archivo}" alt="{esc(alt)}" loading="lazy" '
            f'tabindex="0" title="Clic para ampliar">{pie_html}</figure>')


def pvs(*codigos):
    return "".join(f'<span class="sc-pv">{c}</span>' for c in codigos)


def pre(texto):
    return f'<pre class="mini">{esc(texto.strip())}</pre>'


# ───────────────────────── grupo 1 · plataforma ─────────────────────────

# (PV, escenario, archivo de pruebas, otras formas de verlo)
ESCENARIOS = [
    ("PV01", "Registro y consulta de avisos", "test_evaluacion_avisos, test_autorizacion", "Bruno · interfaz"),
    ("PV02", "Evaluación de avisos", "test_evaluacion_avisos", "Bruno · interfaz"),
    ("PV03", "Priorización por gravedad", "test_emergencias", "Bruno · interfaz"),
    ("PV04", "Varias misiones por emergencia", "test_emergencias, test_api_misiones", "interfaz"),
    ("PV05", "Situación y tipo de misión", "test_emergencias, test_api_misiones", "interfaz"),
    ("PV06", "Capacidad de transporte", "test_asignacion, test_recursos", ""),
    ("PV07", "Competencias e integrantes", "test_asignacion, test_recursos", ""),
    ("PV08", "Compatibilidad de vehículos", "test_asignacion", "Bruno · interfaz"),
    ("PV09", "Equipamiento no operativo", "test_asignacion, test_recursos", ""),
    ("PV10", "Exclusividad de asignación", "test_asignacion", "interfaz"),
    ("PV11", "Ejecución de una misión", "test_ejecucion", "Bruno · interfaz"),
    ("PV12", "Restricciones de responsabilidad", "test_autorizacion, test_ejecucion", "Bruno (403)"),
    ("PV13", "Rechazo y reasignación", "test_ejecucion", "Bruno · interfaz"),
    ("PV14", "Administración de recursos", "test_recursos", "interfaz"),
    ("PV15", "Cancelación", "test_ejecucion", "interfaz"),
    ("PV16", "Cierre de emergencia", "test_emergencias", "Bruno · interfaz"),
    ("PV17", "Historial de operaciones", "test_emergencias", "Bruno · interfaz"),
    ("PV18", "Consistencia ante errores", "test_emergencias, test_api_misiones", "Bruno (409)"),
    ("PV19", "Demostración integral", "—", "interfaz (grupo 11)"),
]

USUARIOS = [
    ("hospital", "reportante", "registra avisos y consulta los propios"),
    ("municipio", "reportante", "segundo reportante (PV01)"),
    ("operador1", "operador", "evalúa avisos y gestiona misiones"),
    ("ana · diego · gabi · ines", "jefe_unidad", "jefes de U-rescate-1, U-rescate-2, U-ambulancia-1, U-transporte-1"),
    ("recursos1", "responsable_recursos", "administra bases y unidades"),
    ("supervisor1", "supervisor", "consulta todo y cierra emergencias"),
]

SERVICIOS = [
    ("api", "construida con el `Dockerfile`", "8000",
     ["La API y la interfaz (`/app`).", "Al arrancar corre la carga inicial y después FastAPI.",
      "Espera a que la base esté **sana** (`depends_on` con `service_healthy`)."]),
    ("db", "`mongo:7.0`", "27017",
     ["Guarda avisos, emergencias, bases y unidades.", "Volumen `mongo-data`: los datos sobreviven a un reinicio.",
      "`healthcheck` con `mongosh ping` cada 5 s."]),
    ("keycloak", "`quay.io/keycloak/keycloak:26.7.5`", "8080",
     ["Usuarios, contraseñas y perfiles.", "Importa el realm `crce` desde `keycloak/crce-realm.json`.",
      "Consola de administración: `admin` / `admin`."]),
]

VARIABLES = [
    ("MONGO_HOST", "db", "dónde está la base; en Compose, el nombre del servicio"),
    ("MONGO_USER / MONGO_PASSWORD", "root / example", "credenciales de MongoDB"),
    ("MONGO_PORT / MONGO_DB", "27017 / crce", "puerto y nombre de la base"),
    ("KEYCLOAK_URL", "http://keycloak:8080", "desde donde la API descarga las claves públicas"),
    ("KEYCLOAK_URL_PUBLICA", "http://localhost:8080", "la que usa el navegador para iniciar sesión"),
    ("KEYCLOAK_REALM / KEYCLOAK_CLIENT_ID", "crce / crce-api", "realm y cliente que emiten los tokens"),
]

TOKEN = """{
  "iss": "http://localhost:8080/realms/crce",
  "azp": "crce-api",
  "preferred_username": "ana",
  "name": "Ana Rescate",
  "realm_access": { "roles": ["jefe_unidad"] },
  "exp": 1795042865
}"""

DOCKERFILE = """FROM python:3.13-slim AS build
COPY --from=ghcr.io/astral-sh/uv:0.8.22 /uv /uvx /bin/
COPY uv.lock pyproject.toml ./
RUN uv sync --frozen --no-dev
COPY . .

FROM python:3.13-slim AS runtime
RUN useradd -u 1001 ... appuser
COPY --from=build /app .
USER appuser
CMD ["sh", "-c", "python -m app.semilla && fastapi run main.py ..."]"""

REQUIERE = """Operador = Annotated[Usuario, Depends(requiere(Perfil.OPERADOR))]
Jefe = Annotated[Usuario, Depends(requiere(Perfil.JEFE_UNIDAD))]

def finalizar(self, emergencia_id, mision_id, datos, servicio, usuario: Jefe):
    ...   # el dominio verifica además que sea el jefe de ESA unidad"""


def _arquitectura():
    """Diagrama de bloques: navegador, Keycloak, API en capas y MongoDB, dentro de Compose."""
    capas = "".join(f'<span class="sc-capa">{c}</span>' for c in ("router", "servicio", "dominio", "repositorio"))
    return f"""
<div class="sc-arq">
 <div class="sc-caja sc-nav"><b>Navegador</b><small>interfaz en <code>/app</code></small></div>
 <div class="sc-flechas">
  <span class="sc-f arriba"><i>①</i> usuario y clave → token</span>
  <span class="sc-f"><i>②</i> pedido con <code>Bearer token</code></span>
 </div>
 <div class="sc-compose"><span class="sc-etq">docker compose · 3 contenedores</span>
  <div class="sc-caja sc-kc"><b>Keycloak</b><small>realm <code>crce</code> · :8080</small><small class="sc-que">usuarios, claves y los cinco perfiles; emite el token</small></div>
  <div class="sc-caja sc-api"><b>API FastAPI</b><small>:8000</small><div class="sc-capas">{capas}</div>
   <small class="sc-nota">③ verifica la firma con las claves públicas de Keycloak</small></div>
  <div class="sc-caja sc-db"><b>MongoDB</b><small>:27017 · volumen <code>mongo-data</code></small><small class="sc-que">avisos, emergencias con sus misiones, bases y unidades</small></div>
 </div>
</div>"""


def slides_plataforma():
    s = []
    s.append(dict(eyebrow="sistema completo · plataforma", titulo="Del modelo al sistema que funciona", grande=True, html=(
        '<p class="lead">El dominio decide las reglas; alrededor hacen falta piezas que lo vuelvan usable: '
        'quién es el usuario, dónde se guardan los datos, cómo se arranca todo y cómo se opera desde una pantalla.</p>'
        + _arquitectura()
        + '<div class="callout">Las tres piezas del recuadro punteado corren en contenedores. Con <code>docker compose up -d --build</code> '
          'queda todo en marcha, con los usuarios y las unidades de demostración ya cargados.</div>')))

    pasos = "".join(f'<li><b>{n}</b><span>{md(t)}</span></li>' for n, t in [
        (1, "El usuario escribe usuario y clave en la interfaz; Keycloak los valida y devuelve un **token firmado** (JWT)."),
        (2, "Cada pedido a la API lleva el token en el encabezado `Authorization: Bearer …`."),
        (3, "`VerificadorKeycloak` comprueba la firma con las **claves públicas** del realm (JWKS) y que el emisor sea `crce`."),
        (4, "`Usuario.desde_token` toma `preferred_username` y el **único** rol de los cinco perfiles."),
        (5, "La ruta exige su perfil con `requiere(...)`; el servicio o el dominio exigen la relación con el recurso."),
    ])
    s.append(dict(eyebrow="sistema completo · autenticación", titulo="Keycloak: quién es el usuario", html=(
        '<p class="lead corto"><b>Keycloak</b> es un servidor de identidad: guarda usuarios, contraseñas y roles, y emite '
        'tokens firmados. La API no maneja contraseñas: solo confía en lo que Keycloak firmó.</p>'
        f'<div class="grid"><div class="card"><h3>Del inicio de sesión a la operación</h3><ol class="sc-pasos">{pasos}</ol></div>'
        f'<div class="card"><h3>El token de <code>ana</code>, decodificado</h3>{pre(TOKEN)}'
        '<p class="sc-pie">Extracto real. El rol <code>jefe_unidad</code> se convierte en <code>Perfil.JEFE_UNIDAD</code>; '
        'el usuario <code>ana</code> coincide con su id de persona, y así el dominio sabe de qué unidad es jefa.</p>'
        '<div class="callout">Problema que evita: si la API guardara claves propias, habría dos fuentes de verdad sobre '
        'quién es quién. Con el token firmado, nadie puede cambiarse el perfil sin invalidar la firma.</div></div></div>')))

    codigos = "".join(f'<tr><td class="sc-cod c{c[0]}">{c}</td><td>{md(q)}</td><td>{md(e)}</td></tr>' for c, q, e in [
        ("401", "Falta el token, o está vencido o mal firmado.", "pedido sin `Authorization`"),
        ("403", "El perfil no puede usar esa ruta (**nivel 1**).", "`ana` intenta registrar un aviso: *Operación permitida solo para: reportante*"),
        ("403", "El perfil es correcto pero el recurso no es suyo (**nivel 2**).", "un jefe inicia una misión de otra unidad; un reportante abre un aviso ajeno"),
        ("503", "Keycloak no responde y no se puede validar la firma.", "el contenedor de Keycloak está detenido"),
    ])
    s.append(dict(eyebrow="sistema completo · autorización", titulo="Dos niveles de autorización (PV01 y PV12)", html=(
        '<div class="grid"><div class="card"><h3>Nivel 1 · perfil por ruta</h3>'
        '<p class="explain">Cada endpoint declara qué perfiles lo usan. Se resuelve antes de llegar al servicio: '
        'si no corresponde, el caso de uso ni se ejecuta.</p>' + pre(REQUIERE) +
        '<h3>Nivel 2 · relación con el recurso</h3>'
        '<p class="explain">Lo decide quien conoce el recurso: <code>Usuario.exigir_acceso_a()</code> para el reportante y '
        '<code>Unidad.exigir_jefe()</code> en el dominio para el jefe. Ambos terminan en 403.</p></div>'
        f'<div class="card"><h3>Qué responde la API</h3><table class="sc-tabla chica"><thead><tr><th>Código</th><th>Cuándo</th>'
        f'<th>Ejemplo</th></tr></thead><tbody>{codigos}</tbody></table>'
        '<div class="callout">El 403 de nivel 2 no se puede resolver solo con el rol: los dos jefes tienen el mismo perfil. '
        'Por eso esa regla vive en el dominio, junto a la unidad.</div></div></div>')))

    filas_u = "".join(f'<tr><td><code>{esc(u)}</code></td><td><span class="tag">{esc(r)}</span></td><td>{esc(d)}</td></tr>'
                      for u, r, d in USUARIOS)
    s.append(dict(eyebrow="sistema completo · autenticación", titulo="El realm crce: perfiles y usuarios de demostración", html=(
        '<div class="sc-dos">' + foto("kc-roles.webp", "Consola de Keycloak: roles del realm crce",
                                       "Los cinco roles del realm coinciden con los cinco perfiles del enunciado (§2).")
        + foto("kc-usuarios.webp", "Consola de Keycloak: usuarios del realm crce",
               "Nueve usuarios de demostración. Todos usan la clave `crce2026`.") + '</div>'
        f'<table class="sc-tabla chica"><thead><tr><th>Usuario</th><th>Rol</th><th>Para qué</th></tr></thead><tbody>{filas_u}</tbody></table>'
        '<p class="sc-pie">El realm entero (roles, usuarios, cliente <code>crce-api</code>) está en '
        '<code>keycloak/crce-realm.json</code> y se importa al arrancar: no hay que configurar nada a mano.</p>')))

    tarjetas = "".join(
        f'<div class="card sc-serv"><h3><code>{esc(n)}</code><span class="sc-puerto">:{p}</span></h3>'
        f'<p class="rol">{md(img)}</p><ul>{"".join(f"<li>{md(x)}</li>" for x in xs)}</ul></div>' for n, img, p, xs in SERVICIOS)
    s.append(dict(eyebrow="sistema completo · docker", titulo="Docker: el mismo sistema en cualquier máquina", html=(
        '<p class="lead corto"><b>Docker</b> empaqueta un programa con todo lo que necesita (Python, dependencias, '
        'configuración) en una <b>imagen</b>; un <b>contenedor</b> es esa imagen en ejecución. <b>Docker Compose</b> '
        'describe varios contenedores que trabajan juntos y los levanta con una sola orden.</p>'
        f'<div class="tres">{tarjetas}</div>'
        '<div class="sc-dk">' + foto("../docker/desktop.webp", "Docker Desktop con el proyecto crce",
                                      "Docker Desktop: el proyecto `crce` con sus tres contenedores en marcha, cada uno con "
                                      "su imagen y su puerto.")
        + '<div class="callout">Problema que evita: «en mi máquina funciona». Sin Docker habría que instalar Python 3.13, '
        'MongoDB y Keycloak con las mismas versiones, crear usuarios y cargar datos a mano. Con Compose, '
        'el profesor ejecuta lo mismo que se probó.</div></div>')))

    orden = "".join(f'<li><b>{n}</b><span>{md(t)}</span></li>' for n, t in [
        (1, "Arrancan `db` y `keycloak`; Keycloak importa el realm."),
        (2, "Cuando `db` responde al `healthcheck`, Compose arranca `api`."),
        (3, "`python -m app.semilla` carga bases y unidades; si ya existen, no las repite."),
        (4, "`fastapi run` atiende en el puerto 8000: API y, en `/app`, la interfaz."),
    ])
    s.append(dict(eyebrow="sistema completo · docker", titulo="Cómo se construye la imagen y en qué orden arranca", html=(
        '<div class="grid"><div class="card"><h3><code>Dockerfile</code> en dos etapas</h3>' + pre(DOCKERFILE) +
        '<ul><li><b>build</b>: instala las dependencias exactas del <code>uv.lock</code>.</li>'
        '<li><b>runtime</b>: copia solo el resultado; la imagen final no lleva herramientas de compilación.</li>'
        '<li>Corre con un usuario sin privilegios (<code>appuser</code>), no como <code>root</code>.</li></ul></div>'
        f'<div class="card"><h3>Orden de arranque</h3><ol class="sc-pasos">{orden}</ol>'
        '<h3>Órdenes de uso</h3>' + pre("""docker compose up -d --build
docker compose ps
docker compose logs api
docker compose down""") +
        '<p class="sc-pie"><code>down</code> detiene todo y conserva los datos; <code>down -v</code> borra también el volumen.</p>'
        '</div></div>')))

    lectura = "".join(f'<li><b>{n}</b><span>{md(t)}</span></li>' for n, t in [
        (1, "`[build 1/7]` a `[build 7/7]`: la primera etapa. Las líneas `CACHED` reutilizan lo que no cambió: si "
            "`uv.lock` es el mismo, las dependencias no se vuelven a instalar."),
        (2, "`[build 6/7] COPY . .`: entra el código nuevo; por eso solo se rehace desde ahí."),
        (3, "`[runtime 1/4]` a `[runtime 4/4]`: la imagen final copia el resultado y crea el usuario `appuser`."),
        (4, "`naming to docker.io/library/crce-api:latest`: la imagen queda lista."),
        (5, "`up 4/4`: imagen construida, `db` **Healthy**, `keycloak` corriendo y recién entonces `api` **Started**."),
    ])
    s.append(dict(eyebrow="sistema completo · docker", titulo="La construcción, vista en la terminal", html=(
        '<div class="sc-docs"><div class="sc-texto"><p class="explain">Salida real de <code>docker compose up -d --build</code>, '
        'leída de arriba hacia abajo:</p>'
        f'<ol class="sc-pasos">{lectura}</ol></div>'
        + '<div class="sc-apila">'
        + foto("../docker/compose-build.webp", "Salida de docker compose up --build",
               "Construcción de la imagen `crce-api` en dos etapas.")
        + foto("../docker/compose-ps.webp", "docker compose ps con los tres contenedores",
               "Final de la orden y `docker compose ps`: los tres en marcha y la base `healthy`.")
        + '</div></div>')))

    filas_v = "".join(f'<tr><td><code>{esc(v)}</code></td><td><code>{esc(x)}</code></td><td>{esc(d)}</td></tr>'
                      for v, x, d in VARIABLES)
    s.append(dict(eyebrow="sistema completo · configuración", titulo="Configuración: variables de entorno", html=(
        '<p class="lead corto">Nada de direcciones ni claves escritas en el código: <code>app/config.py</code> las lee del '
        'entorno (en Compose) o de un archivo <code>.env</code> (en desarrollo, a partir de <code>.env.example</code>).</p>'
        f'<div class="grid sc-ancho"><div class="card"><table class="sc-tabla chica"><thead><tr><th>Variable</th><th>Valor en Compose</th>'
        f'<th>Para qué</th></tr></thead><tbody>{filas_v}</tbody></table></div>'
        '<div class="card"><h3>Por qué dos direcciones de Keycloak</h3>'
        '<p class="explain">Dentro de Compose, la API llega a Keycloak por el nombre del servicio (<code>keycloak:8080</code>); '
        'el navegador, en cambio, por <code>localhost:8080</code>. El token dice que lo emitió <code>localhost</code>, así '
        'que el verificador compara solo el <b>realm</b> del emisor, no el host.</p>'
        '<h3>La interfaz no tiene nada fijo</h3>'
        '<p class="explain">Al cargar, pide <code>GET /configuracion</code>:</p>'
        + pre('{"keycloak_url": "http://localhost:8080", "realm": "crce", "client_id": "crce-api"}') +
        '<p class="sc-pie">Si cambia el puerto o el realm, se cambia una variable y no hay que tocar el JavaScript.</p>'
        '</div></div>')))

    rutas = [("Avisos", "7", "registrar, listar, consultar, notas, aceptar, descartar, ver la emergencia originada"),
             ("Emergencias y misiones", "14", "prioridad, detalle, historial, crear, asignar, reasignar, cancelar, rechazar, "
              "iniciar, novedades, finalizar, cerrar, misiones del jefe"),
             ("Recursos", "13", "bases, unidades, personal, vehículo, equipamiento y su condición"),
             ("Servicio", "2", "estado de la API y configuración pública")]
    filas_r = "".join(f'<div class="sc-ruta"><b>{n}</b><span class="n">{c}</span><span>{esc(d)}</span></div>' for n, c, d in rutas)
    s.append(dict(eyebrow="sistema completo · api y persistencia", titulo="La API en capas y la persistencia", html=(
        '<div class="grid"><div class="card"><h3>36 rutas, tres recursos</h3>' + filas_r +
        '<h3>Una petición, capa por capa</h3><div class="sc-cadena">'
        '<span>router<small>HTTP ⇄ DTO</small></span><i>→</i><span>servicio<small>caso de uso</small></span><i>→</i>'
        '<span>dominio<small>reglas</small></span><i>→</i><span>repositorio<small>guardar</small></span></div>'
        '<p class="sc-pie">Si el dominio lanza un error, <code>errores_http.py</code> lo traduce: 404, 403, 409 o 422, '
        'con el nombre de la excepción en la respuesta.</p></div>'
        '<div class="card"><h3>MongoDB con esquemas versionados</h3><ul>'
        '<li>Cada repositorio tiene dos implementaciones con el mismo contrato (<code>Protocol</code>): en memoria y Mongo.</li>'
        '<li>Cada documento guarda su <code>version</code>; al leer uno viejo se <b>migra</b> (la emergencia v1 pasa a v2 con misiones).</li>'
        '<li>Al reconstruir, el dominio recibe objetos del dominio mediante <code>restaurar</code>: no conoce Mongo.</li>'
        '<li>Se guarda la emergencia completa con sus misiones: una operación, un documento; no quedan cambios a medias (PV18).</li>'
        '</ul></div></div>')))

    s.append(dict(eyebrow="sistema completo · /docs", titulo="La API se documenta sola: /docs", html=(
        '<div class="sc-docs"><div class="sc-texto">'
        '<p class="explain">FastAPI genera la especificación <b>OpenAPI</b> a partir de los routers y de los DTO de '
        'Pydantic, y la muestra en <code>http://localhost:8000/docs</code>. No se escribe a mano: si cambia una ruta o un '
        'esquema, la documentación cambia con el código.</p><ul>'
        '<li>Las 36 rutas, agrupadas por recurso: avisos, emergencias y misiones, recursos y sistema.</li>'
        '<li>El candado indica que la ruta pide el token de Keycloak.</li>'
        '<li>Al pie, los esquemas de entrada y salida: los mismos DTO que valida la API (422 si no cumplen).</li></ul>'
        '<div class="callout">Es el cierre del backend: el contrato completo de la API, en una página, generado desde el '
        'código.</div></div>'
        + foto("../docs/docs-rutas.webp", "Las rutas de /docs", "Las 36 rutas de `/docs`, agrupadas por recurso.")
        + '</div>')))

    probar = "".join(f'<li><b>{n}</b><span>{md(t)}</span></li>' for n, t in [
        (1, "**Authorize**: se pega el token que emitió Keycloak (por ejemplo, el de `operador1`)."),
        (2, "**Try it out** y **Execute** en `GET /emergencias`: 200 con las emergencias abiertas, por prioridad."),
        (3, "El mismo token en `POST /avisos`: 403, porque registrar avisos es solo del reportante."),
    ])
    s.append(dict(eyebrow="sistema completo · /docs", titulo="Probar la API desde /docs", html=(
        f'<div class="sc-docs2"><div class="sc-texto"><ol class="sc-pasos">{probar}</ol>'
        + foto("../docs/docs-authorized.webp", "Token cargado en Authorize", "Token cargado: Swagger lo envía como `Bearer`.")
        + '<p class="sc-pie">Cada ejecución muestra también el <code>curl</code> equivalente, útil para repetirlo desde la terminal.</p></div>'
        + foto("../docs/docs-get-emergencias.webp", "GET /emergencias ejecutado", "`GET /emergencias` → 200.")
        + foto("../docs/docs-post-avisos-403.webp", "POST /avisos rechazado", "`POST /avisos` con perfil operador → 403.")
        + '</div>')))
    return s


def slide_pruebas():
    """Pruebas y Bruno: abre el grupo «Los 19 escenarios»."""
    pruebas = [("test_api_misiones", 46), ("test_autorizacion", 44), ("test_emergencias", 37), ("test_recursos", 31),
               ("test_ejecucion", 29), ("test_diseno", 29), ("test_asignacion", 26), ("test_api_avisos", 26),
               ("test_evaluacion_avisos", 19), ("test_avisos", 18), ("test_persistencia", 16), ("test_avisos_robustez", 15),
               ("test_api_emergencias", 15)]
    filas_p = "".join(f'<div class="fila"><span><code>{n}.py</code></span><b>{c}</b></div>' for n, c in pruebas)
    bruno = [("00-sesiones", "inicia sesión con los 7 usuarios y guarda sus tokens"),
             ("01-avisos", "registro, notas, 401, 403 de PV01 y PV12, aceptación y 409 al repetir"),
             ("02-recursos", "unidades, persona duplicada (409), mantenimiento, 403"),
             ("03-misiones", "crear, 422, ambulancia para rescate (409), asignar, PV18, reasignar, ejecutar, cerrar, historial"),
             ("04-emergencias", "orden por prioridad y consultas")]
    filas_b = "".join(f'<li><code>{n}</code> {esc(d)}</li>' for n, d in bruno)
    return dict(eyebrow="escenarios · cómo se verifican", titulo="Pruebas unitarias y colección Bruno", html=(
        '<div class="grid"><div class="card pruebas"><h3>351 pruebas · <code>uv run python -m pytest</code></h3>' + filas_p +
        '<p class="sc-pie">Las pruebas de API se ejecutan dos veces: con el repositorio en memoria y con Mongo '
        'simulado (<code>mongomock</code>). Así se comprueba que ambas implementaciones cumplen el mismo contrato.</p></div>'
        f'<div class="card"><h3>Bruno · 41 pedidos, 49 verificaciones</h3><ul class="sc-bruno">{filas_b}</ul>'
        + pre("cd bruno\nnpx @usebruno/cli run --env local") +
        '<div class="callout">Las pruebas verifican el dominio sin red; Bruno verifica el sistema levantado, con tokens '
        'reales de Keycloak. La colección se puede repetir: crea sus propios datos en cada corrida.</div></div></div>'))


def slide_escenarios():
    """La tabla de los 19 escenarios: abre el grupo «Los 19 escenarios»."""
    cab = ('<div class="sc-esc cab"><b>PV</b><span class="t">Escenario</span><span class="p">Pruebas</span>'
           '<span class="o">También en</span></div>')
    def columna(filas):
        return '<div>' + cab + "".join(
            f'<div class="sc-esc"><b>{pv}</b><span class="t">{esc(t)}</span><span class="p">{esc(p)}</span>'
            f'<span class="o">{esc(o)}</span></div>' for pv, t, p, o in filas) + '</div>'
    celdas = columna(ESCENARIOS[:10]) + columna(ESCENARIOS[10:])
    return dict(eyebrow="escenarios · resumen", titulo="Los 19 escenarios y dónde se demuestra cada uno", html=(
        '<p class="lead corto">Cada escenario tiene pruebas automáticas que lo reproducen. Los rechazos se muestran también '
        'con Bruno, y el recorrido completo, con la interfaz (el enunciado admite demostrar los casos negativos con Bruno).</p>'
        f'<div class="sc-escs">{celdas}</div>'
        '<p class="sc-pie">Los archivos de pruebas están en <code>tests/</code> y cada prueba nombra el escenario que '
        'reproduce. En las diapositivas siguientes, cada escenario con capturas reales del sistema.</p>'))



# ───────────────────────── grupo 2 · la interfaz en uso ─────────────────────────

# (actor, título, imágenes [(archivo, alt)], qué hace, qué pasa por dentro, escenarios)
FLUJO = [
    ("todos", "Ingreso: Keycloak identifica el perfil", [("f00-ingreso.webp", "Pantalla de ingreso")],
     "Cada participante entra con su usuario. La pantalla no tiene selector de perfil: lo define Keycloak.",
     "La interfaz pide el token a Keycloak, lee el rol y arma el menú de ese perfil. El token queda en la pestaña "
     "(`sessionStorage`) y viaja en cada pedido.", ["§10"]),
    ("reportante", "El hospital registra un aviso y agrega una nota", [("f01-reportante.webp", "Reportante con su aviso pendiente")],
     "Registra un incendio de gravedad alta y, mientras sigue pendiente, agrega una nota.",
     "`POST /avisos` y `POST /avisos/{id}/notas`. Solo ve sus propios avisos: otro reportante no lo encuentra.", ["PV01"]),
    ("operador", "El operador evalúa el aviso", [("f02-pendientes.webp", "Avisos pendientes del operador")],
     "Ve los avisos pendientes, confirma o corrige tipo y gravedad, y acepta. También podría descartarlo con una justificación.",
     "`POST /avisos/{id}/aceptacion`: el aviso queda aceptado y nace la emergencia.", ["PV02"]),
    ("operador", "Emergencias abiertas, por prioridad", [("f03-emergencias.webp", "Lista de emergencias abiertas")],
     "La lista ordena por gravedad (alta, media, baja) y, a igual gravedad, por el momento de aceptación.",
     "`GET /emergencias`: el orden lo calcula el servicio, la interfaz solo lo muestra numerado.", ["PV03"]),
    ("operador", "Crear una misión", [("u-nueva-mision.webp", "Detalle de emergencia sin misiones y formulario de nueva misión")],
     "Abre la emergencia y crea una misión de rescate. El campo de personas a evacuar aparece solo para evacuaciones.",
     "`POST /emergencias/{id}/misiones`: el dominio rechaza tipos que la situación no admite.", ["PV04", "PV05"]),
    ("operador", "Asignación rechazada, sin cambios", [("u-asignacion-rechazada.webp", "Mensaje de asignación rechazada")],
     "Intenta asignar la ambulancia a un rescate. El sistema lo rechaza con un mensaje comprensible.",
     "El dominio lanza `VehiculoIncompatible` → 409. La misión sigue pendiente y la unidad, disponible: nada quedó a medias.",
     ["PV08", "PV18"]),
    ("operador", "Unidad asignada", [("u-unidad-asignada.webp", "Misión asignada a U-rescate-2")],
     "Elige `U-rescate-2`, que cumple vehículo, integrantes y equipamiento. La misión pasa a asignada.",
     "La unidad queda comprometida con esta misión: no se puede asignar a otra.", ["PV10"]),
    ("responsable de recursos", "La unidad comprometida no se modifica",
     [("u-unidad-comprometida.webp", "Unidad comprometida con una misión"),
      ("u-modificacion-rechazada.webp", "Modificación rechazada")],
     "Ve `U-rescate-2` marcada como comprometida e intenta retirar a un integrante.",
     "`UnidadComprometida` → 409. Las unidades libres sí admiten cambios de personal y equipamiento.", ["PV14"]),
    ("jefe de unidad", "Diego inicia la misión de su unidad",
     [("u-jefe-asignada.webp", "Misión asignada en la vista del jefe"),
      ("u-jefe-ejecucion.webp", "Misión en ejecución")],
     "Solo ve las misiones de su unidad. Puede iniciarla o rechazarla con una justificación; la inicia.",
     "`POST …/inicio`. Otro jefe que lo intente recibe 403: el dominio verifica que sea el jefe de esa unidad.", ["PV11", "PV12"]),
    ("jefe de unidad", "Novedad y finalización", [("u-jefe-finalizada.webp", "Misión finalizada con resultado")],
     "Registra una novedad y finaliza con resultado satisfactorio y las tareas realizadas.",
     "La misión queda finalizada y la unidad, liberada para otra misión.", ["PV11"]),
    ("supervisor", "Cierre de la emergencia", [("u-supervisor-antes-de-cerrar.webp", "Supervisor con la emergencia lista para cerrar")],
     "Abre la emergencia: todas las misiones concluyeron y una fue satisfactoria, así que puede cerrarla.",
     "`POST …/cierre`. Con misiones en curso o sin ninguna satisfactoria, el cierre se rechaza (409).", ["PV16"]),
    ("supervisor", "El historial completo", [("u-cerrada-historial.webp", "Emergencia cerrada con su historial")],
     "La emergencia queda cerrada y el historial muestra cada operación con fecha, autor y datos.",
     "Los registros son inmutables: cambios posteriores en una unidad no alteran lo ya registrado.", ["PV17"]),
    ("reportante", "El hospital ve cómo terminó", [("f10-reportante-final.webp", "Reportante ve su aviso aceptado y la emergencia cerrada")],
     "El reportante ve que su aviso fue aceptado y el estado de la emergencia que originó: cerrada.",
     "Ve tipo, gravedad, ubicación y estado; no ve misiones, unidades ni historial operativo.", ["PV02"]),
]

EVOLUCION = [
    ("reportante", "registra", "pendiente", "—", "—", "disponible"),
    ("operador", "acepta", "aceptado", "abierta", "—", "disponible"),
    ("operador", "crea misión", "aceptado", "abierta", "pendiente", "disponible"),
    ("operador", "asigna", "aceptado", "abierta", "asignada", "comprometida"),
    ("jefe", "inicia", "aceptado", "abierta", "en ejecución", "comprometida"),
    ("jefe", "finaliza", "aceptado", "abierta", "finalizada", "disponible"),
    ("supervisor", "cierra", "aceptado", "cerrada", "finalizada", "disponible"),
]


def slides_interfaz():
    s = []
    actores = "".join(f'<span class="sc-actor"><b>{n}</b>{esc(a)}</span>' for n, a in enumerate(
        ["reportante", "operador", "responsable de recursos", "jefe de unidad", "supervisor"], 1))
    s.append(dict(eyebrow="sistema completo · interfaz", titulo="La interfaz en uso: el recorrido de PV19", grande=True, html=(
        '<p class="lead">La interfaz no forma parte del contenido de la materia, pero el enunciado la exige para demostrar '
        'PV19: cinco participantes que intervienen uno después del otro sobre la misma emergencia.</p>'
        f'<div class="sc-actores">{actores}</div>'
        '<div class="grid"><div class="card"><h3>Cómo está hecha</h3><ul>'
        '<li>HTML, CSS y JavaScript, sin framework; la misma API la sirve en <code>/app</code>.</li>'
        '<li>No tiene reglas de negocio: cada botón es un pedido a la API.</li>'
        '<li>Una vista por perfil: cada uno ve solo lo que le corresponde.</li></ul></div>'
        '<div class="card"><h3>Cómo muestra los errores</h3><ul>'
        '<li>El mensaje del dominio, en palabras: <i>Un vehículo de ambulancia no sirve para rescatar</i>.</li>'
        '<li>Debajo, el nombre de la excepción y el código HTTP, para relacionarlo con el modelo.</li>'
        '<li>Los estados se ven como etiquetas de color: pendiente, asignada, en ejecución, finalizada.</li></ul></div></div>'
        '<p class="sc-pie">Capturas reales del sistema en ejecución. Clic en una imagen para ampliarla.</p>')))

    total = len(FLUJO)
    for n, (actor, titulo, imgs, hace, dentro, esc_) in enumerate(FLUJO, 1):
        figuras = "".join(foto(a, alt) for a, alt in imgs)
        clase = "sc-paso doble" if len(imgs) > 1 else "sc-paso"
        s.append(dict(eyebrow=f"interfaz · paso {n} de {total} · {actor}", titulo=titulo, html=(
            f'<div class="{clase}"><div class="sc-texto"><span class="sc-quien">{esc(actor)}</span>'
            f'<div><h3>Qué hace</h3><p class="explain">{md(hace)}</p></div>'
            f'<div><h3>Qué pasa por dentro</h3><p class="explain">{md(dentro)}</p></div><div>{pvs(*esc_)}</div></div>'
            f'<div class="sc-imgs">{figuras}</div></div>')))

    filas = "".join(f'<tr><td>{i}</td><td><b>{esc(a)}</b></td><td>{esc(o)}</td>'
                    + "".join(f'<td><span class="sc-est">{esc(x)}</span></td>' for x in xs) + '</tr>'
                    for i, (a, o, *xs) in enumerate(EVOLUCION, 1))
    s.append(dict(eyebrow="sistema completo · interfaz", titulo="Cómo evoluciona la información", html=(
        '<p class="lead corto">El mismo recorrido, leído por el estado de cada objeto. Cada participante actúa solo cuando '
        'el estado anterior se lo permite.</p>'
        f'<table class="sc-tabla sc-evol"><thead><tr><th></th><th>Quién</th><th>Operación</th><th>Aviso</th><th>Emergencia</th>'
        f'<th>Misión</th><th>Unidad</th></tr></thead><tbody>{filas}</tbody></table>'
        '<div class="callout">Los rechazos del camino (ambulancia para un rescate, modificar una unidad comprometida) no '
        'cambian ninguna columna: esa es la consistencia que pide PV18.</div>')))
    return s


# ───────────────────────── estilos y ampliación de imágenes ─────────────────────────

CSS = r"""
/* sistema completo */
.sc-arq{display:grid;grid-template-columns:minmax(150px,.8fr) minmax(170px,.9fr) 2.6fr;gap:14px;align-items:center;margin:clamp(10px,2vh,22px) 0}
.sc-caja{background:var(--panel2);border:1px solid var(--line);border-radius:14px;padding:14px 16px}
.sc-caja b{display:block;font-size:clamp(15px,1.4vw,19px)}.sc-caja small{display:block;color:var(--muted);font-size:12.5px;margin-top:2px}
.sc-nav{border-color:var(--blue);text-align:center;padding:26px 12px}
.sc-flechas{display:flex;flex-direction:column;gap:16px}
.sc-f{color:var(--accent);font-size:clamp(12px,1.05vw,14px);border-bottom:2px solid var(--accent);padding:0 4px 4px;position:relative;line-height:1.3}
.sc-f::after{content:"";position:absolute;right:-2px;bottom:-6px;border:5px solid transparent;border-left:8px solid var(--accent)}
.sc-f i{font-style:normal;color:var(--gold);margin-right:4px}
.sc-compose{position:relative;border:1.5px dashed #3c5a7a;border-radius:18px;padding:26px 14px 14px;display:grid;grid-template-columns:1fr 1.5fr 1fr;gap:12px;align-items:stretch}
.sc-etq{position:absolute;top:-10px;left:16px;background:var(--bg);color:var(--blue);font-size:12px;font-weight:700;padding:0 8px;letter-spacing:.04em}
.sc-kc{border-color:var(--gold)}.sc-db{border-color:var(--lila)}.sc-api{border-color:var(--accent)}
.sc-capas{display:flex;flex-wrap:wrap;gap:4px;margin-top:8px}.sc-capa{font:600 12px ui-monospace,Menlo,monospace;color:#bce9df;border:1px solid #32665e;border-radius:6px;padding:2px 7px}
.sc-nota{color:var(--gold)!important;margin-top:8px!important}
.sc-tabla{width:100%;border-collapse:collapse;font-size:clamp(12.5px,1.1vw,15px);color:var(--soft)}
.sc-tabla th{text-align:left;color:var(--muted);font-weight:600;font-size:12.5px;padding:6px 10px;border-bottom:1px solid var(--line)}
.sc-tabla td{padding:clamp(4px,.8vh,8px) 10px;border-bottom:1px solid var(--line);vertical-align:top;line-height:1.4}
.sc-tabla td b{color:var(--text)}.sc-tabla.chica{font-size:clamp(12px,1vw,14px)}
.sc-donde{font-size:.92em;white-space:nowrap}.sc-ok{color:#8fe3a0;font-weight:800;text-align:center}
.sc-cod{font:700 14px ui-monospace,Menlo,monospace}.sc-cod.c4{color:#ffb38a}.sc-cod.c5{color:#ff9aa8}
.sc-escs{display:grid;grid-template-columns:1fr 1fr;gap:0 22px}
.sc-esc{display:grid;grid-template-columns:44px 1.25fr 1.35fr .95fr;gap:8px;padding:clamp(3px,.55vh,6px) 4px;border-bottom:1px solid var(--line);font-size:clamp(11.5px,.98vw,13.5px);align-items:baseline;color:var(--soft)}
.sc-esc b{color:var(--accent)}.sc-esc .p{font-family:ui-monospace,Menlo,monospace;font-size:.9em;color:#bce9df}.sc-esc .o{color:var(--gold);font-size:.92em}
.sc-esc.cab{color:var(--muted);font-weight:600}.sc-esc.cab b,.sc-esc.cab .o,.sc-esc.cab .p{color:var(--muted);font-family:inherit}
.sc-pasos{list-style:none;padding:0;margin:0;display:flex;flex-direction:column;gap:8px}
.sc-pasos li{display:grid;grid-template-columns:24px 1fr;gap:10px;align-items:start;font-size:clamp(13.5px,1.2vw,16px);line-height:1.45;color:var(--soft)}
.sc-pasos li>b{display:inline-grid;place-items:center;width:24px;height:24px;border-radius:50%;background:var(--accent);color:#0b1020;font-size:12px}
.sc-dos{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:12px}
.sc-foto{margin:0;display:flex;flex-direction:column;gap:6px;min-width:0}
.sc-foto img{display:block;width:100%;height:auto;max-height:58vh;object-fit:contain;object-position:top left;border-radius:10px;border:1px solid var(--line);background:#fff;cursor:zoom-in;box-shadow:0 8px 24px rgba(0,0,0,.35)}
.sc-foto img:focus-visible{outline:3px solid var(--gold);outline-offset:2px}
.sc-foto figcaption{font-size:12.5px;color:var(--muted);line-height:1.4}
.sc-serv h3{display:flex;justify-content:space-between;align-items:center}.sc-serv h3 code{font-size:1.15em;color:var(--accent)}
.sc-puerto{font:600 13px ui-monospace,Menlo,monospace;color:var(--gold)}
.sc-ruta{display:grid;grid-template-columns:minmax(120px,170px) 30px 1fr;gap:8px;padding:5px 0;border-bottom:1px solid var(--line);font-size:clamp(12.5px,1.1vw,14.5px);color:var(--soft)}
.sc-ruta b{color:var(--text)}.sc-ruta .n{color:var(--accent);font-weight:700;text-align:right}
.sc-cadena{display:flex;align-items:center;flex-wrap:wrap;gap:6px}.sc-cadena span{background:var(--panel2);border:1px solid var(--line);border-radius:10px;padding:6px 12px;font-weight:650;font-size:14px;text-align:center}
.sc-cadena small{display:block;color:var(--muted);font-weight:400;font-size:11.5px}.sc-cadena i{color:var(--accent);font-style:normal}
.sc-bruno{list-style:none;padding:0}.sc-bruno li{margin:0 0 6px;font-size:clamp(13px,1.15vw,15px)}.sc-bruno code{color:var(--accent);margin-right:6px}
.sc-actores{display:flex;flex-wrap:wrap;gap:8px;margin:14px 0 16px}
.sc-actor{display:inline-flex;align-items:center;gap:8px;background:var(--panel2);border:1px solid var(--line);border-radius:99px;padding:5px 14px 5px 5px;font-weight:600;font-size:clamp(13px,1.2vw,16px)}
.sc-actor b{display:inline-grid;place-items:center;width:24px;height:24px;border-radius:50%;background:var(--gold);color:#0b1020;font-size:12px}
.sc-actor+.sc-actor::before{content:"→";color:var(--accent);margin:0 6px 0 -2px;order:-1;display:none}
.sc-paso{display:grid;grid-template-columns:minmax(260px,.75fr) 1.6fr;gap:clamp(14px,2vw,28px);align-items:start}
.sc-paso.doble{grid-template-columns:1fr;gap:14px}
.sc-paso.doble .sc-texto{display:grid;grid-template-columns:auto 1fr 1fr auto;gap:6px 24px;align-items:start}
.sc-paso.doble .sc-texto h3{margin-top:0}.sc-paso.doble .sc-texto>div:last-child>.sc-pv{margin-top:0}
.sc-paso.doble .sc-imgs{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.sc-paso.doble .sc-foto img{max-height:52vh}
.sc-texto h3{margin:12px 0 4px;font-size:clamp(14px,1.2vw,16px);color:var(--muted);font-weight:600}
.sc-quien{display:inline-block;background:var(--gold);color:#0b1020;font-weight:700;font-size:12.5px;border-radius:99px;padding:3px 12px}
.sc-pv{display:inline-block;color:var(--accent);border:1px solid #32665e;border-radius:99px;padding:3px 10px;font-size:12px;font-weight:700;margin:8px 6px 0 0}
.sc-est{display:inline-block;background:var(--panel2);border:1px solid var(--line);border-radius:99px;padding:2px 10px;font-size:.92em}
.sc-dk{display:grid;grid-template-columns:1.7fr 1fr;gap:16px;align-items:center;margin-top:14px}.sc-dk .callout{margin:0}
.sc-apila{display:flex;flex-direction:column;gap:12px;min-width:0}.sc-apila .sc-foto img{max-height:none}
.sc-docs{display:grid;grid-template-columns:minmax(260px,.7fr) 1.6fr;gap:clamp(14px,2vw,28px);align-items:start}
.sc-docs2{display:grid;grid-template-columns:minmax(240px,.8fr) 1fr 1fr;gap:16px;align-items:start}
.sc-docs2 .sc-foto img{max-height:62vh}
@media (max-width:900px){.sc-dk,.sc-docs,.sc-docs2{grid-template-columns:1fr}}
.sc-evol td:first-child{color:var(--muted);width:24px}
.sc-pie{font-size:13px;color:var(--muted);margin:10px 0 0;line-height:1.45}.sc-pie code{font-size:.95em}
.sc-que{color:var(--soft)!important;margin-top:8px!important;font-size:13px!important;line-height:1.35}
.sc-tabla .tag{margin:0}.grid.sc-ancho{grid-template-columns:minmax(0,1.35fr) minmax(0,1fr)}.sc-ancho pre.mini{white-space:pre-wrap}
#sc-zoom{position:fixed;inset:0;z-index:50;background:rgba(5,8,18,.88);display:none;align-items:center;justify-content:center;padding:3vh 3vw;cursor:zoom-out}
#sc-zoom.on{display:flex}#sc-zoom img{max-width:100%;max-height:100%;border-radius:10px;background:#fff;box-shadow:0 12px 40px rgba(0,0,0,.6)}
@media (max-width:900px){.sc-arq,.sc-compose,.sc-paso,.sc-paso.doble,.sc-dos,.sc-escs{grid-template-columns:1fr}.sc-paso.doble .sc-imgs{grid-template-columns:1fr}}
"""

JS = r"""<script>
/* ampliar capturas: clic o Enter abre; clic, Esc o cualquier tecla cierra. Se reajusta la diapositiva al cargar la imagen. */
document.addEventListener('DOMContentLoaded',()=>{
 const capa=document.createElement('div');capa.id='sc-zoom';capa.setAttribute('role','dialog');capa.setAttribute('aria-label','Imagen ampliada');
 const im=document.createElement('img');capa.append(im);document.body.append(capa);
 const abrir=img=>{im.src=img.src;im.alt=img.alt;capa.classList.add('on')};
 const cerrar=()=>capa.classList.remove('on');
 capa.addEventListener('click',e=>{e.stopPropagation();cerrar()});
 document.querySelectorAll('.sc-foto img').forEach(img=>{
  img.addEventListener('click',e=>{e.stopPropagation();abrir(img)});
  img.addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();e.stopPropagation();abrir(img)}});
  img.addEventListener('load',()=>{if(typeof ajustarSlide==='function'&&img.closest('.slide.active'))ajustarSlide()});
 });
 addEventListener('keydown',e=>{if(capa.classList.contains('on')){e.preventDefault();e.stopImmediatePropagation();cerrar()}},true);
});
</script>"""
