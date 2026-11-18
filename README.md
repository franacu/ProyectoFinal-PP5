# CRCE — Centro Regional de Coordinación de Emergencias

TP Integrador 2026 · Paradigmas de Programación V · FIE-UNDEF

Dominio en Python puro (solo biblioteca estándar), orientado a objetos, expuesto mediante una API REST
(FastAPI) por capas con persistencia en MongoDB.

**Ver en línea (presentación y diagramas):** https://franacu.github.io/ProyectoFinal-PP5/

## Ver el proyecto en tu computadora (paso a paso)

Si solo querés mirarlo, no hace falta instalar nada: abrí https://franacu.github.io/ProyectoFinal-PP5/
(en esa versión los enlaces al enunciado y a VS Code no funcionan). Para correrlo en tu máquina:

La versión en línea muestra la **presentación y los diagramas interactivos** (páginas HTML estáticas
generadas a partir del código real). Para usar la API hacen falta además Docker y uv (pasos 3 y 3b).

**1. Requisitos**

- Git
- Python 3.13 o superior (`python3 --version` para comprobarlo)
- [uv](https://docs.astral.sh/uv/) (opcional pero recomendado): `curl -LsSf https://astral.sh/uv/install.sh | sh`
  en macOS/Linux, o `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"` en Windows

**2. Clonar el repositorio**

```bash
git clone https://github.com/franacu/ProyectoFinal-PP5.git
cd ProyectoFinal-PP5
```

**3. Instalar y comprobar que todo funciona** (debe terminar con `305 passed`)

```bash
uv sync
uv run python -m pytest -q
```

Los tests no necesitan MongoDB. Cada prueba de la API corre dos veces: con repositorios en memoria y con
los repositorios de MongoDB sobre `mongomock` (una base Mongo simulada), de modo que también se prueba
que cada objeto se guarde y se restaure sin pérdidas.

**3b. Levantar la API REST con MongoDB**

```bash
docker compose up -d db      # solo la base (Mongo 7) en localhost:27017
uv run fastapi dev           # API en http://localhost:8000 · documentación en http://localhost:8000/docs
```

O todo en contenedores: `docker compose up -d --build`. Para probar los endpoints, abrir la carpeta
`bruno/` con [Bruno](https://www.usebruno.com/) y elegir el entorno `local`
(o por consola: `cd bruno && npx @usebruno/cli run --env local`). La colección recorre avisos, recursos,
misiones y cierre, con los casos negativos (403, 409, 422) y PV18; puede ejecutarse varias veces seguidas.

Mientras no esté la autenticación, el usuario se indica con el encabezado `X-Usuario`.

**4. Generar la pantalla de presentación y diagramas**

```bash
uv run python docs/crce.py
```

(o `python3 docs/crce.py`; solo usa la biblioteca estándar). Crea `docs/crce.html`, `docs/diagrama.html`
y `docs/backend_presentacion.html`.

**5. Abrirla en el navegador**

```bash
open docs/crce.html          # macOS
xdg-open docs/crce.html      # Linux
start docs\crce.html         # Windows
```

Se abre una página con una barra lateral:

| Tecla / botón | Qué hace |
|---|---|
| **Presentación** (`P`) | Avanza de a un clic con `Espacio` o `→`; `←` vuelve; `F` pantalla completa |
| **Diagramas** (`D`) | Modelo de clases, estados de la misión y vista en lista; cada caja se vincula al código |
| `M` | Achica o agranda el menú |

Desde la presentación, tocar una clase del pie (o apretar `D`) abre el diagrama enfocado en esa clase.

**6. Opcional: enlaces al enunciado y a VS Code**

- Para que los botones "§ sección" abran el enunciado, copiá el PDF como `docs/enunciado.pdf`
  (está en `.gitignore`: no se sube) y volvé a ejecutar el paso 4.
- "Ver en VS Code" abre el archivo en la línea exacta, siempre que VS Code esté instalado y el
  repositorio esté clonado en esta misma ubicación.

**Si algo falla**

| Síntoma | Solución |
|---|---|
| `command not found: python` | Usá `python3` |
| `uv: command not found` | Reabrí la terminal tras instalar uv, o usá la variante sin uv |
| La presentación abre pero la barra lateral no cambia | Abrí `docs/crce.html`, no los otros dos archivos sueltos |
| Los enlaces al enunciado no abren | Falta `docs/enunciado.pdf` (paso 6) |

## Estructura

```
dominio/
  catalogos.py     # catálogos cerrados: situaciones, gravedad, competencias, categorías, condiciones
  errores.py       # excepciones de dominio (un motivo = una clase)
  valores.py       # Ubicacion y validaciones compartidas
  historial.py     # Registro inmutable + catálogo de operaciones (§9)
  aviso.py         # Aviso (entidad, State) + Nota, Descarte; aceptar() origina la Emergencia
  emergencia.py    # Emergencia (raíz de sus misiones, State abierta/cerrada), prioridad, cierre
  mision.py        # Mision abstracta (State de 5 estados) + Evacuacion, Rescate, AsistenciaSanitaria
  unidad.py        # Unidad: condición de servicio (State) y compromiso con una misión
  flota.py         # Flota: bases y unidades; garantiza que ningún recurso esté en dos unidades
  personal.py      # Persona y competencias
  vehiculos.py     # Vehiculo polimórfico: TransportePersonas, VehiculoRescate, Ambulancia
  equipamiento.py  # Equipo y su condición
  distribucion.py  # ¿existe un reparto de personas distintas que cubra los puestos?
tests/
  test_avisos.py, test_avisos_robustez.py   # Avance 1 (R1–R6)
  test_evaluacion_avisos.py                 # PV01–PV02: aceptar / descartar
  test_recursos.py                          # PV07, PV14 y unicidad de recursos
  test_asignacion.py                        # PV06–PV10
  test_ejecucion.py                         # PV11–PV13, PV15, PV18
  test_emergencias.py                       # PV03–PV05, PV16–PV18
  test_diseno.py                            # el dominio no pregunta por clase, solo stdlib, sin hora del sistema
  test_api_avisos.py, test_api_emergencias.py  # contrato HTTP y códigos de error
  test_api_misiones.py                      # recursos, misiones y cierre por HTTP (PV04–PV18)
  test_persistencia.py                      # esquemas versionados y repositorios Mongo
  escenarios.py                             # armado de datos de ejemplo
PDFs_documentacion/        # enunciado, Avance 1 (avance-1.md) y primera entrega (PDF)
app/                       # capa de aplicación (FastAPI + MongoDB); el dominio no la conoce
  main.py                  # crear_aplicacion(): servicios, routers y manejo de errores
  dependencies.py          # entrega a cada endpoint su servicio (Depends)
  avisos/                  # router → service → repository; esquema_mongo (documento ⇄ Aviso, versionado)
  emergencias/             # emergencias y misiones; esquema v2 (incluye misiones, migra la v1)
  recursos/                # bases y unidades: composición y condición; fabricas (texto ⇄ clase)
  internal/                # conexión Mongo, reloj, identidad, esquema común, errores → HTTP
bruno/                     # colección de pedidos HTTP con sus verificaciones
docs/
  crce.py                  # genera crce.html: barra lateral con presentación y diagramas
  backend_presentacion.py  # la presentación: menú, recorrido general y un grupo por archivo
  conformacion.py          # sección «Conformación del diagrama»: del enunciado a las clases y sus relaciones
  guion_archivos.py        # las notas de cada diapositiva de código
  diagrama_interactivo.py  # diagramas vinculados al código
```

## Decisiones de diseño (resumen)

- **State** en Aviso, Mision (5 estados), Emergencia y condición de servicio de Unidad: cada estado
  decide qué admite; el objeto que lo contiene delega y nunca pregunta "¿en qué estado estás?".
- **Polimorfismo por tipo de misión y de vehículo** (doble despacho): la unidad le pregunta a la
  misión y el vehículo contesta; no hay `isinstance` en el dominio (lo vigila `test_diseno.py`).
- **Null Object** para la unidad asignada de una misión: liberar una misión pendiente es no hacer nada.
- **Falla antes de modificar**: toda operación valida todo primero; un rechazo no deja cambios ni registros.
- **Historial inmutable**: cada agregado expone sus `Registro` como tupla de objetos congelados.
- **Fechas como parámetro**: el dominio nunca llama a `datetime.now()`.
