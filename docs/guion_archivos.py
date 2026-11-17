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
        "`@dataclass` arma el constructor a partir de los campos declarados. Los dos parámetros agregan:\n"
        "\n"
        "1. `frozen=True`: una vez creada, la ubicación **no se puede modificar**,\n"
        "2. `slots=True`: el objeto guarda **solo los campos declarados** (dirección y localidad); no se le pueden agregar atributos por error y ocupa menos memoria.",
        "Una ubicación es un valor: dos con los mismos datos son la misma, y nadie la cambia a escondidas."),
      n("def __post_init__", "__post_init__: validar al crearse",
        "Se ejecuta justo después del constructor. Exige dos cosas:\n"
        "\n"
        "1. una **dirección** con contenido,\n"
        "2. una **localidad** con contenido.\n"
        "\n"
        "Si falta cualquiera, `raise` lanza DatoDeAvisoInvalido.",
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
        "Se lanza cuando un registro del historial no tiene alguna de estas cuatro cosas:\n"
        "\n"
        "1. un **actor** (quién),\n"
        "2. una **fecha y hora** (cuándo),\n"
        "3. una **operación** del catálogo (qué),\n"
        "4. al menos un **recurso afectado** (sobre qué).",
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
        "Un registro es **inmutable**, igual que Ubicacion. Guarda cinco campos:\n"
        "\n"
        "1. `actor_id`: quién hizo la operación,\n"
        "2. `fecha_hora`: cuándo,\n"
        "3. `operacion`: qué operación del catálogo,\n"
        "4. `recursos`: sobre qué ids; `tuple[str, ...]` es una tupla de textos de cualquier largo,\n"
        "5. `detalle`: datos extra como pares (clave, texto); `= ()` lo hace opcional, por defecto vacío.",
        "Cada constancia del historial tiene siempre la misma forma y no se puede alterar (§9)."),
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
        "Un **valor inmutable** (`frozen`) que se valida apenas se crea, en `__post_init__`. Exige tres cosas:\n"
        "\n"
        "1. un **autor** (quién la escribe),\n"
        "2. un **texto** con contenido (qué dice),\n"
        "3. una **fecha y hora** (cuándo).\n"
        "\n"
        "Si falta cualquiera, lanza NotaInvalida.",
        "No puede existir una nota sin autor, vacía o sin fecha (R2)."),
      n("class Descarte", "Descarte: operador, justificación y fecha",
        "Mismo molde que Nota: un **valor inmutable** que se valida al crearse. Exige tres cosas, en este orden:\n"
        "\n"
        "1. una **justificación** con contenido (por qué se descarta) → si falta, JustificacionVacia,\n"
        "2. un **operador** (quién descarta) → si falta, DescarteInvalido,\n"
        "3. una **fecha y hora** (cuándo) → si falta, DescarteInvalido.\n"
        "\n"
        "La justificación va primero porque es la regla central: descartar sin explicar no existe.",
        "No puede existir un descarte sin explicación, sin responsable o sin fecha (R4).")),
 paso("avi_estados", 2, "aviso.py: los estados del aviso", AVI, R(AVI, "class EstadoAviso", "_ESTADO_POR_ETIQUETA ="),
      "Pendiente, Aceptado y Descartado son clases; el aviso les delega en vez de usar un if.",
      n("class EstadoAviso(Enum)", "EstadoAviso: el nombre público del estado",
        "Es la etiqueta que se muestra y se guarda (pendiente, aceptado, descartado). El objeto estado queda privado: afuera solo sale este nombre."),
      n("class _Estado(ABC)", "_Estado: las preguntas que todo estado responde",
        "`ABC` marca una **clase abstracta**: no se puede crear sola. `@abstractmethod` obliga a cada subclase a implementar cuatro métodos:\n"
        "\n"
        "1. `permitir_nota()`: ¿admite notas?,\n"
        "2. `descartar()`: ¿se puede descartar?,\n"
        "3. `aceptar()`: ¿se puede aceptar?,\n"
        "4. `validar_descarte()`: ¿el descarte es coherente con este estado?\n"
        "\n"
        "El guion bajo inicial (`_Estado`) indica que es una clase **privada** del módulo.",
        "Si se agrega un estado y le falta responder alguna pregunta, Python no deja crearlo."),
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
        "Al terminar el constructor, el aviso queda así:\n"
        "\n"
        "1. **estado**: `_PENDIENTE`, guardado como objeto (anotado `: _Estado`),\n"
        "2. **notas**: lista vacía,\n"
        "3. **descarte**: None, todavía no hay,\n"
        "4. **registros**: la lista que se arma en la línea siguiente.",
        "Regla R1: un aviso recién registrado está pendiente, sin notas y sin descarte."),
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
        "Antes de tocar el aviso, comprueba tres cosas en orden:\n"
        "\n"
        "1. **el estado**: `self._estado.permitir_nota()` lanza AvisoNoPendiente si el aviso ya fue evaluado,\n"
        "2. **el autor**: si no es el reportante del aviso, lanza NotaDeOtroAutor,\n"
        "3. **la nota**: al crear `Nota(...)` se valida sola (autor, texto y fecha).\n"
        "\n"
        "Después arma el registro NOTA_AGREGADA. Si cualquier paso falla, el aviso queda intacto.",
        "Reglas R2, R5 y R6: solo se agregan notas válidas, del reportante, a un aviso pendiente."),
      n("self._notas.append(nota)", "Modificar al final",
        "Recién acá cambia el aviso, cuando ya no puede fallar nada:\n"
        "\n"
        "1. se agrega la nota a la lista,\n"
        "2. se agrega su registro al historial,\n"
        "3. se devuelve la nota creada.",
        "Regla R6: una operación rechazada no deja cambios a medias."),
      n("def descartar", "descartar(): el mismo orden",
        "Mismo orden que agregar_nota: primero todo lo que puede fallar, al final los cambios.\n"
        "\n"
        "1. **pregunta al estado**: `self._estado.descartar()` devuelve el estado siguiente o lanza AvisoNoPendiente,\n"
        "2. **crea el Descarte**, que valida la justificación, el operador y la fecha,\n"
        "3. **arma el registro** AVISO_DESCARTADO con la justificación.\n"
        "\n"
        "Recién entonces cambia tres cosas juntas: el descarte, el estado y los registros.",
        "Reglas R4, R5 y R6: un descarte inválido o repetido no deja el aviso a medio descartar.")),
 paso("avi_aceptar", 2, "aviso.py: aceptar", AVI, R(AVI, "def aceptar(self, operador_id", "return emergencia"),
      "§2.2 y §7.1: aceptar origina una única emergencia.",
      n("siguiente = self._estado.aceptar()", "aceptar(): origina la emergencia",
        "Mismo orden que descartar:\n"
        "\n"
        "1. **pregunta al estado**: `self._estado.aceptar()` devuelve el estado siguiente o lanza AvisoNoPendiente,\n"
        "2. **construye la Emergencia**, que valida tipo, gravedad, operador y fecha,\n"
        "3. **arma el registro** AVISO_ACEPTADO.\n"
        "\n"
        "Recién entonces cambia el estado, guarda el registro y **devuelve la emergencia** creada.",
        "Los datos del aviso no se pisan: la emergencia guarda el tipo y la gravedad que el operador confirmó (§2.2, §7.1).")),
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
        "Igual que en Ubicacion: `__post_init__` valida apenas se crea el vehículo. Exige dos cosas:\n"
        "\n"
        "1. un **id** con contenido,\n"
        "2. una **condición** que pertenezca al catálogo.\n"
        "\n"
        "Si falta cualquiera, lanza RecursoInvalido.",
        "No existe un vehículo sin identificación o con una condición inventada."),
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
        "`Sequence` es un **tipo genérico** de la biblioteca estándar: significa «cualquier colección ordenada», ya sea lista o tupla.\n"
        "\n"
        "Se usa **solo para anotar** el parámetro `puestos`: la función acepta los puestos en cualquiera de las dos formas.",
        "La misión puede pasar sus puestos como tupla sin que la función exija un tipo exacto."),
      n("if not puestos", "Caso base de la recursión",
        "Una función **recursiva** se resuelve llamándose a sí misma con un problema más chico. Necesita un punto donde **dejar de llamarse**: el caso base.\n"
        "\n"
        "Acá el caso base es: **no quedan puestos por cubrir**. Si todos los puestos ya tienen a alguien, el reparto existe y devuelve **True**.",
        "Sin caso base, la función se llamaría a sí misma para siempre."),
      n("primero, resto =", "Cortar la lista: slicing",
        "Separa el problema en dos partes:\n"
        "\n"
        "1. `puestos[0]`: el **primer** puesto, el que se intenta cubrir ahora,\n"
        "2. `puestos[1:]`: **todos los demás**, que se resuelven en la próxima llamada.\n"
        "\n"
        "`primero, resto = a, b` asigna los dos valores en una sola línea.\n"
        "\n"
        "Ejemplo: con (conducción, rescate, rescate), `primero` es conducción y `resto` es (rescate, rescate).",
        "En cada llamada queda un puesto menos: así se llega al caso base."),
      n("enumerate(personas)", "enumerate: el índice y el elemento",
        "`enumerate(personas)` recorre la lista entregando, en cada vuelta, **dos cosas**:\n"
        "\n"
        "1. `indice`: la **posición** de la persona (0, 1, 2…),\n"
        "2. `persona`: la **persona** en sí.\n"
        "\n"
        "La posición se necesita en la línea siguiente, para sacar a esa persona del grupo.",
        "Se prueba a cada persona, una por una, para el primer puesto."),
      n("personas[:indice] +", "Sacar a la persona elegida",
        "Si la persona **tiene la competencia** del primer puesto, se la saca del grupo y se resuelven los puestos que quedan con los demás:\n"
        "\n"
        "- `personas[:indice]`: los que están **antes** de ella,\n"
        "- `personas[indice + 1:]`: los que están **después**,\n"
        "- sumados con `+`: el grupo **sin esa persona**.",
        "Una persona que ya ocupó un puesto no puede volver a contarse: es la regla de «personas distintas» del §5.3."),
      n("return False", "Ninguna sirvió",
        "Si ninguna persona logra cubrir el primer puesto **y** los que siguen, no hay reparto posible: devuelve **False**. Cuando una llamada devuelve False, la anterior **retrocede** y prueba con la siguiente persona.\n"
        "\n"
        "**Ejemplo real (PV07):** rescate con puestos conducción, rescate y rescate. Ana tiene conducción y rescate, Bruno conducción, Carla rescate.\n"
        "\n"
        "1. Prueba **Ana** de conductora → quedan Bruno y Carla para dos rescates: Carla cubre uno, Bruno no cubre el otro → **falla y retrocede**.\n"
        "2. Prueba **Bruno** de conductor → quedan Ana y Carla: Ana rescata, Carla rescata → **True**.",
        "Encuentra un reparto aunque el primer intento no sirva, sin asignar nominalmente cada puesto (§8.2).")),
 paso("uni_condicion", 4, "unidad.py: la condición de servicio", UNI, R(UNI, "class _Condicion", "_HABILITADA, _EN_MANTENIMIENTO"),
      "§8.4: una unidad puede estar habilitada, en mantenimiento o fuera de servicio.",
      n("class _Condicion", "_Condicion: otro State",
        "Mismo patrón que los estados del aviso. `_Condicion` es una **clase abstracta privada** (guion bajo inicial) con una sola pregunta abstracta:\n"
        "\n"
        "`verificar_habilitada()`: ¿puede esta unidad recibir misiones?\n"
        "\n"
        "Hay una subclase por cada condición del §8.4: habilitada, en mantenimiento y fuera de servicio.",
        "La unidad no pregunta con un if en qué condición está: le delega la pregunta a su condición."),
      n("class _Habilitada", "Habilitada: acepta",
        "Responde con `pass`, es decir, **no hace nada**: no lanza error.\n"
        "\n"
        "Que no haya error significa que la unidad **puede recibir misiones**.",
        "Es la condición con la que nace toda unidad."),
      n("class _EnMantenimiento", "En mantenimiento y fuera de servicio: rechazan",
        "Las dos responden lanzando **UnidadNoHabilitada**, cada una con su motivo:\n"
        "\n"
        "- en mantenimiento → «la unidad está en mantenimiento»,\n"
        "- fuera de servicio → «la unidad está fuera de servicio».",
        "§8.4: solo las unidades habilitadas pueden recibir asignaciones, y el operador ve el motivo exacto."),
      n("_HABILITADA, _EN_MANTENIMIENTO", "Tres objetos únicos",
        "Igual que en el aviso: las condiciones no guardan datos propios, así que alcanza con **un único objeto de cada una**.\n"
        "\n"
        "1. **Al cargar el módulo** se crean las tres una sola vez: `_Habilitada()`, `_EnMantenimiento()` y `_FueraDeServicio()`.\n"
        "2. Se guardan en variables **privadas** (`_HABILITADA`, etc.).\n"
        "3. Cada unidad apunta a una de ellas; cambiar de condición es **apuntar a otro objeto**, no crear uno nuevo.",
        "Se ahorra memoria y todas las unidades en mantenimiento se comportan exactamente igual.")),
 paso("uni_init", 4, "unidad.py: Unidad.__init__", UNI, R(UNI, "class Unidad:", "self._registros: list[Registro] = []"),
      "§5.2: una unidad agrupa jefe, personal, vehículo y equipamiento.",
      n("personal: tuple[Persona, ...] = ()", "Parámetros opcionales",
        "`personal` y `equipamiento` terminan en `= ()`: igual que la condición del vehículo, son **opcionales** y, si no se pasan, valen una **tupla vacía**.\n"
        "\n"
        "En cambio, `jefe` y `vehiculo` no tienen valor por defecto: son **obligatorios**.",
        "Una unidad siempre tiene jefe y vehículo; el resto del personal y el equipo se pueden sumar después."),
      n("dotacion = (jefe, *personal)", "(jefe, *personal): desempaquetar",
        "El `*` **abre** la tupla `personal` dentro de otra tupla:\n"
        "\n"
        "`(jefe, *personal)` → (jefe, p1, p2, …)\n"
        "\n"
        "Así se arma la **dotación completa**, con el jefe incluido.",
        "§5.2: el jefe integra la dotación y aporta sus competencias, contado una sola vez."),
      n("len({p.id for p in dotacion})", "Detectar repetidos con un conjunto",
        "`{p.id for p in dotacion}` arma un **conjunto** con los ids. Un conjunto **no admite repetidos**, entonces:\n"
        "\n"
        "- si tiene la **misma cantidad** de elementos que la dotación → nadie se repite,\n"
        "- si tiene **menos** → alguien figuraba dos veces → RecursoDuplicado.\n"
        "\n"
        "Lo mismo se hace con el equipamiento.",
        "Una misma persona no puede ocupar dos lugares en la unidad."),
      n("self._personal: dict", "Diccionarios por id",
        "`{p.id: p for p in dotacion}` arma un **diccionario** que va del id a la persona (una «comprensión de diccionario»).\n"
        "\n"
        "- Buscar a alguien por su id es **directo**, sin recorrer la lista.\n"
        "- Del jefe se guarda **solo su id**: la persona ya está en el diccionario de personal.",
        "Incorporar, retirar o consultar una persona o un equipo por id es una sola operación."),
      n("self._mision_id: str | None", "Condición y misión: dos cosas distintas",
        "La unidad guarda por separado dos datos que el §8.4 distingue:\n"
        "\n"
        "1. `_condicion`: si está **habilitada**, en mantenimiento o fuera de servicio,\n"
        "2. `_mision_id`: si está **comprometida** con una misión. `str | None` significa «un id o nada».\n"
        "\n"
        "Una unidad puede estar habilitada y ocupada, o habilitada y libre.",
        "Declarar mantenimiento no libera una misión, y terminar una misión no cambia la condición.")),
 paso("uni_lectura", 4, "unidad.py: lectura y consultas", UNI, R(UNI, "def personal(self)", "for e in self._equipamiento.values())", antes=1),
      "La unidad responde preguntas sin entregar sus colecciones.",
      n("def personal", "personal: toda la dotación",
        "Devuelve una **tupla** con todas las personas, con el jefe incluido y contado **una sola vez**.\n"
        "\n"
        "Igual que las notas del aviso: es una copia que no se puede modificar desde afuera.",
        "Es lo que recibe la misión para verificar si alcanzan las personas."),
      n("def tiene_persona", "Consultas por id",
        "Tres **consultas rápidas** que responden True o False:\n"
        "\n"
        "- `tiene_persona(id)`: ¿esta persona integra la unidad?\n"
        "- `usa_vehiculo(id)`: ¿este es su vehículo?\n"
        "- `tiene_equipo(id)`: ¿este equipo es de la unidad?\n"
        "\n"
        "`id in diccionario` busca entre las **claves** del diccionario.",
        "La flota las usa para comprobar que ningún recurso esté en dos unidades."),
      n("any(e.categoria", "any(): ¿alguno cumple?",
        "`any(...)` es lo opuesto de `all()`: es verdadero si **al menos un** elemento cumple la condición.\n"
        "\n"
        "Acá pregunta: «¿hay **algún** equipo de esta categoría **y** operativo?».\n"
        "\n"
        "Un equipo de la categoría pero fuera de servicio **no cuenta**.",
        "PV09: con el único equipo de rescate roto, la respuesta es False y la asignación se rechaza.")),
 paso("uni_compromiso", 4, "unidad.py: comprometer, liberar y exigir_jefe", UNI, R(UNI, "def comprometer", "no es el jefe de la unidad"),
      "§8.2 y §8.3: la unidad verifica todo y recién entonces se reserva.",
      n("self._condicion.verificar_habilitada()", "comprometer(): las condiciones en orden",
        "Verifica **todas** las condiciones del §8.2, en este orden:\n"
        "\n"
        "1. la unidad está **habilitada** → si no, UnidadNoHabilitada,\n"
        "2. la unidad está **libre** → si no, UnidadOcupada,\n"
        "3. su vehículo está **operativo** → si no, VehiculoIncompatible,\n"
        "4. su vehículo **sirve para la misión** → si no, VehiculoIncompatible,\n"
        "5. hay **personal suficiente** → si no, PersonalInsuficiente,\n"
        "6. tiene el **equipamiento** operativo → si no, EquipamientoInsuficiente.\n"
        "\n"
        "Solo si pasan las seis, guarda el id de la misión y la unidad queda reservada.",
        "Si cualquier condición falla, el error dice el motivo y la unidad queda exactamente como estaba."),
      n("def liberar", "liberar(): solo la misión que reservó",
        "Recupera la disponibilidad dejando `_mision_id` en **None**.\n"
        "\n"
        "Antes comprueba que quien pide liberar sea **la misma misión** que la reservó; si no, lanza UnidadComprometida.",
        "Una misión no puede liberar por error una unidad que está trabajando para otra."),
      n("def exigir_jefe", "exigir_jefe(): solo el jefe",
        "Compara el id de quien intenta operar con el id del jefe de la unidad. Si no coinciden, lanza **NoEsJefeDeLaUnidad**.\n"
        "\n"
        "La misión lo llama antes de iniciar, rechazar, registrar novedades o finalizar.",
        "§2.3 y PV12: un jefe solo opera sobre las misiones de su propia unidad.")),
 paso("uni_admin", 4, "unidad.py: administrar el personal, el vehículo y el equipo", UNI, R(UNI, "def incorporar_personal", "self._registros.append(registro)", antes=0)[0:1] + (R(UNI, "def cambiar_condicion_equipo", "self._registros.append(registro)")[1],),
      "§2.4: se agregan, quitan y cambian recursos, siempre con la misma secuencia.",
      n("def incorporar_personal", "La secuencia de todos los mutadores",
        "Todos los métodos que modifican la unidad siguen los mismos cuatro pasos:\n"
        "\n"
        "1. `_exigir_modificable()`: si la unidad está comprometida, lanza UnidadComprometida,\n"
        "2. **validar** el cambio (por ejemplo, que la persona no esté ya en la unidad),\n"
        "3. **armar el Registro** de la operación,\n"
        "4. **cambiar** la unidad y agregar el registro al final.",
        "Si algo falla antes del paso 4, la unidad queda como estaba (R6, §8.4)."),
      n("del self._personal", "retirar_personal(): el jefe no se retira",
        "Antes de borrar, comprueba tres cosas:\n"
        "\n"
        "1. que la unidad **se pueda modificar** (no comprometida),\n"
        "2. que la persona **integre la unidad** → si no, NoEncontrado,\n"
        "3. que **no sea el jefe** → si lo es, RecursoInvalido.\n"
        "\n"
        "Después arma el registro y recién ahí `del diccionario[clave]` borra a la persona.",
        "Una unidad nunca queda sin jefe."),
      n("def cambiar_vehiculo", "Cambiar el vehículo y su condición",
        "Dos métodos que siguen la secuencia de los mutadores:\n"
        "\n"
        "- `cambiar_vehiculo`: reemplaza el vehículo y guarda en el registro cuál era el **anterior**.\n"
        "- `cambiar_condicion_vehiculo`: igual que en Equipo, usa `con_condicion()` para crear una **copia** del vehículo con la nueva condición; la copia se valida antes de reemplazar al original.",
        "El historial muestra qué vehículo tenía la unidad antes del cambio (§9)."),
      n("def incorporar_equipo", "Equipo: incorporar, retirar y cambiar condición",
        "Los mismos pasos que con el personal:\n"
        "\n"
        "- **incorporar**: rechaza un equipo que ya está (RecursoDuplicado),\n"
        "- **retirar**: rechaza un equipo que no está (NoEncontrado),\n"
        "- **cambiar condición**: crea la copia con `con_condicion()` y la guarda en el diccionario en lugar del original.",
        "PV09: restablecer un equipo roto es reemplazarlo por su copia operativa.")),
 paso("uni_servicio", 4, "unidad.py: condición de servicio e internos", UNI, R(UNI, "def declarar_en_mantenimiento", "no se modifica"),
      "La unidad cambia su condición de servicio con los mismos cuidados.",
      n("def declarar_en_mantenimiento", "Tres métodos finos",
        "`declarar_en_mantenimiento`, `declarar_fuera_de_servicio` y `restablecer_servicio` tienen **una sola línea**:\n"
        "\n"
        "eligen el objeto de la condición nueva y le delegan todo al método privado `_cambiar_condicion`.",
        "La lógica del cambio está escrita una sola vez, no repetida en tres lugares."),
      n("def registrar_alta", "registrar_alta(): el primer registro",
        "Igual que el aviso nace con AVISO_REGISTRADO, la unidad deja **UNIDAD_REGISTRADA**, con la base en el detalle.\n"
        "\n"
        "Diferencia: no lo hace en su constructor, sino cuando **la flota la incorpora**.",
        "Si la flota rechaza la unidad, no queda un alta registrada de una unidad que nunca entró."),
      n("def _cambiar_condicion", "_cambiar_condicion(): el cambio común",
        "Es un método **privado** (empieza con _) que comparten los tres métodos de condición. Hace tres pasos:\n"
        "\n"
        "1. exige que la unidad **se pueda modificar**,\n"
        "2. arma el registro con la condición **anterior** y la **nueva**,\n"
        "3. recién después **cambia** la condición y guarda el registro.",
        "El historial muestra siempre de qué condición a qué condición pasó la unidad."),
      n("def _exigir_modificable", "_exigir_modificable(): comprometida no se toca",
        "Es un **método privado** (guion bajo inicial): solo lo usa la propia unidad.\n"
        "\n"
        "Si la unidad tiene una misión (`_mision_id` no es None), lanza **UnidadComprometida**.\n"
        "\n"
        "Es la **primera línea** de todos los métodos que modifican la unidad.",
        "§8.4 y PV14: no se cambia el personal, el vehículo o el equipo de una unidad que está en una misión.")),
]

# ═════════ 6 · LA MISIÓN ═════════
P += [
 paso("mis_valores", 5, "mision.py: Novedad, Resultado y VistaMision", MIS, R(MIS, "class Novedad", "resultado: Resultado | None", antes=1),
      "§2.3 y §8.1: lo que el jefe informa durante y al terminar una misión.",
      n("class Novedad", "Novedad: autor, texto y fecha",
        "Un **valor inmutable**: lo que el jefe informa mientras la misión se ejecuta. Igual que Nota, exige tres cosas:\n"
        "\n"
        "1. un **autor** (el jefe),\n"
        "2. un **texto** con contenido,\n"
        "3. una **fecha y hora**.\n"
        "\n"
        "Si falta cualquiera, lanza MisionInvalida.",
        "No queda registrada una novedad vacía o sin autor."),
      n("class Resultado", "Resultado: qué se logró y qué se hizo",
        "Lo que el jefe registra al finalizar. Exige tres cosas:\n"
        "\n"
        "1. un **resultado** del catálogo (satisfactorio o no satisfactorio),\n"
        "2. la descripción de las **tareas** realizadas,\n"
        "3. una **fecha y hora**.\n"
        "\n"
        "Si falta cualquiera, lanza ResultadoInvalido. La propiedad `satisfactorio` responde si el resultado fue satisfactorio.",
        "§2.3: el jefe declara si cumplió el objetivo y qué hizo. Una emergencia solo cierra si alguna misión fue satisfactoria."),
      n("class VistaMision", "VistaMision: una foto de solo lectura",
        "Un **valor inmutable** con los datos de la misión en un momento dado: id, tipo, objetivo, estado, unidad, novedades y resultado.\n"
        "\n"
        "Es lo que la emergencia entrega hacia afuera: se puede **mirar** la misión, pero no **operar** sobre ella.",
        "Nadie puede llamar a `asignar()` o `finalizar()` salteando a la emergencia, que es la que valida y registra.")),
 paso("mis_estados", 5, "mision.py: los cinco estados", MIS, R(MIS, "class EstadoMision", "_FINALIZADA, _CANCELADA ="),
      "§8.1: no se admiten transiciones arbitrarias.",
      n("class EstadoMision", "EstadoMision: el nombre público",
        "Igual que EstadoAviso: un Enum con los cinco nombres del §8.1 (pendiente, asignada, en ejecución, finalizada y cancelada).\n"
        "\n"
        "Es lo que se **muestra y se guarda**. El objeto estado, que tiene el comportamiento, queda **privado**.",
        "Afuera solo se ve el nombre, nunca el objeto que decide."),
      n("def _no_admite", "_no_admite(): el error de la base",
        "Es un **método privado** que arma el mensaje del error: «una misión **X** no puede **Y**».\n"
        "\n"
        "Ejemplo: «una misión cancelada no puede iniciarse».\n"
        "\n"
        "Los métodos de abajo lo usan con `raise self._no_admite(...)`.",
        "Todos los rechazos de estado tienen el mismo formato y el nombre del estado actual."),
      n("def asignar(self) -> _Estado", "Todo se rechaza por defecto",
        "A diferencia del aviso, la base `_Estado` de la misión **no es solo abstracta**: ya responde las siete operaciones, y las responde **rechazando** (asignar, reasignar, rechazar, iniciar, novedad, finalizar, cancelar).\n"
        "\n"
        "Cada estado concreto **sobrescribe solo las que admite**.",
        "Igual que «por defecto no sirve para nada» de los vehículos: lo que un estado no declara, queda prohibido."),
      n("def verificar_concluida", "Dos preguntas para la emergencia",
        "La base también responde dos preguntas que usa la emergencia al cerrar:\n"
        "\n"
        "1. `verificar_concluida()`: lanza **MisionSinConcluir** si la misión sigue activa,\n"
        "2. `exito()`: dice si terminó bien.\n"
        "\n"
        "Por defecto: **no concluida** y **no exitosa**.",
        "Solo Finalizada y Cancelada cambian estas respuestas."),
      n("class _Pendiente", "Pendiente y Asignada: sus salidas",
        "Cada método devuelve el **estado siguiente**:\n"
        "\n"
        "- **Pendiente** → `asignar()` pasa a Asignada · `cancelar()` pasa a Cancelada.\n"
        "- **Asignada** → `reasignar()` sigue Asignada · `rechazar()` vuelve a Pendiente · `iniciar()` pasa a En ejecución · `cancelar()` pasa a Cancelada.\n"
        "\n"
        "Lo que no aparece en la lista lo rechaza la base con MisionEnEstadoInvalido.",
        "§8.1: no hay transiciones arbitrarias; cada estado sabe a dónde puede ir."),
      n("class _EnEjecucion", "En ejecución: novedades y finalizar",
        "Sobrescribe solo dos operaciones:\n"
        "\n"
        "1. `permitir_novedad()`: `pass`, acepta novedades,\n"
        "2. `finalizar()`: devuelve el estado **Finalizada**.\n"
        "\n"
        "Todo lo demás sigue rechazado: no se puede **cancelar, reasignar ni rechazar** una misión en ejecución.",
        "§8.3 y PV13: una vez iniciada, la misión solo puede terminar."),
      n("class _Finalizada", "Finalizada y Cancelada: terminales",
        "No admiten ninguna operación: una misión finalizada o cancelada **no se reabre**.\n"
        "\n"
        "- Las dos pisan `verificar_concluida` con `pass`: cuentan como **concluidas**.\n"
        "- Solo **Finalizada** con resultado satisfactorio cuenta como **éxito**.",
        "La emergencia puede cerrarse cuando todas sus misiones llegaron a uno de estos dos estados (§7.2)."),
      n("_PENDIENTE, _ASIGNADA", "Un objeto por estado",
        "Igual que en el aviso y en la unidad: los cinco estados no guardan datos, así que se crea **un único objeto de cada uno** al cargar el módulo y todas las misiones los comparten.\n"
        "\n"
        "Cambiar de estado es **apuntar a otro objeto**.",
        "Todas las misiones en ejecución se comportan exactamente igual.")),
 paso("mis_asignacion", 5, "mision.py: la unidad asignada (Null Object)", MIS, R(MIS, "class _Asignacion", "_SIN_UNIDAD ="),
      "Una misión pendiente todavía no tiene unidad: igual debe poder responder.",
      n("class _Asignacion", "_Asignacion: lo que toda asignación sabe hacer",
        "Una **clase abstracta privada** con dos operaciones:\n"
        "\n"
        "1. `liberar()`: soltar la unidad,\n"
        "2. `exigir_jefe()`: comprobar que quien opera sea el jefe.\n"
        "\n"
        "`...` es el cuerpo vacío de un método abstracto: cada subclase lo completa.",
        "La misión le habla siempre a «su asignación», tenga o no una unidad real."),
      n("class _SinUnidad", "_SinUnidad: no hace nada",
        "Representa a una misión **sin unidad**. Responde así:\n"
        "\n"
        "- `liberar()`: `pass`, no hay nada que liberar,\n"
        "- `exigir_jefe()`: lanza NoEsJefeDeLaUnidad, porque no hay jefe.\n"
        "\n"
        "Es el patrón **Null Object**: en lugar de guardar None y preguntar `if unidad is None` en cada método, se usa un objeto que ya sabe responder.",
        "El código de la misión no se llena de ifs para el caso «sin unidad»."),
      n("class _ConUnidad", "_ConUnidad: delega en la unidad real",
        "Guarda la unidad asignada y su id. Sus dos operaciones **le pasan el pedido a la unidad**:\n"
        "\n"
        "- `liberar()` → `unidad.liberar(...)`,\n"
        "- `exigir_jefe()` → `unidad.exigir_jefe(...)`.",
        "La misión no necesita saber si tiene unidad: le pregunta a su asignación y ella resuelve."),
      n("_SIN_UNIDAD =", "Un solo _SinUnidad",
        "Igual que los estados: `_SinUnidad` no guarda datos, así que se crea **un único objeto** (`_SIN_UNIDAD`) que comparten todas las misiones sin unidad.",
        "Una misión vuelve a «sin unidad» apuntando a ese objeto, sin crear uno nuevo.")),
 paso("mis_base", 5, "mision.py: Mision, la clase abstracta", MIS, R(MIS, "class Mision(ABC)", "if situacion not in", antes=0)[0:1] + (R(MIS, "def _exigir_equipo", "Falta un")[1],),
      "§6: cada tipo de misión declara lo suyo y la clase base hace lo común.",
      n("tipo: TipoMision", "Atributos de clase declarados, sin valor",
        "Estas tres líneas **solo anotan** lo que cada tipo de misión tiene que definir:\n"
        "\n"
        "1. `tipo`: qué misión es,\n"
        "2. `situaciones_admitidas`: en qué situaciones se permite (§6.4),\n"
        "3. `puestos`: qué competencias necesita, un puesto por persona distinta.\n"
        "\n"
        "Son **atributos de clase**: se definen una vez en cada subclase y valen para todos sus objetos.",
        "Los requisitos dependen del tipo de misión, no de cada misión en particular (§6.4)."),
      n("def __init__", "Mision.__init__: nace pendiente y sin unidad",
        "Al crear una misión:\n"
        "\n"
        "1. **valida** el objetivo → si está vacío, MisionInvalida,\n"
        "2. **genera el id**, igual que el aviso,\n"
        "3. arranca en **_PENDIENTE** y **_SIN_UNIDAD**,\n"
        "4. las **novedades** empiezan vacías y el **resultado** en None.",
        "Toda misión nace igual, sin importar su tipo: pendiente y sin unidad (§8.1)."),
      n("def verificar_vehiculo", "Dos métodos que cada tipo define",
        "Dos **métodos abstractos**: Mision no los implementa, cada tipo está obligado a hacerlo.\n"
        "\n"
        "1. `verificar_vehiculo()`: le pregunta al vehículo si sirve (doble despacho),\n"
        "2. `verificar_equipamiento()`: comprueba el equipo que exige ese tipo.",
        "Si se agrega un tipo de misión y le falta alguno, Python no deja crearlo."),
      n("def verificar_personal", "verificar_personal(): personas distintas",
        "Llama a `existe_distribucion` con los **puestos** de la misión y el **personal** de la unidad.\n"
        "\n"
        "Si no hay forma de cubrirlos con personas distintas, lanza **PersonalInsuficiente** con la lista de competencias que se necesitaban.",
        "PV07: el operador ve qué competencias faltaron."),
      n("def verificar_situacion", "verificar_situacion(): ¿sirve para esta emergencia?",
        "Pregunta si la situación de la emergencia está en `situaciones_admitidas`. Si no está, lanza **MisionIncompatible**.\n"
        "\n"
        "Ejemplo: una evacuación solo admite inundación e incendio; para un accidente vial se rechaza.",
        "§6.4 y PV05: la tabla de compatibilidad vive en cada tipo de misión."),
      n("def _exigir_equipo", "_exigir_equipo(): helper común",
        "Es un **método privado** de ayuda (helper): le pregunta a la unidad si tiene un equipo **operativo** de la categoría pedida y, si no, lanza **EquipamientoInsuficiente**.\n"
        "\n"
        "Lo reutilizan Rescate (equipo de rescate) y AsistenciaSanitaria (equipo sanitario).",
        "La misma comprobación está escrita una sola vez.")),
 paso("mis_operador", 5, "mision.py: asignar, reasignar y cancelar", MIS, (R(MIS, "def asignar(self, unidad", "def asignar(self, unidad")[0], R(MIS, "def cancelar(self) -> None", "self._estado = siguiente")[1]),
      "§2.2: lo que hace el operador sobre una misión.",
      n("siguiente = self._estado.asignar()", "asignar(): primero preguntar, después comprometer",
        "Tres pasos, en orden:\n"
        "\n"
        "1. **pregunta al estado** a cuál pasa: si no admite asignarse, lanza MisionEnEstadoInvalido,\n"
        "2. `unidad.comprometer(self)` **verifica todo** (habilitada, libre, vehículo, personal y equipo),\n"
        "3. recién ahí **guarda** la unidad (`_ConUnidad`) y **cambia de estado**.",
        "Si la unidad no sirve, la misión y la unidad quedan como estaban."),
      n("def reasignar", "reasignar(): la nueva primero",
        "El orden es lo importante:\n"
        "\n"
        "1. pregunta al estado si admite reasignarse,\n"
        "2. **compromete la unidad nueva**, que verifica todo,\n"
        "3. recién después **libera la anterior**,\n"
        "4. guarda la nueva asignación.",
        "PV18: si la nueva unidad no cumple, la anterior sigue asignada y reservada, y nada cambia."),
      n("def cancelar", "cancelar(): liberar y quedar sin unidad",
        "Tres pasos:\n"
        "\n"
        "1. pregunta al estado si admite cancelarse (solo Pendiente o Asignada),\n"
        "2. **libera** la unidad reservada, si había,\n"
        "3. vuelve a **_SIN_UNIDAD** y cambia a Cancelada.",
        "PV15: la unidad queda disponible y la misión no puede iniciarse después.")),
 paso("mis_jefe", 5, "mision.py: lo que hace el jefe de la unidad", MIS, R(MIS, "def rechazar(self, jefe_id", "self._estado = siguiente", antes=0)[0:1] + (R(MIS, "def finalizar(self, jefe_id", "self._estado = siguiente")[1],),
      "§2.3: el jefe rechaza, inicia, informa novedades y finaliza.",
      n("def rechazar", "rechazar(): justificar y volver a pendiente",
        "Comprueba tres cosas y después cambia:\n"
        "\n"
        "1. que el estado admita rechazarse (solo Asignada),\n"
        "2. que quien rechaza sea **el jefe** de la unidad,\n"
        "3. que haya **justificación** → si no, JustificacionVacia.\n"
        "\n"
        "Recién entonces libera la unidad, queda sin unidad y vuelve a **Pendiente**.",
        "PV13: la misión puede asignarse a otra unidad apta."),
      n("def iniciar", "iniciar(): solo el jefe",
        "Dos comprobaciones y el cambio:\n"
        "\n"
        "1. pregunta al estado (solo Asignada puede iniciarse),\n"
        "2. comprueba que sea **el jefe** de la unidad,\n"
        "3. cambia a **En ejecución**.",
        "§2.3: el operador no puede declarar iniciada una misión en nombre de la unidad."),
      n("def registrar_novedad", "registrar_novedad(): solo en ejecución",
        "Tres pasos:\n"
        "\n"
        "1. el estado lo permite **solo en ejecución**,\n"
        "2. comprueba que sea **el jefe**,\n"
        "3. crea la **Novedad** (que se valida sola) y la agrega a la lista.",
        "PV11: el jefe informa cómo avanza la intervención."),
      n("def finalizar", "finalizar(): validar el resultado antes de liberar",
        "Primero todo lo que puede fallar, después los cambios:\n"
        "\n"
        "1. pregunta al estado (solo En ejecución puede finalizar),\n"
        "2. comprueba que sea **el jefe**,\n"
        "3. arma el **Resultado**, que se valida solo.\n"
        "\n"
        "Recién después **libera la unidad**, guarda el resultado y cambia a **Finalizada**.",
        "Si el resultado es inválido, la unidad no se libera y la misión sigue en ejecución.")),
 paso("mis_lectura", 5, "mision.py: lo que la emergencia le pregunta", MIS, (R(MIS, "def es_exitosa", "def es_exitosa")[0] - 3, R(MIS, "tuple(self._novedades), self._resultado)", "tuple(self._novedades), self._resultado)")[1]),
      "La emergencia pregunta sin poder modificar.",
      n("def verificar_concluida", "verificar_concluida() y es_exitosa()",
        "La misión **no responde sola**: le pasa la pregunta a su estado.\n"
        "\n"
        "- `verificar_concluida()` → el estado decide si lanza MisionSinConcluir,\n"
        "- `es_exitosa()` → el estado decide mirando el resultado.\n"
        "\n"
        "La emergencia las usa para saber si puede cerrarse.",
        "La regla de cierre no depende de ifs sobre el estado: cada estado ya sabe contestar."),
      n("def estado", "Lectura: estado y unidad",
        "Dos propiedades de solo lectura:\n"
        "\n"
        "- `estado`: devuelve solo la **etiqueta** pública, igual que en el aviso,\n"
        "- `unidad_id`: sale de la asignación; con `_SinUnidad` vale **None**.",
        "Se puede saber qué unidad tiene la misión sin tocar la asignación."),
      n("def vista", "vista(): la foto de solo lectura",
        "Arma una **VistaMision** con los datos actuales. Las novedades salen como **tupla**, igual que las notas del aviso.",
        "Es lo único que la emergencia entrega hacia afuera de sus misiones.")),
 paso("mis_tipos", 5, "mision.py: Evacuación, Rescate y Asistencia sanitaria", MIS, R(MIS, "class Evacuacion", "EQUIPO_SANITARIO)"),
      "§6.1 a §6.3: tres tipos de misión con requisitos distintos.",
      n("tipo = TipoMision.EVACUACION", "Cada tipo declara sus datos",
        "Evacuacion completa los tres atributos de clase que pidió Mision:\n"
        "\n"
        "1. `tipo`: EVACUACION,\n"
        "2. `situaciones_admitidas`: inundación e incendio (un frozenset: no se evacúa en un accidente vial),\n"
        "3. `puestos`: conducción y evacuación.\n"
        "\n"
        "Son iguales para todas las evacuaciones, por eso viven en la clase y no en cada objeto.",
        "§6.1 y §6.4: los requisitos dependen del tipo de misión."),
      n("super().__init__", "Evacuacion.__init__: un dato más",
        "La evacuación necesita un dato que las demás no: **cuántas personas** evacuar.\n"
        "\n"
        "1. valida que la cantidad sea un **entero positivo** → si no, MisionInvalida,\n"
        "2. llama a `super().__init__()`: igual que en TransportePersonas, la base valida el objetivo y genera el id,\n"
        "3. guarda la cantidad.",
        "PV06: la capacidad del vehículo se compara contra esta cantidad."),
      n("vehiculo.verificar_evacuacion", "Doble despacho",
        "La misión **no compara categorías**: le pregunta al vehículo.\n"
        "\n"
        "- Evacuación → `vehiculo.verificar_evacuacion(cantidad)`,\n"
        "- Rescate → `vehiculo.verificar_rescate()`,\n"
        "- Asistencia → `vehiculo.verificar_asistencia()`.\n"
        "\n"
        "Se llama **doble despacho** porque la respuesta depende de **dos tipos**: el de la misión (qué pregunta hace) y el del vehículo (cómo contesta).",
        "PV08: una ambulancia no sirve para evacuar sin escribir ningún if de categorías."),
      n("class Rescate", "Rescate: conductor y dos rescatistas",
        "Declara sus datos y sus dos verificaciones:\n"
        "\n"
        "1. `puestos`: conducción y **dos** de rescate, tres personas distintas,\n"
        "2. `verificar_vehiculo()`: le pregunta al vehículo si sirve para rescatar,\n"
        "3. `verificar_equipamiento()`: pide un **equipo de rescate** operativo con `_exigir_equipo`.",
        "§6.2 y PV07: un rescate exige un mínimo de tres integrantes distintos."),
      n("class AsistenciaSanitaria", "Asistencia sanitaria: ambulancia y primeros auxilios",
        "Mismo molde que Rescate:\n"
        "\n"
        "1. `puestos`: conducción y primeros auxilios,\n"
        "2. `verificar_vehiculo()`: solo una **ambulancia** responde que sí,\n"
        "3. `verificar_equipamiento()`: pide un **equipo sanitario** operativo.",
        "§6.3 y PV08: una unidad con transporte de personas se rechaza aunque tenga personal con primeros auxilios.")),
]

# ═════════ 7 · LA EMERGENCIA Y LA FLOTA ═════════
P += [
 paso("eme_estados", 6, "emergencia.py: abierta o cerrada", EME, R(EME, "class EstadoEmergencia", "_ABIERTA, _CERRADA"),
      "§7.2: una emergencia solo se cierra si todas sus misiones terminaron y alguna fue exitosa.",
      n("class EstadoEmergencia", "EstadoEmergencia: el nombre público",
        "Igual que en el aviso y la misión: un Enum con los dos estados, **abierta** y **cerrada**. Es lo que se muestra y se guarda.",
        "El reportante puede consultar si su emergencia está abierta o cerrada (§2.1)."),
      n("def permitir_modificaciones", "_Estado: dos preguntas",
        "Clase abstracta **privada**, igual que la del aviso, con dos métodos abstractos:\n"
        "\n"
        "1. `permitir_modificaciones()`: lanza EmergenciaCerrada si ya no se puede operar,\n"
        "2. `cerrar(misiones)`: recibe las misiones y devuelve el estado siguiente, o lanza el motivo por el que no puede cerrarse.",
        "Cada operación de la emergencia empieza preguntándole a su estado."),
      n("class _Abierta", "Abierta: permite todo y puede cerrarse",
        "Acepta modificaciones (`pass`). Para **cerrar** exige dos cosas:\n"
        "\n"
        "1. **todas** las misiones concluidas: recorre cada una con `verificar_concluida()` → si alguna sigue activa, MisionSinConcluir,\n"
        "2. **al menos una** exitosa: `any(...)` → si ninguna lo es (o no hay misiones), SinMisionExitosa.",
        "§7.2 y PV16: las dos condiciones del cierre, en el mismo lugar."),
      n("class _Cerrada", "Cerrada: rechaza todo",
        "Responde las dos preguntas con **EmergenciaCerrada**:\n"
        "\n"
        "- cualquier modificación → «no admite misiones ni modificaciones operativas»,\n"
        "- un segundo cierre → «la emergencia ya está cerrada».",
        "§7.2 y PV16: una emergencia cerrada no admite nuevas misiones."),
      n("_ABIERTA, _CERRADA", "Dos objetos únicos",
        "Igual que en el aviso: se crean **una sola vez** `_Abierta()` y `_Cerrada()`, y todas las emergencias los comparten.",
        "Todas las emergencias cerradas se comportan exactamente igual.")),
 paso("eme_init", 6, "emergencia.py: Emergencia.__init__", EME, R(EME, "class Emergencia:", "        ]"),
      "§7.2: una emergencia nace al aceptar un aviso.",
      n("if not hay_texto(aviso_id)", "Validar el origen",
        "Valida en tres grupos, en orden:\n"
        "\n"
        "1. el **aviso de origen**, el **reportante** y la **ubicación**,\n"
        "2. el **tipo** y la **gravedad** confirmados, dentro del catálogo,\n"
        "3. el **operador** que acepta y la **fecha** de aceptación.\n"
        "\n"
        "Si falla cualquier grupo, lanza AceptacionInvalida.",
        "Una emergencia nace completa: sin ella el aviso tampoco cambia de estado."),
      n("self._estado: _Estado = _ABIERTA", "Nace abierta",
        "Igual que el aviso: guarda sus datos en **atributos privados** y genera su id con `uuid4()` si no se le pasa uno.\n"
        "\n"
        "Su estado inicial es **_ABIERTA**: toda emergencia nace abierta.",
        "§7.2: mientras esté abierta, el operador puede agregar misiones."),
      n("self._misiones: dict", "Las misiones por id",
        "`_misiones` es un **diccionario privado** id → misión, que empieza vacío.\n"
        "\n"
        "La emergencia es la **dueña** de sus misiones: toda operación sobre una misión pasa por ella.",
        "Nadie opera una misión salteando las reglas de la emergencia (abierta, registro, compatibilidad)."),
      n("Operacion.EMERGENCIA_CREADA", "Nace con su primer registro",
        "Igual que el aviso: `self._registros = [ ... ]` crea una lista con **un único elemento**, el registro de su creación. Ese registro guarda:\n"
        "\n"
        "- **quién**: el operador que aceptó el aviso,\n"
        "- **cuándo**: el momento de la aceptación,\n"
        "- **qué**: `Operacion.EMERGENCIA_CREADA`,\n"
        "- **sobre qué**: la emergencia y el aviso de origen,\n"
        "- **detalle**: el tipo y la gravedad **confirmados**.",
        "§9: la creación de la emergencia queda registrada desde el primer momento.")),
 paso("eme_operador", 6, "emergencia.py: lo que hace el operador", EME, (R(EME, "def crear_mision", "def crear_mision")[0], R(EME, "def cancelar_mision", "self._registros.append(registro)")[1]),
      "§2.2: crear, asignar, reasignar y cancelar misiones.",
      n("def crear_mision", "crear_mision(): agregar una misión",
        "Cuatro pasos:\n"
        "\n"
        "1. pregunta al estado si la emergencia **está abierta**,\n"
        "2. verifica que el tipo de misión **sirva para la situación** → si no, MisionIncompatible,\n"
        "3. arma el registro MISION_CREADA,\n"
        "4. recién al final **agrega la misión** al diccionario.",
        "PV05: una evacuación para un accidente vial se rechaza sin dejar rastros."),
      n("def asignar_mision", "asignar_mision(): coordina y delega",
        "La emergencia coordina y la misión verifica:\n"
        "\n"
        "1. la emergencia **está abierta**,\n"
        "2. **busca la misión** por id → si no está, NoEncontrado,\n"
        "3. arma el registro MISION_ASIGNADA,\n"
        "4. `mision.asignar(unidad)` **verifica todo** lo demás.\n"
        "\n"
        "El registro se guarda solo si la misión aceptó la unidad.",
        "§8.2: las siete verificaciones se reparten entre la emergencia, la misión y la unidad."),
      n("def reasignar_mision", "reasignar_mision(): quién era y quién es",
        "Tres pasos:\n"
        "\n"
        "1. guarda la unidad **anterior** antes de reasignar,\n"
        "2. `mision.reasignar(unidad_nueva)` verifica todo,\n"
        "3. registra **las dos** unidades en el detalle.\n"
        "\n"
        "`str(anterior)` convierte a texto aunque sea None.",
        "§9 y PV17: una reasignación identifica la unidad anterior y la nueva."),
      n("def cancelar_mision", "cancelar_mision(): el registro antes de cancelar",
        "Cuatro pasos:\n"
        "\n"
        "1. la emergencia **está abierta**,\n"
        "2. busca la misión,\n"
        "3. toma la unidad que se va a liberar y **arma el registro**,\n"
        "4. **cancela** la misión y guarda el registro.",
        "El historial guarda qué unidad quedó liberada, aunque después la misión ya no la tenga.")),
 paso("eme_jefe", 6, "emergencia.py: lo que hace el jefe de unidad", EME, (R(EME, "def rechazar_mision", "def rechazar_mision")[0], R(EME, "def finalizar_mision", "tareas=tareas))")[1]),
      "§2.3: rechazar, iniciar, informar novedades y finalizar. Siempre pasan por la emergencia.",
      n("def rechazar_mision", "El mismo molde en las cuatro",
        "rechazar, iniciar, registrar novedad y finalizar siguen los mismos pasos:\n"
        "\n"
        "1. la emergencia **está abierta**,\n"
        "2. **busca la misión** por id,\n"
        "3. **delega** en la misión, que valida que sea el jefe,\n"
        "4. deja el **registro**.",
        "La emergencia no repite las reglas de la misión: solo coordina y deja constancia."),
      n("def registrar_novedad", "registrar_novedad(): la novedad queda en el detalle",
        "Sigue el molde de las cuatro operaciones del jefe y, al registrar, pasa `novedad=texto`: el texto queda como **dato con nombre** en el detalle del registro.",
        "PV11: el historial muestra qué informó el jefe durante la ejecución."),
      n("def finalizar_mision", "finalizar_mision(): resultado y tareas",
        "Tres pasos:\n"
        "\n"
        "1. guarda qué unidad tenía la misión, **antes** de finalizar (después queda libre),\n"
        "2. `mision.finalizar(...)` valida el jefe y el resultado,\n"
        "3. registra la unidad, el **resultado** y las **tareas**.",
        "§9: la finalización deja constancia de qué unidad hizo qué y con qué resultado.")),
 paso("eme_cierre", 6, "emergencia.py: cerrar", EME, R(EME, "def cerrar(self, supervisor_id", "self._registros.append(registro)"),
      "§7.2: el supervisor cierra la emergencia.",
      n("self._estado.cerrar(", "cerrar(): el estado decide",
        "Tres pasos:\n"
        "\n"
        "1. le pasa las misiones al **estado**: Abierta verifica que todas terminaron y alguna fue exitosa; Cerrada lanza error,\n"
        "2. arma el registro EMERGENCIA_CERRADA,\n"
        "3. recién después **cambia el estado** y guarda el registro.",
        "PV16: un cierre rechazado deja la emergencia abierta y admitiendo misiones."),
      ),
 paso("eme_lectura", 6, "emergencia.py: lectura y prioridad", EME, (R(EME, "def id(self)", "def id(self)", antes=1)[0], R(EME, "return tuple(sorted(abiertas", "return tuple(sorted(abiertas")[1]),
      "§4: las emergencias abiertas se atienden de más grave a menos grave.",
      n("def misiones", "misiones: solo fotos de lectura",
        "`tuple(m.vista() for m in ...)` es una **expresión generadora**: recorre las misiones y arma una tupla con la **VistaMision** de cada una.\n"
        "\n"
        "La emergencia **nunca entrega la misión misma**, solo su foto.",
        "Nadie puede finalizar o cancelar una misión desde afuera sin pasar por la emergencia."),
      n("def clave_de_prioridad", "clave_de_prioridad: qué se ordena",
        "Devuelve una tupla **(-gravedad, creada_en)**. Python ordena las tuplas comparando primero el primer valor y, si empatan, el segundo.\n"
        "\n"
        "1. `-gravedad`: Alta vale 3, entonces su clave es **-3**, la más chica: va **primero**.\n"
        "2. `creada_en`: a igual gravedad, gana la **más antigua**.\n"
        "\n"
        "| emergencia | gravedad | aceptada | clave |\n"
        "|---|---|---|---|\n"
        "| E2 | Alta | 10:30 | (-3, 10:30) |\n"
        "| E1 | Media | 10:00 | (-2, 10:00) |\n"
        "| E3 | Media | 10:15 | (-2, 10:15) |",
        "§4 y PV03: Alta, Media y Baja; a igual gravedad, primero la aceptada antes."),
      n("def _mision", "_mision(): buscar o NoEncontrado",
        "Es un **método privado** de la emergencia: busca una misión por su id en el diccionario y, si no está, lanza **NoEncontrado**.\n"
        "\n"
        "Lo usan todas las operaciones sobre misiones.",
        "Operar sobre una misión de otra emergencia se rechaza con un motivo claro."),
      n("def abiertas_por_prioridad", "abiertas_por_prioridad(): una función de módulo",
        "Es una **función** del módulo, fuera de la clase, porque trabaja con **muchas** emergencias. Hace dos pasos:\n"
        "\n"
        "1. **filtra**: `(e for e in emergencias if ...)` deja solo las abiertas,\n"
        "2. **ordena**: `sorted(..., key=lambda e: e.clave_de_prioridad)` las ordena por su clave.\n"
        "\n"
        "`lambda e: ...` es una **mini función sin nombre**: le dice a sorted qué mirar de cada emergencia.",
        "PV03: el operador ve primero lo más urgente.")),
 paso("flo_consulta", 6, "flota.py: BaseOperativa y Flota", FLO, R(FLO, "@dataclass", "if u.base_id == base_id"),
      "§5.1 y §5.2: la flota conoce todas las bases y unidades.",
      n("class BaseOperativa", "BaseOperativa: un valor",
        "Mismo molde que Ubicacion: un **valor inmutable** que exige tres cosas:\n"
        "\n"
        "1. una **identificación**,\n"
        "2. un **nombre**,\n"
        "3. una **ubicación**.\n"
        "\n"
        "Si falta cualquiera, lanza RecursoInvalido.",
        "§5.1: cada base tiene identificación y ubicación."),
      n("class Flota", "Flota: dos diccionarios",
        "Guarda en dos **diccionarios privados** las bases y las unidades, cada una por su id.\n"
        "\n"
        "Es la **raíz de consistencia** de los recursos: la regla «un recurso no puede estar en dos unidades» involucra a **todas** las unidades, y solo la flota las ve a todas.",
        "§5.2: una unidad sola no puede saber si su vehículo ya está en otra."),
      n("def unidad(self", "unidad(): buscar o NoEncontrado",
        "Igual que `_mision()` en la emergencia: `if unidad_id not in diccionario` comprueba que exista la clave **antes** de leerla y, si no está, lanza **NoEncontrado**.",
        "Pedir una unidad inexistente da un error con nombre, no un KeyError de Python."),
      n("def unidades_de", "unidades_de(): filtrar con una expresión",
        "`tuple(u for u in ... if condición)` recorre las unidades y se queda solo con las de esa **base**.",
        "§5.1: una base aloja varias unidades y cada unidad pertenece a una sola base.")),
 paso("flo_altas", 6, "flota.py: registrar bases e incorporar unidades", FLO, R(FLO, "def registrar_base", "self._unidades[unidad.id] = unidad"),
      "Dar de alta exige revisar a todas las demás.",
      n("def registrar_base", "registrar_base(): sin duplicados",
        "Si ya existe una base con ese id, lanza **RecursoDuplicado**; si no, la guarda en el diccionario.",
        "No hay dos bases con la misma identificación."),
      n("def incorporar_unidad", "incorporar_unidad(): revisar todo y después guardar",
        "Antes de guardar, la flota verifica:\n"
        "\n"
        "1. que **exista la base** → si no, NoEncontrado,\n"
        "2. que la unidad **no esté repetida** → si no, RecursoDuplicado,\n"
        "3. que **ninguna persona** esté en otra unidad,\n"
        "4. que el **vehículo** no esté en otra unidad,\n"
        "5. que **ningún equipo** esté en otra unidad.\n"
        "\n"
        "Recién después registra el alta y guarda la unidad.",
        "§5.2: ningún recurso termina en dos unidades a la vez.")),
 paso("flo_cambios", 6, "flota.py: cambios que miran a las demás unidades", FLO, R(FLO, "def incorporar_personal", "unidad.incorporar_equipo(equipo, actor_id, fecha_hora)"),
      "Agregar un recurso a una unidad existente también puede chocar con otra unidad.",
      n("def incorporar_personal", "Primero la flota, después la unidad",
        "Tres pasos:\n"
        "\n"
        "1. la flota **busca la unidad** → si no existe, NoEncontrado,\n"
        "2. comprueba que el recurso esté **libre en las demás** unidades,\n"
        "3. **delega** en la unidad, que valida lo suyo (no comprometida, no repetido).",
        "Cada uno controla lo que sabe: la flota ve todas las unidades, la unidad se ve a sí misma."),
      n("def cambiar_vehiculo", "Vehículo y equipo: el mismo orden",
        "`cambiar_vehiculo` e `incorporar_equipo` repiten los tres pasos de `incorporar_personal`:\n"
        "\n"
        "1. buscar la unidad,\n"
        "2. comprobar que el recurso esté **libre** en las demás,\n"
        "3. delegar en la unidad.",
        "§5.2: ningún vehículo ni equipo termina en dos unidades.")),
 paso("flo_unicidad", 6, "flota.py: unicidad entre unidades", FLO, R(FLO, "def _exigir_persona_libre", "El equipo {equipo_id}"),
      "§5.2: una persona, vehículo o equipo no puede estar en dos unidades.",
      n("def _exigir_persona_libre", "_exigir_persona_libre(): recorrer las unidades",
        "Es un **método privado** de la flota. Recorre **todas** las unidades y, si alguna ya tiene a la persona, lanza **RecursoDuplicado** indicando cuál.\n"
        "\n"
        "`salvo_unidad_id` indica qué unidad **no** revisar:\n"
        "\n"
        "- al **incorporar a una unidad existente**, se saltea esa misma unidad (la valida ella),\n"
        "- al **dar de alta una unidad nueva**, vale None y se revisan todas.",
        "§5.2: una misma persona no puede formar parte de dos unidades."),
      n("def _exigir_vehiculo_libre", "Lo mismo para vehículos y equipos",
        "`_exigir_vehiculo_libre` y `_exigir_equipo_libre` también son **métodos privados** y hacen lo mismo; solo cambia la pregunta que le hacen a cada unidad:\n"
        "\n"
        "- vehículos → `usa_vehiculo()`,\n"
        "- equipos → `tiene_equipo()`.",
        "Las tres reglas de unicidad del §5.2 viven en un solo lugar.")),
]
