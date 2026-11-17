"""Sección «Código»: los 13 archivos del dominio en 7 grupos, de la base hasta lo último que se construyó.

Cada diapositiva explica una función, clase o construcción de Python. Lo que ya se explicó
no se repite: se cita («igual que en ...») y se sigue.
Una nota es (texto_a_buscar_en_la_línea, título, qué es, para qué sirve [opcional]).
"""
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def R(archivo, desde, hasta, antes=0):
    """Rango de líneas [ini, fin] (1-based): desde la primera que contiene `desde` hasta la primera posterior que contiene `hasta`."""
    lineas = (RAIZ / archivo).read_text(encoding="utf-8").split("\n")
    ini = next(i for i, l in enumerate(lineas) if desde in l)
    fin = next(i for i in range(ini, len(lineas)) if hasta in lineas[i])
    return (ini + 1 - antes, fin + 1)


def n(aguja, titulo, que, para=""):
    return (aguja, titulo, que, para, {})


def paso(clave, grupo, titulo, archivo, rango, por_que, *notas, clase=None):
    return dict(tipo="codigo", directo=True, titulo=f"0 · {titulo}", clase=clase, archivo=archivo, simbolo=clave,
                lineas=rango, por_que=por_que, notas=list(notas), grupo=grupo, sin_web=True)


DOM = "dominio/"
CAT, VAL, ERR, HIS = DOM + "catalogos.py", DOM + "valores.py", DOM + "errores.py", DOM + "historial.py"
AVI, PER, EQU, VEH = DOM + "aviso.py", DOM + "personal.py", DOM + "equipamiento.py", DOM + "vehiculos.py"
DIS, UNI, MIS, EME, FLO = DOM + "distribucion.py", DOM + "unidad.py", DOM + "mision.py", DOM + "emergencia.py", DOM + "flota.py"

GRUPOS = [
    dict(titulo="La base: listas cerradas y validaciones", archivos=["catalogos.py", "valores.py"],
         desc="Lo primero que se escribió: de acá depende todo lo demás."),
    dict(titulo="Los errores y el historial", archivos=["errores.py", "historial.py"],
         desc="Un error con nombre por cada regla, y el Registro que deja constancia de todo."),
    dict(titulo="El aviso", archivos=["aviso.py"],
         desc="Donde empieza el negocio: Nota, Descarte, estados y Aviso."),
    dict(titulo="Personal, equipo y vehículos", archivos=["personal.py", "equipamiento.py", "vehiculos.py"],
         desc="Los recursos simples con los que se arman las unidades."),
    dict(titulo="La distribución y la unidad", archivos=["distribucion.py", "unidad.py"],
         desc="Cómo se reparten las personas y cómo una unidad se compromete con una misión."),
    dict(titulo="La misión", archivos=["mision.py"],
         desc="Estados, unidad asignada, operaciones y los tres tipos de misión."),
    dict(titulo="La emergencia y la flota", archivos=["emergencia.py", "flota.py"],
         desc="Lo último que se armó: coordina las misiones y controla los recursos de todas las unidades."),
]

P = []   # pasos, en orden; cada uno lleva su grupo (0..6)

# ═════════ 1 · LA BASE ═════════
P += [
 paso("cat_base", 0, "catalogos.py: Catalogo", CAT, R(CAT, "from enum", "return valor in tuple"),
      "Todo lo que el enunciado fija como lista cerrada se escribe una sola vez acá.",
      n("from enum import Enum", "Importar de la biblioteca estándar",
        "`from módulo import nombre` trae una pieza de Python ya hecha. Enum viene en la biblioteca estándar: el dominio no usa librerías externas."),
      n("class Catalogo(Enum)", "Enum: una lista cerrada de opciones",
        "Un **Enum** define un conjunto cerrado de constantes con nombre: una lista fija de opciones válidas.\n\n"
        "**Catalogo** es la base de todas las listas del enunciado. Garantiza que un valor solo pueda ser uno de los elementos predefinidos: si no está en la lista, no se puede construir.",
        "Nunca entra al sistema un tipo de situación o un nivel de gravedad inventado."),
      n("@classmethod", "@classmethod: un método de la clase",
        "Un método de clase se llama sobre la clase misma, sin crear objetos: TipoSituacion.contiene(x). Su primer parámetro, cls, es la clase."),
      n("return valor in tuple(cls)", "contiene(): ¿está en la lista?",
        "tuple(cls) arma la tupla con los miembros reales del Enum y `in` pregunta si el valor es uno de ellos. `-> bool` indica que devuelve verdadero o falso.",
        "Compara contra los miembros reales, no contra su texto.")),
 paso("cat_listas", 0, "catalogos.py: las listas del enunciado", CAT, R(CAT, "class TipoSituacion", 'NO_SATISFACTORIO = "no_satisfactorio"'),
      "Cada lista es una clase que hereda de Catalogo y solo declara sus miembros.",
      n("INUNDACION =", "NOMBRE = valor",
        "Cada línea es un miembro: el nombre se usa en el código (TipoSituacion.INUNDACION) y el valor es el texto que viaja y se guarda ('inundacion')."),
      n("BAJA = 1", "Gravedad: el valor es un número",
        "Baja vale 1, Media 2 y Alta 3. El número sirve para ordenar después las emergencias de más a menos graves (§4)."),
      n("class Competencia", "Las demás listas siguen el mismo molde",
        "Competencia (qué sabe hacer una persona), CategoriaVehiculo, CategoriaEquipo, CondicionOperativa (vehículo o equipo), CondicionServicio (unidad), TipoMision y ResultadoMision. Todas heredan contiene()."),
      n("class ResultadoMision", "ResultadoMision: lo que declara el jefe", "Satisfactorio o no satisfactorio. Define cuándo una emergencia puede cerrarse (§7.2).")),
 paso("val_funciones", 0, "valores.py: validaciones compartidas", VAL, R(VAL, "from __future__", "return False"),
      "Dos preguntas que se hacen en todo el dominio: ¿hay texto? y ¿es un entero positivo?",
      n("from __future__", "Anotaciones de tipo",
        "Con esta línea se pueden escribir tipos como `-> Aviso` antes de que la clase exista. Los tipos (valor: str, -> bool) ayudan a leer y revisar el código; Python no los hace cumplir al ejecutar."),
      n("def hay_texto", "hay_texto(): ¿hay texto con contenido?",
        "`return bool(valor) and not valor.isspace()` hace dos comprobaciones:\n\n"
        "- `bool(valor)`: el valor no es nulo (None) ni está vacío ('').\n"
        "- `not valor.isspace()`: no está compuesto solo por espacios en blanco.",
        "Garantiza que un campo de texto obligatorio contenga caracteres reales y útiles. Se usa en todo el dominio."),
      n("return operator.index", "es_entero_positivo(): 1, 2, 3…",
        "Verifica que el valor sea un **número entero mayor a cero**.\n\n"
        "- `operator.index(valor)` acepta solo enteros verdaderos: con texto, decimales o None lanza TypeError.\n"
        "- `valor is not True` excluye explícitamente los booleanos, porque Python trata True como 1.",
        "Rechaza capacidades o cantidades como 0, -3, 2.5, '8' o True."),
      n("except TypeError", "try / except: atrapar un error",
        "Si el tipo de dato no es un entero válido, el TypeError se **captura** en el except: el programa no se interrumpe y la función responde False.",
        "Quien pregunta recibe siempre un sí o un no, nunca una excepción inesperada.")),
 paso("val_ubicacion", 0, "valores.py: Ubicacion", VAL, R(VAL, "@dataclass", "raise DatoDeAvisoInvalido", antes=0),
      "§7.1: todo aviso informa dónde ocurre la situación.",
      n("@dataclass", "Inmutable y con campos cerrados",
        "@dataclass arma el constructor. frozen=True: una vez creada no se puede modificar. slots=True: el objeto solo guarda los campos declarados (dirección y localidad); no se le agregan atributos por error y ocupa menos memoria.",
        "Una ubicación es un valor: dos con los mismos datos son lo mismo, y nadie la cambia a escondidas."),
      n("def __post_init__", "__post_init__: validar al crearse",
        "Se ejecuta justo después del constructor y rechaza dirección o localidad vacías con DatoDeAvisoInvalido. `raise` lanza el error.",
        "Una ubicación inválida nunca llega a existir.")),
]

# ═════════ 2 · ERRORES E HISTORIAL ═════════
P += [
 paso("err_base", 1, "errores.py: la base y los errores del aviso", ERR, R(ERR, "class ErrorDeDominio", "Aceptar exige operador"),
      "Cada regla del negocio que se viola lanza un error con nombre propio. Primero, la base común y los errores del aviso (§2.1, §7.1).",
      n("class ErrorDeDominio", "ErrorDeDominio: la base de todos los rechazos",
        "Hereda de **Exception**, la clase de errores de Python, y no agrega código: su función es **agrupar**.\n\n"
        "Todos los errores del negocio heredan de ella, así que con un solo `except ErrorDeDominio` se atrapan todos los rechazos del dominio, sin confundirlos con fallas técnicas de Python.",
        "La futura API podrá traducir cualquier rechazo del negocio a una respuesta HTTP clara con una sola regla."),
      n("class DatoDeAvisoInvalido", "DatoDeAvisoInvalido: un dato del aviso falta o no vale",
        "Se lanza al **crear un aviso** cuando falta un dato obligatorio o no pertenece al catálogo: reportante, ubicación, tipo de situación, gravedad, descripción o fecha. "
        "También cuando una ubicación no tiene dirección o localidad.\n\n"
        "Ejemplo: registrar un aviso con descripción '   ' o con gravedad 'altísima'.",
        "Regla R1: un aviso nace completo o no nace."),
      n("class NotaInvalida", "NotaInvalida: una nota incompleta",
        "Se lanza cuando una nota no tiene **autor**, **texto** o **fecha y hora**.\n\n"
        "Ejemplo: `aviso.agregar_nota('rep-1', '', fecha)`.",
        "Regla R2: cada nota conserva autor, fecha y hora."),
      n("class NotaDeOtroAutor", "NotaDeOtroAutor: la nota no la escribe el reportante",
        "Se lanza cuando alguien que **no es el reportante del aviso** intenta agregarle una nota.\n\n"
        "Ejemplo: el reportante rep-2 intenta comentar un aviso de rep-1.",
        "§2.1: solo su reportante puede agregar notas. La regla la decide el aviso, que conoce a su reportante."),
      n("class DescarteInvalido", "DescarteInvalido: un descarte incompleto",
        "Se lanza cuando el descarte no tiene **operador** o **fecha y hora**.\n\n"
        "Es además la base de JustificacionVacia: agrupa todo lo que puede faltarle a un descarte.",
        "Regla R4: el descarte deja constancia de quién lo hizo y cuándo."),
      n("class JustificacionVacia", "JustificacionVacia: descartar o rechazar sin explicar",
        "Es un caso **más específico** de DescarteInvalido (hereda de él). Se lanza cuando la justificación está vacía o tiene solo espacios.\n\n"
        "Se usa en dos lugares:\n\n"
        "- El operador **descarta un aviso** sin justificación (R4).\n"
        "- El jefe **rechaza una misión** sin justificación (§2.3).",
        "Se puede atrapar el caso puntual (JustificacionVacia) o todo el grupo (DescarteInvalido)."),
      n("class AvisoNoPendiente", "AvisoNoPendiente: el aviso ya fue evaluado",
        "Se lanza cuando se intenta operar sobre un aviso que **ya no está pendiente**, es decir, aceptado o descartado:\n\n"
        "- agregarle una nota,\n"
        "- descartarlo otra vez,\n"
        "- aceptarlo después de descartado, o aceptarlo dos veces.\n\n"
        "Lo lanzan los estados _Aceptado y _Descartado.",
        "Regla R5 y §7.1: un aviso se evalúa una sola vez y un aceptado origina una única emergencia."),
      n("class AceptacionInvalida", "AceptacionInvalida: aceptar con datos incompletos",
        "Se lanza al **aceptar un aviso** cuando la emergencia que se origina queda incompleta: falta el operador o la fecha, o el tipo y la gravedad confirmados están fuera de catálogo.\n\n"
        "Ejemplo: aceptar confirmando una gravedad que no existe.",
        "§2.2: al aceptar, el operador confirma o corrige tipo y gravedad; esos datos tienen que ser válidos.")),
 paso("err_recursos", 1, "errores.py: recursos y unidades", ERR, R(ERR, "class RecursoInvalido", "no se asigna ni se modifica"),
      "§5: errores de las personas, vehículos, equipos, bases y unidades.",
      n("class RecursoInvalido", "RecursoInvalido: un recurso mal cargado",
        "Se lanza cuando una **persona, vehículo, equipo o unidad** tiene datos incompletos o incoherentes.\n\n"
        "Ejemplos:\n\n"
        "- una persona sin nombre o sin competencias,\n"
        "- un transporte con capacidad 0,\n"
        "- un equipo con una categoría fuera de catálogo,\n"
        "- una unidad o una base sin identificación,\n"
        "- una unidad sin jefe o sin vehículo, o retirar al jefe de su unidad.",
        "Es el error más usado del dominio: ningún recurso inválido llega a formar parte de una unidad."),
      n("class RecursoDuplicado", "RecursoDuplicado: un recurso en dos lugares",
        "Se lanza cuando una **persona, vehículo o equipo ya pertenece a otra unidad**, o cuando se registra dos veces la misma base o unidad.\n\n"
        "Ejemplo: incorporar a Ana a la unidad U2 cuando ya integra U1.",
        "§5.2: una misma persona, vehículo o elemento de equipamiento no puede formar parte de dos unidades a la vez. Lo controla la Flota."),
      n("class NoEncontrado", "NoEncontrado: se pidió algo que no existe",
        "Se lanza cuando se busca una **unidad, base, misión o recurso** por su id y no está.\n\n"
        "Ejemplos: asignar la unidad 'U99', o operar sobre una misión que no pertenece a esa emergencia.",
        "La futura API lo traduce en un 404: el pedido es correcto, pero el recurso no existe."),
      n("class UnidadComprometida", "UnidadComprometida: la unidad está ocupada en una misión",
        "Se lanza cuando se intenta **modificar la composición** de una unidad (personal, vehículo, equipo o condición) mientras está **reservada o ejecutando una misión**.\n\n"
        "Ejemplo: el responsable de recursos intenta cambiar el vehículo de una unidad asignada (PV14).\n\n"
        "También se lanza si se intenta **liberar** una unidad de una misión con la que no está comprometida.",
        "§8.4: una unidad no puede modificarse administrativamente mientras está comprometida.")),
 paso("err_asignacion", 1, "errores.py: motivos de rechazo de una asignación", ERR, R(ERR, "class AsignacionRechazada", "Un jefe solo opera"),
      "§8.2: si una unidad no puede recibir una misión, el error dice exactamente por qué.",
      n("class AsignacionRechazada", "AsignacionRechazada: la familia de los rechazos",
        "Es la **base** de todos los motivos por los que una unidad no puede recibir una misión. No se lanza sola: se lanza siempre uno de sus hijos.\n\n"
        "Corresponde a la lista de verificaciones del §8.2: si alguna falla, la asignación se rechaza indicando el motivo.",
        "Se pueden atrapar todos los rechazos de asignación juntos, o uno en particular."),
      n("class UnidadNoHabilitada", "UnidadNoHabilitada: en mantenimiento o fuera de servicio",
        "Se lanza cuando la unidad elegida está **en mantenimiento** o **fuera de servicio**.\n\n"
        "Ejemplo: asignar una misión a una unidad que el responsable de recursos declaró en mantenimiento.",
        "§8.4: solo las unidades habilitadas pueden recibir asignaciones."),
      n("class UnidadOcupada", "UnidadOcupada: ya tiene otra misión",
        "Se lanza cuando la unidad **ya tiene otra misión** asignada o en ejecución.\n\n"
        "Hereda de **dos clases** (herencia múltiple): es un rechazo de asignación y también un caso de unidad comprometida. Se la puede atrapar como cualquiera de las dos.",
        "PV10: la segunda asignación se rechaza sin alterar la primera."),
      n("class VehiculoIncompatible", "VehiculoIncompatible: el vehículo no sirve",
        "Se lanza en tres situaciones:\n\n"
        "- el vehículo es de **otra categoría** (una ambulancia para una evacuación),\n"
        "- **no alcanza la capacidad** (6 plazas para evacuar a 8 personas, PV06),\n"
        "- está **fuera de servicio**.\n\n"
        "Lo lanza el propio vehículo al responder si sirve para la misión.",
        "PV06 y PV08: el mensaje dice cuál de los tres casos ocurrió."),
      n("class PersonalInsuficiente", "PersonalInsuficiente: faltan personas para los puestos",
        "Se lanza cuando **no existe un reparto de personas distintas** que cubra todos los puestos de la misión.\n\n"
        "Ejemplo: un rescate necesita un conductor y dos rescatistas, pero la unidad tiene un conductor y un solo rescatista. Una persona con dos competencias no cuenta dos veces.",
        "PV07: se verifica que exista una distribución, sin asignar nominalmente cada puesto."),
      n("class EquipamientoInsuficiente", "EquipamientoInsuficiente: falta el equipo operativo",
        "Se lanza cuando la unidad **no tiene al menos un elemento operativo** de la categoría que exige la misión (equipo de rescate o sanitario).\n\n"
        "Un equipo fuera de servicio no cuenta.",
        "PV09: con el equipo roto se rechaza; al restablecerlo, la asignación se acepta."),
      n("class NoEsJefeDeLaUnidad", "NoEsJefeDeLaUnidad: no es su misión",
        "Se lanza cuando un jefe intenta **iniciar, rechazar, registrar novedades o finalizar** una misión que no está asignada a **su propia unidad**, o una misión que no tiene unidad.\n\n"
        "No hereda de AsignacionRechazada: no es un problema de la unidad, sino de quién intenta operar.",
        "§2.3 y PV12: un jefe solo opera sobre las misiones de su unidad.")),
 paso("err_mision", 1, "errores.py: misiones", ERR, R(ERR, "class MisionInvalida", "Finalizar exige resultado"),
      "§6 y §8: errores propios de la misión y de su ciclo de vida.",
      n("class MisionInvalida", "MisionInvalida: una misión mal creada",
        "Se lanza al **crear una misión** sin objetivo, o una evacuación con una cantidad de personas que no es un entero positivo. "
        "También cuando una novedad no tiene autor, texto o fecha.\n\n"
        "Ejemplo: crear una evacuación de 0 personas.",
        "Una misión nace con lo que necesita para poder verificarse después."),
      n("class MisionIncompatible", "MisionIncompatible: ese tipo no corresponde a la situación",
        "Se lanza cuando el **tipo de misión no está permitido** para el tipo de situación de la emergencia, según la tabla del §6.4.\n\n"
        "Ejemplo: crear una evacuación para un accidente vial.",
        "PV05: la misión se rechaza; rescate y asistencia sanitaria sí se admiten."),
      n("class MisionEnEstadoInvalido", "MisionEnEstadoInvalido: esa operación no corresponde al estado",
        "Se lanza cuando se pide una **transición no admitida** desde el estado actual de la misión.\n\n"
        "Ejemplos:\n\n"
        "- iniciar una misión pendiente (no tiene unidad),\n"
        "- reasignar o rechazar una misión en ejecución (PV13),\n"
        "- iniciar una misión cancelada (PV15),\n"
        "- reabrir una finalizada.\n\n"
        "Lo arma cada estado con el nombre de la operación rechazada.",
        "§8.1: no se admiten transiciones arbitrarias, y una misión finalizada o cancelada no se reabre."),
      n("class MisionSinConcluir", "MisionSinConcluir: todavía hay misiones activas",
        "Se lanza al intentar **cerrar una emergencia** que tiene alguna misión pendiente, asignada o en ejecución.",
        "§7.2 y PV16: para cerrar, todas las misiones tienen que estar finalizadas o canceladas."),
      n("class ResultadoInvalido", "ResultadoInvalido: finalizar sin informar",
        "Se lanza cuando el jefe **finaliza una misión** con un resultado fuera de catálogo, sin describir las tareas realizadas o sin fecha.\n\n"
        "Ejemplo: finalizar con tareas = ''.",
        "§2.3: al finalizar, el jefe registra el resultado y describe las tareas.")),
 paso("err_resto", 1, "errores.py: emergencias e historial", ERR, R(ERR, "class EmergenciaCerrada", '"""Un registro histórico'),
      "§7.2 y §9: el cierre de la emergencia y la validez de cada registro.",
      n("class EmergenciaCerrada", "EmergenciaCerrada: ya no admite cambios",
        "Se lanza cuando se intenta **agregar o modificar misiones** en una emergencia cerrada, o **cerrarla por segunda vez**.",
        "§7.2 y PV16: una emergencia cerrada no admite nuevas misiones ni modificaciones operativas."),
      n("class SinMisionExitosa", "SinMisionExitosa: falta un resultado satisfactorio",
        "Se lanza al intentar cerrar una emergencia **sin misiones**, o cuyas misiones terminaron todas canceladas o finalizadas sin resultado satisfactorio.\n\n"
        "La emergencia sigue abierta y admite nuevas misiones.",
        "§7.2 y PV16: para cerrar hace falta al menos una misión finalizada con éxito."),
      n("class RegistroInvalido", "RegistroInvalido: una constancia incompleta",
        "Se lanza cuando un registro del historial no tiene **actor**, **fecha y hora**, una **operación del catálogo** o al menos un **recurso afectado**.",
        "§9: cada registro identifica quién, cuándo, qué operación y sobre qué recursos. Un registro incompleto no se guarda.")),
 paso("his_registro", 1, "historial.py: Operacion y Registro", HIS, R(HIS, "from __future__", "return dict(self.detalle).get(clave)"),
      "§9: cada cambio deja constancia de quién hizo qué, cuándo y sobre qué recursos.",
      n("class Operacion(Enum)", "Operacion: qué se puede registrar",
        "Son las **etiquetas** que identifican cada acción que queda guardada en el historial: dicen **qué pasó** (se registró un aviso, se asignó una misión, se cambió un vehículo…).\n\n"
        "**Ejemplo: AVISO_REGISTRADO.** Cuando un reportante crea un aviso, el constructor guarda solo este registro:\n\n"
        "| quién | cuándo | qué | sobre qué |\n"
        "|---|---|---|---|\n"
        "| rep-1 | 10:00 | AVISO_REGISTRADO | av-1 |",
        "Leyendo el historial se sabe qué pasó, siempre con el mismo nombre (§9)."),
      n("@dataclass(frozen=True, slots=True)", "Registro: quién, cuándo y qué",
        "Un registro es inmutable, igual que Ubicacion. `tuple[str, ...]` es una tupla de textos de cualquier largo; `detalle` guarda pares (clave, texto) y su `= ()` es el valor por defecto: tupla vacía."),
      n("def __post_init__", "Validar el registro",
        "Igual que en Ubicacion, `__post_init__` valida apenas se crea el registro. Exige cuatro cosas:\n\n"
        "1. un **actor** (quién),\n"
        "2. una **fecha y hora** (cuándo),\n"
        "3. una **operación** del catálogo (qué),\n"
        "4. al menos un **recurso afectado** (sobre qué).\n\n"
        "Si falta cualquiera, lanza RegistroInvalido.",
        "No puede existir una constancia incompleta en el historial."),
      n("def de(cls", "Registro.de(): un atajo para crear registros",
        "Es un `@classmethod` que arma un Registro a partir de datos sueltos. Recibe:\n\n"
        "- `actor_id`: quién hizo la operación,\n"
        "- `fecha_hora`: cuándo,\n"
        "- `operacion`: qué operación del catálogo,\n"
        "- `*recursos`: los ids afectados, **todos los que hagan falta**,\n"
        "- `**detalle`: datos extra **con nombre**, también los que hagan falta.\n\n"
        "**Caso real**, una reasignación en emergencia.py:\n\n"
        "`Registro.de('op-1', fecha, Operacion.MISION_REASIGNADA, 'em-1', 'mi-3', unidad_anterior='U1', unidad_nueva='U2')`\n\n"
        "1. `*recursos` junta los ids sueltos en una tupla: ('em-1', 'mi-3').\n"
        "2. `**detalle` junta los datos con nombre en un diccionario: {unidad_anterior: 'U1', unidad_nueva: 'U2'}.\n\n"
        "Por último, el detalle se guarda como **pares (clave, texto)**: (('unidad_anterior', 'U1'), ('unidad_nueva', 'U2')).",
        "Quien registra una operación escribe una sola línea legible, y el Registro queda inmutable igual."),
      n("def dato", "dato(): leer un valor del detalle",
        "Responde: «¿qué valor tiene esta clave en el detalle del registro?».\n\n"
        "1. **La firma:** `dato(self, clave: str) -> str | None` recibe el nombre de una clave y devuelve su texto, o **None** si esa clave no está.\n"
        "2. **El return:** `dict(self.detalle)` vuelve a armar el diccionario a partir de los pares guardados y `.get(clave)` busca el valor; si no lo encuentra, devuelve None en lugar de lanzar un error.\n\n"
        "**Ejemplo**, con el registro de la reasignación:\n\n"
        "- `registro.dato('unidad_anterior')` → 'U1'\n"
        "- `registro.dato('justificacion')` → None",
        "PV17: se consulta qué unidades intervinieron en una reasignación sin recorrer el detalle a mano.")),
]

# ═════════ 3 · EL AVISO ═════════
P += [
 paso("avi_valores", 2, "aviso.py: Nota y Descarte", AVI, R(AVI, "class Nota", "El descarte necesita fecha", antes=1),
      "§2.1 y §7.1: un aviso puede recibir notas y puede descartarse con justificación.",
      n("class Nota", "Nota: autor, texto y fecha",
        "Un valor inmutable que se valida al nacer: no existe una nota sin autor, vacía o sin fecha. Si falta algo lanza NotaInvalida."),
      n("class Descarte", "Descarte: operador, justificación y fecha",
        "Mismo molde. Valida primero la justificación porque es la regla central: descartar sin explicar no existe y falla con su error propio, JustificacionVacia.")),
 paso("avi_estados", 2, "aviso.py: los estados del aviso", AVI, R(AVI, "class EstadoAviso", "_ESTADO_POR_ETIQUETA ="),
      "Pendiente, Aceptado y Descartado son clases; el aviso les delega en vez de usar un if.",
      n("class EstadoAviso(Enum)", "EstadoAviso: el nombre público del estado",
        "Es la etiqueta que se muestra y se guarda (pendiente, aceptado, descartado). El objeto estado queda privado: afuera solo sale este nombre."),
      n("class _Estado(ABC)", "_Estado: las preguntas que todo estado responde",
        "ABC marca una clase abstracta: no se puede crear sola. @abstractmethod obliga a cada subclase a implementar el método. El guion bajo inicial (_Estado) avisa que es interno del módulo."),
      n("class _Pendiente", "Pendiente, Aceptado y Descartado",
        "Las tres clases responden las **mismas cuatro preguntas** que define _Estado, pero cada una contesta distinto:\n\n"
        "- **Pendiente**: el único que admite operaciones. Deja agregar notas, y descartar o aceptar le devuelve el estado siguiente.\n"
        "- **Aceptado**: final. Rechaza todo con AvisoNoPendiente.\n"
        "- **Descartado**: final. También rechaza todo con AvisoNoPendiente.\n\n"
        "```\n"
        "              ┌── descartar() ──▶ DESCARTADO  ✕ notas ✕ evaluar\n"
        "PENDIENTE ────┤\n"
        "  ✓ notas     └── aceptar() ───▶ ACEPTADO    ✕ notas ✕ evaluar\n"
        "```\n\n"
        "| | permitir_nota() | descartar() | aceptar() | validar_descarte() |\n"
        "|---|---|---|---|---|\n"
        "| **Pendiente** | ✓ no hace nada | → Descartado | → Aceptado | sin descarte |\n"
        "| **Aceptado** | ✕ error | ✕ error | ✕ error | sin descarte |\n"
        "| **Descartado** | ✕ error | ✕ error | ✕ error | con descarte |",
        "El aviso nunca pregunta «¿en qué estado estoy?» con un if: le delega la pregunta a su estado, y cada estado ya sabe qué contestar. validar_descarte comprueba que un aviso descartado tenga su descarte y los otros dos no."),
      n("_PENDIENTE, _ACEPTADO", "Una sola instancia de cada estado",
        "Los estados no guardan datos propios, así que alcanza con **un único objeto de cada uno**, que se reutiliza en todos los avisos.\n\n"
        "1. **Al cargar el módulo** se crean los tres objetos una sola vez (`_Pendiente()`, `_Aceptado()`, `_Descartado()`) y se guardan en variables privadas.\n"
        "2. **Se arma el diccionario** `_ESTADO_POR_ETIQUETA`, que asocia cada nombre público con su objeto: «cuando busquen DESCARTADO, apunten al objeto ya creado».\n"
        "3. **Cuando llega un aviso guardado en la base de datos** con la etiqueta DESCARTADO, se busca en el diccionario. No se crea un objeto nuevo: se entrega el mismo que ya estaba en memoria.",
        "Se ahorra memoria y todos los avisos descartados comparten exactamente el mismo comportamiento.")),
 paso("avi_init", 2, "aviso.py: Aviso.__init__", AVI, (lambda r: (r[0], r[1] + 1))(R(AVI, "class Aviso:", "gravedad=gravedad_estimada.name.lower())")),
      "Un aviso nace válido, pendiente y con su primer registro.",
      n("_validar_datos(", "Validar antes de guardar nada",
        "`_validar_datos` es una **función privada** del módulo (el guion bajo inicial lo indica): solo se usa dentro de aviso.py.\n\n"
        "Primero se validan todos los datos; si algo falla, el objeto no llega a crearse (R6)."),
      n("aviso_id or str(uuid.uuid4())", "La identidad del aviso",
        "`uuid.uuid4()` genera un **código único** para identificar el aviso.\n\n"
        "La expresión `aviso_id or str(uuid.uuid4())` funciona como un valor por defecto:\n\n"
        "- Si al crear el objeto se pasa un id existente (por ejemplo, al leerlo de la base de datos), se usa ese.\n"
        "- Si no se pasa nada (aviso nuevo), se genera uno automáticamente.",
        "Cada aviso tiene una identidad propia que no cambia en toda su vida."),
      n("self._descripcion = descripcion.strip()", "Atributos privados",
        "El **guion bajo inicial** (`self._id`) marca el dato como **privado**: es interno del aviso y nadie de afuera lo modifica.\n\n"
        "`strip()` elimina los espacios en blanco y saltos de línea que quedan **al principio y al final** de un texto: '  Agua en la calle  ' queda como 'Agua en la calle'. "
        "Un texto de solo espacios ('     ') quedaría vacío; por eso `_validar_datos` lo rechaza antes con hay_texto.",
        "Se guarda siempre un texto limpio y nadie puede alterar los datos del aviso desde afuera."),
      n("self._estado: _Estado = _PENDIENTE", "Todo aviso nace pendiente",
        "Se guarda el estado como objeto (anotado `: _Estado`). Las listas de notas y registros empiezan vacías y el descarte en None (R1)."),
      n("Registro.de(reportante_id", "Nace con su primer registro",
        "Al escribir `self._registros = [ ... ]` se crea una lista con **un único elemento**: el objeto que devuelve `Registro.de(...)`.\n\n"
        "Ese registro se construye con:\n\n"
        "- **Quién** lo hizo: `reportante_id`.\n"
        "- **Cuándo**: `registrado_en`.\n"
        "- **Qué acción**: `Operacion.AVISO_REGISTRADO`.\n"
        "- **Sobre qué recurso**: el id del aviso, más el detalle (tipo y gravedad).\n\n"
        "`gravedad.name.lower()` convierte ALTA en 'alta': `name` es el nombre del miembro del Enum.",
        "El aviso guarda en memoria su primer evento histórico, que ya no se puede alterar (§9).")),
 paso("avi_operaciones", 2, "aviso.py: agregar_nota y descartar", AVI, R(AVI, "def agregar_nota", "return nota")[0:1] + (R(AVI, "def descartar(self, operador_id", "self._registros.append(registro)")[1],),
      "Cada operación pregunta, valida, arma lo nuevo y recién al final modifica.",
      n("self._estado.permitir_nota()", "agregar_nota(): preguntar y validar",
        "Primero el estado (¿admite notas?), después que el autor sea el reportante (NotaDeOtroAutor) y después se crea la Nota, que se valida sola. Todo antes de tocar el aviso."),
      n("self._notas.append(nota)", "Modificar al final",
        "Recién acá se agregan la nota y su registro, y se devuelve la nota. Si algo falló antes, el aviso quedó intacto."),
      n("def descartar", "descartar(): el mismo orden",
        "Pregunta al estado, crea el Descarte (valida la justificación), arma el registro y cambia las tres cosas juntas al final: descarte, estado y registros.")),
 paso("avi_aceptar", 2, "aviso.py: aceptar", AVI, R(AVI, "def aceptar(self, operador_id", "return emergencia"),
      "§2.2 y §7.1: aceptar origina una única emergencia.",
      n("siguiente = self._estado.aceptar()", "aceptar(): origina la emergencia",
        "Mismo orden: pregunta al estado, construye la Emergencia (que valida tipo, gravedad y operador), arma el registro y recién entonces cambia el estado. Devuelve la emergencia creada.",
        "Los datos del aviso no se pisan: la emergencia guarda los que el operador confirmó.")),
 paso("avi_lectura", 2, "aviso.py: lectura del aviso", AVI, R(AVI, "def id(self)", "return tuple(self._registros)", antes=1),
      "Todo se puede leer y nada se puede asignar desde afuera.",
      n("@property", "@property: leer sin poder escribir",
        "Permite escribir `aviso.id` como si fuera un dato, pero **sin setter**: se puede leer y no se puede reasignar.\n\n"
        "Lo mismo vale para reportante, ubicación, tipo, gravedad estimada, descripción y fecha de registro.",
        "Si se pudiera hacer `aviso.descripcion = 'otra cosa'`, se perdería lo que informó el reportante y se rompería R3: las notas agregan información, nunca reemplazan los datos originales."),
      n("return self._estado.etiqueta", "estado: solo el nombre",
        "Devuelve la etiqueta pública (EstadoAviso.PENDIENTE, ACEPTADO o DESCARTADO), nunca el objeto estado interno.",
        "Nadie puede escribir `aviso.estado = DESCARTADO` y saltear el descarte: quedaría un aviso descartado sin justificación ni fecha. El estado solo cambia a través de descartar() o aceptar()."),
      n("return tuple(self._notas)", "notas: se devuelven como tupla",
        "`tuple(...)` entrega una **copia que no se puede modificar**: `aviso.notas.append(...)` no existe.",
        "Si se devolviera la lista interna, cualquiera podría agregar una nota a un aviso ya descartado o aceptado, o con un autor que no es el reportante, y se saltearían R2 y R5."),
      n("return self._descarte", "descarte: un valor inmutable",
        "Devuelve el objeto Descarte tal cual: como es `frozen`, se puede entregar sin copiarlo.",
        "Nadie puede cambiar la justificación ni la fecha después de descartar: queda la explicación original (R4)."),
      n("return tuple(self._registros)", "registros: el historial, solo lectura",
        "También sale como tupla.",
        "El historial no se puede editar ni borrar desde afuera: nadie falsea quién hizo qué ni cuándo (§9).")),
 paso("avi_validar", 2, "aviso.py: _validar_datos", AVI, R(AVI, "def _validar_datos", "fecha y hora de registro"),
      "R1: ningún dato obligatorio puede faltar.",
      n("def _validar_datos", "Una función privada del módulo",
        "`_validar_datos` es una **función privada** (el guion bajo inicial lo indica): no pertenece a ninguna clase y solo se usa dentro de aviso.py, en el constructor del aviso.\n\n"
        "Es una cadena de ifs, uno por regla, y cada uno lanza el error de su motivo."),
      n("not TipoSituacion.contiene", "Catálogo en acción",
        "Usa contiene() para rechazar tipos y gravedades fuera de la lista.")),
]

# ═════════ 4 · PERSONAL, EQUIPO, VEHÍCULOS ═════════
P += [
 paso("per_persona", 3, "personal.py: Persona", PER, R(PER, "@dataclass", "return competencia in"),
      "§5.3: una persona tiene una o varias competencias.",
      n("competencias: frozenset", "frozenset: un conjunto que no cambia",
        "Un conjunto **no tiene repetidos ni orden**; frozenset además es **inmutable**: una vez creado no se le agregan ni quitan elementos.\n\n"
        "- **Sin repetidos**: si se carga dos veces «Rescate», cuenta una sola.\n"
        "- **Inmutable**: nadie puede quitarle una competencia a la persona mientras se verifica si una unidad cubre una misión.\n"
        "- **Seguro para compartir**: la misma persona puede consultarse desde la unidad y desde la flota sin riesgo de que una parte del sistema la cambie a escondidas.",
        "Es el tipo justo para «una o varias competencias»: lo que se verificó al asignar sigue siendo cierto después."),
      n("object.__setattr__", "Cambiar un campo de una clase frozen",
        "Una clase `frozen` no permite asignar atributos, ni siquiera desde adentro.\n\n"
        "Esta línea usa `object.__setattr__` dentro de `__post_init__` (la continuación del constructor `__init__`) como **el único punto de inicialización permitido**: "
        "acepta cualquier colección (lista, tupla, set) y guarda el valor ya blindado como frozenset.\n\n"
        "Cuando el constructor termina, `frozen=True` sella el objeto por completo: queda estrictamente inmutable y bloquea cualquier modificación en el resto del programa."),
      n("if not all(", "all(): ¿todas cumplen?",
        "`all(...)` valida que **absolutamente todas** las competencias ingresadas existan en el catálogo oficial; "
        "`Competencia.contiene(c) for c in ...` las recorre una por una.\n\n"
        "Si al menos una no es válida, el operador `not` activa el error y se rechaza la creación de la persona.",
        "No existe una persona con una competencia inventada."),
      n("def tiene", "tiene(): ¿sabe hacer esto?",
        "Es un método de **consulta rápida** que responde a la pregunta: «¿esta persona tiene la competencia X?».\n\n"
        "`competencia in self.competencias` devuelve True o False.",
        "Es lo que usa la distribución para saber quién puede ocupar cada puesto de una misión.")),
 paso("equ_equipo", 3, "equipamiento.py: Equipo", EQU, R(EQU, "@dataclass", "return replace"),
      "§5.5: el equipamiento tiene categoría y una condición operativa.",
      n("condicion: CondicionOperativa =", "Valor por defecto",
        "Si no se indica la condición, el equipo nace operativo. Un campo con `= valor` es opcional al crear."),
      n("def operativo", "operativo: una propiedad calculada",
        "No guarda un dato: lo **deduce** a partir de la condición.\n\n"
        "Usa `is` para preguntar: «¿la condición de este equipo es exactamente el mismo objeto OPERATIVO que está en el Enum?».\n\n"
        "- Si son el mismo, la condición es OPERATIVO y devuelve **True**.\n"
        "- Si no, devuelve **False**.\n\n"
        "En un Enum existe un solo objeto por miembro, por eso `is` es la forma correcta de comparar.",
        "Una misión de rescate puede preguntar `equipo.operativo` sin conocer el catálogo de condiciones."),
      n("def con_condicion", "con_condicion(): una copia con otra condición",
        "Como el equipo original **no se puede modificar** (es frozen), este método usa `replace()` para crear una **copia exacta** con la nueva condición, dejando el original intacto.\n\n"
        "Al crearse la copia, el constructor vuelve a validar sus datos.",
        "Para «reparar» un equipo fuera de servicio se reemplaza por su copia operativa, y nunca existe un equipo a medio cambiar.")),
 paso("veh_base", 3, "vehiculos.py: Vehiculo", VEH, R(VEH, "@dataclass(frozen=True, kw_only=True)", "no sirve para asistencia sanitaria"),
      "§5.4: cada categoría de vehículo sirve para una misión distinta.",
      n("kw_only=True", "kw_only: campos solo con nombre",
        "Sin `kw_only=True`, Python permite llenar los campos **por posición**, en orden y sin decir su nombre: en `Ambulancia('a1')` asume que 'a1' es el id.\n\n"
        "¿Qué pasa si mañana alguien cambia el orden de los campos y pone primero la condición? `Ambulancia('a1')` intentaría guardar 'a1' como condición y el código se rompería sin avisar.\n\n"
        "Con `kw_only=True`, Python **obliga a escribir el nombre** de cada campo: `Ambulancia(id='a1')`. No importa el orden: siempre queda claro que eso es el id.",
        "Además es necesario técnicamente: TransportePersonas agrega un campo obligatorio (capacidad) después de uno que ya tiene valor por defecto (condición), y eso solo se permite con campos por nombre."),
      n("condicion: CondicionOperativa =", "Un campo opcional con valor por defecto",
        "`condicion: CondicionOperativa = CondicionOperativa.OPERATIVO` es la forma que tiene Python de decir: «este campo es **opcional** y, si no me lo das, por defecto vale **OPERATIVO**».\n\n"
        "- `condicion`: el nombre del campo.\n"
        "- `: CondicionOperativa`: su tipo, un miembro del catálogo.\n"
        "- `= CondicionOperativa.OPERATIVO`: el valor que toma si no se indica.",
        "Un vehículo nuevo se da de alta listo para usarse, sin tener que repetir la condición cada vez."),
      n("class Vehiculo(ABC)", "Una clase abstracta con propiedad abstracta",
        "`@property` junto con `@abstractmethod` obliga a cada subclase a definir su categoría. Vehiculo no se instancia directamente."),
      n("def __post_init__", "Validar id y condición",
        "Igual que en Ubicacion: se valida apenas se crea. La condición tiene que ser un miembro del catálogo."),
      n("def operativo", "operativo: una propiedad calculada",
        "Igual que en Equipo: no guarda un dato, lo **deduce**. Usa `is` para preguntar si la condición del vehículo es exactamente el objeto OPERATIVO del Enum.\n\n"
        "- Si lo es, devuelve **True**: el vehículo puede salir a una misión.\n"
        "- Si no, devuelve **False**: está fuera de servicio.",
        "Es la pregunta que usa verificar_operativo() antes de cualquier asignación."),
      n("def con_condicion", "con_condicion(): una copia con otra condición",
        "Igual que en Equipo: como el vehículo **no se puede modificar**, `replace()` crea una **copia exacta** con la nueva condición y deja el original intacto.\n\n"
        "La copia conserva su clase: una Ambulancia sigue siendo Ambulancia, y el constructor vuelve a validar sus datos.",
        "Declarar un vehículo fuera de servicio, o devolverlo al servicio, nunca deja un objeto a medio cambiar."),
      n("def verificar_operativo", "verificar_operativo(): lanzar si no sirve",
        "Si el vehículo está fuera de servicio lanza VehiculoIncompatible con su id; si está operativo no hace nada."),
      n("def verificar_evacuacion", "Por defecto no sirve para nada",
        "Tres preguntas: evacuar (recibe la cantidad), rescatar y asistir. En la clase base **todas rechazan**; cada categoría sobrescribe solo la suya.\n\n"
        "Si mañana se agrega un vehículo nuevo (por ejemplo, un dron) y se olvida programar si puede evacuar, el sistema asumirá por defecto que **no puede** y lanzará un error.",
        "Es preferible que el sistema rechace una misión a que envíe un vehículo no capacitado a una emergencia real. Lo no declarado queda prohibido.")),
 paso("veh_sub", 3, "vehiculos.py: las tres categorías", VEH, (R(VEH, "class TransportePersonas", "class TransportePersonas", antes=1)[0], R(VEH, "class Ambulancia", "pass")[1]),
      "Cada subclase habilita lo suyo.",
      n("class TransportePersonas", "TransportePersonas: capacidad propia",
        "Hereda de Vehiculo y agrega capacidad_evacuados, el campo propio de esta categoría."),
      n("super().__post_init__()", "super(): usar lo de la clase padre",
        "`super()` llama al método de la clase padre.\n\n"
        "1. Primero se ejecutan las validaciones de Vehiculo: id y condición válidos.\n"
        "2. Después se agrega la regla propia: la capacidad de evacuados tiene que ser un entero positivo.",
        "No se pierden las validaciones del padre y se rechaza cualquier capacidad errónea (0, negativa, decimal o texto)."),
      n("return CategoriaVehiculo.TRANSPORTE", "Implementar lo abstracto",
        "La subclase completa la propiedad abstracta `categoria`, que el padre dejó sin implementar, devolviendo su miembro específico del Enum: TRANSPORTE_DE_PERSONAS."),
      n("def verificar_evacuacion", "Habilita evacuar según la capacidad",
        "Sobrescribe la pregunta de evacuar: acepta si la cantidad entra en la capacidad y rechaza si no."),
      n("return CategoriaVehiculo.VEHICULO_DE_RESCATE", "VehiculoRescate: su categoría",
        "Lo mismo que en TransportePersonas: implementa la propiedad abstracta `categoria`, esta vez devolviendo `CategoriaVehiculo.VEHICULO_DE_RESCATE`."),
      n("def verificar_rescate", "VehiculoRescate: habilita rescatar",
        "Sobrescribe solo la pregunta de rescate. `pass` significa «no hacer nada»: no lanzar el error equivale a aceptar.\n\n"
        "Evacuar y asistir siguen rechazados por defecto."),
      n("return CategoriaVehiculo.AMBULANCIA", "Ambulancia: su categoría",
        "Lo mismo que en VehiculoRescate: implementa la propiedad abstracta `categoria`, esta vez devolviendo `CategoriaVehiculo.AMBULANCIA`.",
        "Así, cada vehículo define su propia identidad y el sistema sabe qué es sin usar condicionales."),
      n("def verificar_asistencia", "Ambulancia: habilita la asistencia sanitaria",
        "Misma idea con verificar_asistencia: `pass` acepta. Evacuar y rescatar siguen rechazados por defecto.")),
]

# ═════════ 5 · DISTRIBUCIÓN Y UNIDAD ═════════
P += [
 paso("dis_funcion", 4, "distribucion.py: existe_distribucion", DIS, R(DIS, "from collections.abc", "return False"),
      "§5.3 y §8.2: cada puesto de la misión lo ocupa una persona distinta.",
      n("from collections.abc import Sequence", "Sequence: cualquier lista o tupla",
        "Se usa solo como tipo: dice que la función acepta una secuencia ordenada (lista o tupla) de puestos."),
      n("if not puestos", "Caso base de la recursión",
        "Una función recursiva se llama a sí misma. Sin puestos que cubrir ya está resuelto: devuelve True. Es el punto donde la recursión termina."),
      n("primero, resto =", "Cortar la lista: slicing",
        "puestos[0] es el primero y puestos[1:] es todo menos el primero. Dos asignaciones en una línea: primero, resto = a, b."),
      n("enumerate(personas)", "enumerate: el índice y el elemento",
        "Recorre las personas dando, en cada vuelta, su posición (indice) y la persona."),
      n("personas[:indice] +", "Sacar a la persona elegida",
        "personas[:indice] es lo que está antes de ella y personas[indice + 1:] lo que está después; sumadas, el grupo sin esa persona. Con ese grupo se resuelve el resto de los puestos."),
      n("return False", "Ninguna sirvió",
        "Si ninguna persona logra cubrir el primer puesto y los demás, no hay forma de repartir: devuelve False. Es el «retroceso» de la búsqueda.")),
 paso("uni_condicion", 4, "unidad.py: la condición de servicio", UNI, R(UNI, "class _Condicion", "_HABILITADA, _EN_MANTENIMIENTO"),
      "§8.4: una unidad puede estar habilitada, en mantenimiento o fuera de servicio.",
      n("class _Condicion", "_Condicion: otro State",
        "Mismo patrón que el aviso: una base abstracta con la pregunta verificar_habilitada() y una clase por condición."),
      n("class _Habilitada", "Habilitada: acepta",
        "No hace nada (pass), o sea que no lanza error: la unidad puede recibir misiones."),
      n("class _EnMantenimiento", "En mantenimiento y fuera de servicio: rechazan",
        "Lanzan UnidadNoHabilitada con el motivo: «está en mantenimiento» o «está fuera de servicio»."),
      n("_HABILITADA, _EN_MANTENIMIENTO", "Tres objetos únicos",
        "Como en el aviso: un objeto por condición, reutilizado.")),
 paso("uni_init", 4, "unidad.py: Unidad.__init__", UNI, R(UNI, "class Unidad:", "self._registros: list[Registro] = []"),
      "§5.2: una unidad agrupa jefe, personal, vehículo y equipamiento.",
      n("personal: tuple[Persona, ...] = ()", "Parámetros opcionales",
        "personal y equipamiento tienen `= ()`: se pueden omitir y valen tupla vacía. Una unidad siempre tiene jefe y vehículo; el resto es opcional."),
      n("dotacion = (jefe, *personal)", "(jefe, *personal): desempaquetar",
        "*personal abre la tupla dentro de otra: arma (jefe, p1, p2, …). La dotación incluye al jefe."),
      n("len({p.id for p in dotacion})", "Detectar repetidos con un conjunto",
        "{p.id for p in dotacion} arma un conjunto de ids, que no admite repetidos. Si tiene menos elementos que la dotación, alguien figuraba dos veces."),
      n("self._personal: dict", "Diccionarios por id",
        "{p.id: p for p in dotacion} arma un diccionario id → persona (comprensión de diccionario). Buscar por id es directo. Del jefe solo se guarda el id: está en el diccionario de personal."),
      n("self._mision_id: str | None", "Condición y misión: dos cosas distintas",
        "Estar habilitada no es lo mismo que estar comprometida (§8.4): se guardan por separado. `str | None` significa «un id o nada».")),
 paso("uni_lectura", 4, "unidad.py: lectura y consultas", UNI, R(UNI, "def personal(self)", "for e in self._equipamiento.values())", antes=1),
      "La unidad responde preguntas sin entregar sus colecciones.",
      n("def personal", "personal: toda la dotación",
        "Devuelve una tupla con todas las personas, jefe incluido, contado una sola vez."),
      n("def tiene_persona", "Consultas por id",
        "tiene_persona, usa_vehiculo y tiene_equipo responden sí o no. `id in diccionario` busca entre las claves."),
      n("any(e.categoria", "any(): ¿alguno cumple?",
        "any(...) es verdadero si al menos un elemento cumple la condición. Acá: ¿hay un equipo de esa categoría y operativo?")),
 paso("uni_compromiso", 4, "unidad.py: comprometer, liberar y exigir_jefe", UNI, R(UNI, "def comprometer", "no es el jefe de la unidad"),
      "§8.2 y §8.3: la unidad verifica todo y recién entonces se reserva.",
      n("self._condicion.verificar_habilitada()", "comprometer(): las condiciones en orden",
        "Habilitada, libre, vehículo operativo y compatible, personal y equipamiento. Cada una lanza su motivo; solo si todas pasan guarda el id de la misión."),
      n("def liberar", "liberar(): solo la misión que reservó",
        "Recupera la disponibilidad dejando _mision_id en None, pero solo si quien lo pide es la misión que la reservó."),
      n("def exigir_jefe", "exigir_jefe(): solo el jefe",
        "Compara el id de la persona con el del jefe y lanza NoEsJefeDeLaUnidad si no coincide. Lo usa la misión antes de iniciar o finalizar.")),
 paso("uni_admin", 4, "unidad.py: administrar el personal, el vehículo y el equipo", UNI, R(UNI, "def incorporar_personal", "self._registros.append(registro)", antes=0)[0:1] + (R(UNI, "def cambiar_condicion_equipo", "self._registros.append(registro)")[1],),
      "§2.4: se agregan, quitan y cambian recursos, siempre con la misma secuencia.",
      n("def incorporar_personal", "La secuencia de todos los mutadores",
        "1) _exigir_modificable() 2) validar 3) armar el Registro 4) cambiar y agregar el registro al final. Si algo falla antes del paso 4, la unidad queda como estaba."),
      n("del self._personal", "retirar_personal(): el jefe no se retira",
        "`del diccionario[clave]` borra esa entrada. Antes se verifica que la persona integre la unidad y que no sea el jefe."),
      n("def cambiar_vehiculo", "Cambiar el vehículo y su condición",
        "cambiar_vehiculo reemplaza el vehículo y deja el anterior en el detalle del registro. cambiar_condicion_vehiculo usa con_condicion, que valida antes de tocar."),
      n("def incorporar_equipo", "Equipo: incorporar, retirar y cambiar condición",
        "Mismos pasos que con el personal. El diccionario por id permite reemplazar un equipo por su copia con otra condición.")),
 paso("uni_servicio", 4, "unidad.py: condición de servicio e internos", UNI, R(UNI, "def declarar_en_mantenimiento", "no se modifica"),
      "La unidad cambia su condición de servicio con los mismos cuidados.",
      n("def declarar_en_mantenimiento", "Tres métodos finos",
        "declarar_en_mantenimiento, declarar_fuera_de_servicio y restablecer_servicio solo eligen el estado y delegan en _cambiar_condicion."),
      n("def registrar_alta", "registrar_alta(): el primer registro",
        "La flota la llama al incorporar la unidad. Deja el registro «unidad registrada» con la base en el detalle."),
      n("def _cambiar_condicion", "_cambiar_condicion(): el cambio común",
        "Es privado (empieza con _). Exige que se pueda modificar, arma el registro con la condición anterior y la nueva, y recién después cambia."),
      n("def _exigir_modificable", "_exigir_modificable(): comprometida no se toca",
        "Si la unidad tiene una misión, lanza UnidadComprometida. Es la primera línea de todos los métodos que modifican (§8.4).")),
]

# ═════════ 6 · LA MISIÓN ═════════
P += [
 paso("mis_valores", 5, "mision.py: Novedad, Resultado y VistaMision", MIS, R(MIS, "class Novedad", "resultado: Resultado | None", antes=1),
      "§2.3 y §8.1: lo que el jefe informa durante y al terminar una misión.",
      n("class Novedad", "Novedad: autor, texto y fecha",
        "Valor inmutable: lo que el jefe informa mientras la misión se ejecuta. Se valida al nacer, como Nota."),
      n("class Resultado", "Resultado: qué se logró y qué se hizo",
        "Exige un resultado del catálogo, las tareas descriptas y la fecha. `satisfactorio` es una propiedad que dice si el resultado fue satisfactorio."),
      n("class VistaMision", "VistaMision: una foto de solo lectura",
        "Copia de los datos de la misión (id, tipo, estado, unidad, novedades, resultado) que sale de la emergencia. Con ella se mira la misión sin poder cambiarla.")),
 paso("mis_estados", 5, "mision.py: los cinco estados", MIS, R(MIS, "class EstadoMision", "_FINALIZADA, _CANCELADA ="),
      "§8.1: no se admiten transiciones arbitrarias.",
      n("class EstadoMision", "EstadoMision: el nombre público",
        "Pendiente, asignada, en ejecución, finalizada y cancelada. Es lo que se muestra y se guarda; el objeto estado queda privado."),
      n("def _no_admite", "_no_admite(): el error de la base",
        "Arma el error «una misión X no puede Y». Los métodos de abajo lo lanzan con `raise self._no_admite(...)`."),
      n("def asignar(self) -> _Estado", "Todo se rechaza por defecto",
        "La base rechaza cada operación (asignar, reasignar, rechazar, iniciar, novedad, finalizar, cancelar). Un estado concreto sobrescribe solo las que admite."),
      n("def verificar_concluida", "Dos preguntas para la emergencia",
        "verificar_concluida() lanza MisionSinConcluir si la misión sigue abierta; exito() dice si terminó bien. Por defecto: no concluida y no exitosa."),
      n("class _Pendiente", "Pendiente y Asignada: sus salidas",
        "Pendiente puede asignarse o cancelarse. Asignada puede reasignarse (sigue asignada), rechazarse (vuelve a pendiente), iniciarse o cancelarse. Cada método devuelve el estado siguiente."),
      n("class _EnEjecucion", "En ejecución: novedades y finalizar",
        "Admite novedades (pass: acepta) y finalizar, que lleva a Finalizada. No se puede cancelar una misión ya en ejecución."),
      n("class _Finalizada", "Finalizada y Cancelada: terminales",
        "No admiten ninguna operación. Ambas pisan verificar_concluida con `pass`; solo Finalizada con resultado satisfactorio cuenta como éxito."),
      n("_PENDIENTE, _ASIGNADA", "Un objeto por estado",
        "Igual que en el aviso: una instancia reutilizable de cada estado.")),
 paso("mis_asignacion", 5, "mision.py: la unidad asignada (Null Object)", MIS, R(MIS, "class _Asignacion", "_SIN_UNIDAD ="),
      "Una misión pendiente todavía no tiene unidad: igual debe poder responder.",
      n("class _Asignacion", "_Asignacion: lo que toda asignación sabe hacer",
        "Base abstracta con dos operaciones: liberar y exigir_jefe. `...` es el cuerpo vacío de un método abstracto."),
      n("class _SinUnidad", "_SinUnidad: no hace nada",
        "Para una misión sin unidad: liberar no hace nada y exigir_jefe lanza NoEsJefeDeLaUnidad. Es el patrón Null Object: en lugar de None, un objeto que responde."),
      n("class _ConUnidad", "_ConUnidad: delega en la unidad real",
        "Guarda la unidad y su id; liberar y exigir_jefe le pasan la operación a la unidad."),
      n("_SIN_UNIDAD =", "Un solo _SinUnidad",
        "Como no guarda datos, se crea un único objeto compartido por todas las misiones sin unidad.")),
 paso("mis_base", 5, "mision.py: Mision, la clase abstracta", MIS, R(MIS, "class Mision(ABC)", "if situacion not in", antes=0)[0:1] + (R(MIS, "def _exigir_equipo", "Falta un")[1],),
      "§6: cada tipo de misión declara lo suyo y la clase base hace lo común.",
      n("tipo: TipoMision", "Atributos de clase declarados, sin valor",
        "Estas tres líneas solo anotan que cada subclase debe definir su tipo, sus situaciones admitidas y sus puestos. Están en la clase y no en cada objeto."),
      n("def __init__", "Mision.__init__: nace pendiente y sin unidad",
        "Valida el objetivo, genera el id y arranca en _PENDIENTE con _SIN_UNIDAD. Las novedades empiezan vacías y el resultado en None."),
      n("def verificar_vehiculo", "Dos métodos que cada tipo define",
        "verificar_vehiculo (doble despacho: le pregunta al vehículo) y verificar_equipamiento son abstractos: cada subclase los implementa."),
      n("def verificar_personal", "verificar_personal(): personas distintas",
        "Llama a existe_distribucion con los puestos de la misión y, si no hay forma de cubrirlos, lanza PersonalInsuficiente con la lista de competencias."),
      n("def verificar_situacion", "verificar_situacion(): ¿sirve para esta emergencia?",
        "Rechaza con MisionIncompatible si la situación no está en situaciones_admitidas (§6.4)."),
      n("def _exigir_equipo", "_exigir_equipo(): helper común",
        "Pregunta a la unidad si tiene un equipo operativo de la categoría y, si no, lanza EquipamientoInsuficiente. Lo reutilizan Rescate y AsistenciaSanitaria.")),
 paso("mis_operador", 5, "mision.py: asignar, reasignar y cancelar", MIS, (R(MIS, "def asignar(self, unidad", "def asignar(self, unidad")[0], R(MIS, "def cancelar(self) -> None", "self._estado = siguiente")[1]),
      "§2.2: lo que hace el operador sobre una misión.",
      n("siguiente = self._estado.asignar()", "asignar(): primero preguntar, después comprometer",
        "El estado dice a cuál pasa. unidad.comprometer(self) verifica todo; si falla, no cambió nada. Recién ahí guarda _ConUnidad y cambia de estado."),
      n("def reasignar", "reasignar(): la nueva primero",
        "Compromete la unidad nueva antes de liberar la anterior: si la nueva falla, la anterior sigue asignada."),
      n("def cancelar", "cancelar(): liberar y quedar sin unidad",
        "Libera la unidad reservada (si había) y vuelve a _SIN_UNIDAD antes de cambiar de estado.")),
 paso("mis_jefe", 5, "mision.py: lo que hace el jefe de la unidad", MIS, R(MIS, "def rechazar(self, jefe_id", "self._estado = siguiente", antes=0)[0:1] + (R(MIS, "def finalizar(self, jefe_id", "self._estado = siguiente")[1],),
      "§2.3: el jefe rechaza, inicia, informa novedades y finaliza.",
      n("def rechazar", "rechazar(): justificar y volver a pendiente",
        "Solo el jefe, y con justificación. Libera la unidad, queda sin unidad y la misión vuelve a Pendiente."),
      n("def iniciar", "iniciar(): solo el jefe",
        "Pregunta al estado, comprueba que sea el jefe y cambia a En ejecución."),
      n("def registrar_novedad", "registrar_novedad(): solo en ejecución",
        "El estado lo permite solo En ejecución. Crea la Novedad (que se valida sola) y la agrega a la lista."),
      n("def finalizar", "finalizar(): validar el resultado antes de liberar",
        "Comprueba estado y jefe, arma el Resultado (se valida) y recién después libera la unidad y cambia a Finalizada.")),
 paso("mis_lectura", 5, "mision.py: lo que la emergencia le pregunta", MIS, (R(MIS, "def es_exitosa", "def es_exitosa")[0] - 3, R(MIS, "tuple(self._novedades), self._resultado)", "tuple(self._novedades), self._resultado)")[1]),
      "La emergencia pregunta sin poder modificar.",
      n("def verificar_concluida", "verificar_concluida() y es_exitosa()",
        "La misión le pasa la pregunta a su estado. La emergencia las usa para decidir si se puede cerrar."),
      n("def estado", "Lectura: estado y unidad",
        "estado devuelve solo la etiqueta pública; unidad_id sale de la asignación, sea real o _SinUnidad (None)."),
      n("def vista", "vista(): la foto de solo lectura",
        "Arma una VistaMision con los datos actuales y una tupla de novedades. Es lo que sale de la emergencia.")),
 paso("mis_tipos", 5, "mision.py: Evacuación, Rescate y Asistencia sanitaria", MIS, R(MIS, "class Evacuacion", "EQUIPO_SANITARIO)"),
      "§6.1 a §6.3: tres tipos de misión con requisitos distintos.",
      n("tipo = TipoMision.EVACUACION", "Cada tipo declara sus datos",
        "tipo, situaciones_admitidas (frozenset: no se evacúa en un accidente vial) y puestos (conducción y evacuación). Son atributos de clase, iguales para todas las evacuaciones."),
      n("super().__init__", "Evacuacion.__init__: un dato más",
        "Valida la cantidad de personas y llama a super().__init__ para que la base valide el objetivo y cree el id."),
      n("vehiculo.verificar_evacuacion", "Doble despacho",
        "La misión no compara categorías: le pregunta al vehículo. Cada categoría de vehículo responde lo suyo."),
      n("class Rescate", "Rescate: conductor y dos rescatistas",
        "Puestos: conducción y dos de rescate. Pide un equipo de rescate operativo con _exigir_equipo."),
      n("class AsistenciaSanitaria", "Asistencia sanitaria: ambulancia y primeros auxilios",
        "Puestos: conducción y primeros auxilios. Pide una ambulancia y un equipo sanitario operativo.")),
]

# ═════════ 7 · LA EMERGENCIA Y LA FLOTA ═════════
P += [
 paso("eme_estados", 6, "emergencia.py: abierta o cerrada", EME, R(EME, "class EstadoEmergencia", "_ABIERTA, _CERRADA"),
      "§7.2: una emergencia solo se cierra si todas sus misiones terminaron y alguna fue exitosa.",
      n("class EstadoEmergencia", "EstadoEmergencia: el nombre público", "Abierta o cerrada: lo que se muestra y se guarda."),
      n("def permitir_modificaciones", "_Estado: dos preguntas",
        "permitir_modificaciones() lanza EmergenciaCerrada si ya no se puede operar; cerrar() recibe las misiones y devuelve el estado siguiente. Mismo patrón abstracto que los otros State."),
      n("class _Abierta", "Abierta: permite todo y puede cerrarse",
        "Acepta modificaciones (pass). Para cerrar recorre las misiones: `for mision in misiones` pide a cada una verificar_concluida(), y `any(...)` exige que al menos una sea exitosa."),
      n("class _Cerrada", "Cerrada: rechaza todo",
        "Cualquier modificación y un segundo cierre lanzan EmergenciaCerrada."),
      n("_ABIERTA, _CERRADA", "Dos objetos únicos", "Una instancia de cada estado, reutilizada.")),
 paso("eme_init", 6, "emergencia.py: Emergencia.__init__", EME, R(EME, "class Emergencia:", "        ]"),
      "§7.2: una emergencia nace al aceptar un aviso.",
      n("if not hay_texto(aviso_id)", "Validar el origen",
        "Exige el aviso de origen, el reportante y la ubicación; después el tipo y la gravedad del catálogo; después operador y fecha. Cada grupo lanza AceptacionInvalida."),
      n("self._estado: _Estado = _ABIERTA", "Nace abierta",
        "Guarda sus datos privados y empieza en el estado Abierta."),
      n("self._misiones: dict", "Las misiones por id",
        "Un diccionario id → misión: la emergencia es la dueña de sus misiones."),
      n("Operacion.EMERGENCIA_CREADA", "Nace con su primer registro",
        "Una lista con un solo Registro: «emergencia creada» con el tipo y la gravedad confirmados.")),
 paso("eme_operador", 6, "emergencia.py: lo que hace el operador", EME, (R(EME, "def crear_mision", "def crear_mision")[0], R(EME, "def cancelar_mision", "self._registros.append(registro)")[1]),
      "§2.2: crear, asignar, reasignar y cancelar misiones.",
      n("def crear_mision", "crear_mision(): agregar una misión",
        "Pregunta al estado, verifica que el tipo de misión sirva para la situación, arma el registro y recién al final agrega la misión al diccionario."),
      n("def asignar_mision", "asignar_mision(): coordina y delega",
        "Estado, búsqueda de la misión por id, registro y mision.asignar(unidad), que verifica todo. El registro se guarda solo si la misión aceptó."),
      n("def reasignar_mision", "reasignar_mision(): quién era y quién es",
        "Guarda la unidad anterior antes de reasignar y deja ambas en el detalle del registro. `str(anterior)` convierte a texto aunque sea None."),
      n("def cancelar_mision", "cancelar_mision(): el registro antes de cancelar",
        "Toma la unidad que se va a liberar, arma el registro y recién después cancela la misión.")),
 paso("eme_jefe", 6, "emergencia.py: lo que hace el jefe de unidad", EME, (R(EME, "def rechazar_mision", "def rechazar_mision")[0], R(EME, "def finalizar_mision", "tareas=tareas))")[1]),
      "§2.3: rechazar, iniciar, informar novedades y finalizar. Siempre pasan por la emergencia.",
      n("def rechazar_mision", "El mismo molde en las cuatro",
        "Cada operación pide a la emergencia estar abierta, busca la misión, delega en ella y deja el registro. La misión valida que sea el jefe."),
      n("def registrar_novedad", "registrar_novedad(): la novedad queda en el detalle",
        "`novedad=texto` pasa el texto como dato con nombre al detalle del registro."),
      n("def finalizar_mision", "finalizar_mision(): resultado y tareas",
        "Guarda la unidad antes de finalizar (después queda libre) y registra el resultado y las tareas.")),
 paso("eme_cierre", 6, "emergencia.py: cerrar", EME, R(EME, "def cerrar(self, supervisor_id", "self._registros.append(registro)"),
      "§7.2: el supervisor cierra la emergencia.",
      n("self._estado.cerrar(", "cerrar(): el estado decide",
        "Le pasa las misiones al estado: Abierta verifica que todas terminaron y alguna fue exitosa; Cerrada lanza error. Recién después se cambia el estado y se agrega el registro."),
      ),
 paso("eme_lectura", 6, "emergencia.py: lectura y prioridad", EME, (R(EME, "def id(self)", "def id(self)", antes=1)[0], R(EME, "return tuple(sorted(abiertas", "return tuple(sorted(abiertas")[1]),
      "§4: las emergencias abiertas se atienden de más grave a menos grave.",
      n("def misiones", "misiones: solo fotos de lectura",
        "`tuple(m.vista() for m in ...)` es una expresión generadora: recorre las misiones y arma una tupla con la VistaMision de cada una. La emergencia nunca entrega la misión misma."),
      n("def clave_de_prioridad", "clave_de_prioridad: qué se ordena",
        "Una tupla (-gravedad, creada_en): el signo menos pone la Alta primero y, a igual gravedad, gana la más antigua."),
      n("def _mision", "_mision(): buscar o NoEncontrado",
        "Función privada que busca por id y lanza NoEncontrado si no está."),
      n("def abiertas_por_prioridad", "abiertas_por_prioridad(): una función de módulo",
        "(e for e in emergencias if ...) filtra solo las abiertas; sorted(..., key=lambda e: e.clave_de_prioridad) las ordena. `lambda e: ...` es una mini función sin nombre; devuelve una tupla.")),
 paso("flo_consulta", 6, "flota.py: BaseOperativa y Flota", FLO, R(FLO, "@dataclass", "if u.base_id == base_id"),
      "§5.1 y §5.2: la flota conoce todas las bases y unidades.",
      n("class BaseOperativa", "BaseOperativa: un valor",
        "Mismo molde que Ubicacion: identificación, nombre y ubicación obligatorios."),
      n("class Flota", "Flota: dos diccionarios",
        "Guarda bases y unidades por id. Es la raíz de consistencia: la regla de no repetir recursos involucra a todas las unidades."),
      n("def unidad(self", "unidad(): buscar o NoEncontrado",
        "`if unidad_id not in diccionario` comprueba la clave antes de leer."),
      n("def unidades_de", "unidades_de(): filtrar con una expresión",
        "`tuple(u for u in ... if condición)` devuelve solo las unidades de esa base.")),
 paso("flo_altas", 6, "flota.py: registrar bases e incorporar unidades", FLO, R(FLO, "def registrar_base", "self._unidades[unidad.id] = unidad"),
      "Dar de alta exige revisar a todas las demás.",
      n("def registrar_base", "registrar_base(): sin duplicados", "Si ya existe una base con ese id, lanza RecursoDuplicado; si no, la guarda."),
      n("def incorporar_unidad", "incorporar_unidad(): revisar todo y después guardar",
        "Verifica que exista la base, que la unidad no esté repetida y que ninguna persona, vehículo o equipo ya esté en otra unidad. Recién después registra el alta y guarda la unidad.")),
 paso("flo_cambios", 6, "flota.py: cambios que miran a las demás unidades", FLO, R(FLO, "def incorporar_personal", "unidad.incorporar_equipo(equipo, actor_id, fecha_hora)"),
      "Agregar un recurso a una unidad existente también puede chocar con otra unidad.",
      n("def incorporar_personal", "Primero la flota, después la unidad",
        "La flota busca la unidad y comprueba que el recurso esté libre en las demás (salvo en ella misma); si pasa, delega en la unidad, que valida lo suyo."),
      n("def cambiar_vehiculo", "Vehículo y equipo: el mismo orden", "cambiar_vehiculo e incorporar_equipo hacen lo mismo con sus propios chequeos.")),
 paso("flo_unicidad", 6, "flota.py: unicidad entre unidades", FLO, R(FLO, "def _exigir_persona_libre", "El equipo {equipo_id}"),
      "§5.2: una persona, vehículo o equipo no puede estar en dos unidades.",
      n("def _exigir_persona_libre", "_exigir_persona_libre(): recorrer las unidades",
        "Recorre todas las unidades menos la indicada (salvo_unidad_id, que puede ser None); si alguna ya tiene a la persona, lanza RecursoDuplicado con la unidad."),
      n("def _exigir_vehiculo_libre", "Lo mismo para vehículos y equipos",
        "Cambia solo la pregunta: usa_vehiculo o tiene_equipo.")),
]
