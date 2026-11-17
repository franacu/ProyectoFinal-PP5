"""Pasos que completan la presentación: todo el dominio, pieza por pieza.

Cada nota: N(archivo, símbolo, línea_a_buscar, término, qué_es, problema, por_qué_lo_usé, ejemplo).
Si un término ya se explicó antes, la presentación no vuelve a explicarlo (solo cuenta por qué se usó acá).
"""

from guion import DECISION, EXPLICA, PASOS

A, V, M, C, U, E = "dominio/aviso.py", "dominio/vehiculos.py", "dominio/mision.py", "dominio/catalogos.py", "dominio/valores.py", "dominio/emergencia.py"
H, P, EQ, D, UN, F, ER = ("dominio/historial.py", "dominio/personal.py", "dominio/equipamiento.py", "dominio/distribucion.py",
                          "dominio/unidad.py", "dominio/flota.py", "dominio/errores.py")


def N(arch, sim, aguja, term, que, prob, elec, ej=""):
    EXPLICA[(arch, sim, term)] = (que, ej)
    DECISION[(arch, sim, term)] = (prob, "", elec)
    return (aguja, term, que, elec)


def paso(arch, sim, clase, titulo, por_que, notas):
    return dict(tipo="codigo", titulo="0 · " + titulo, clase=clase, archivo=arch, simbolo=sim, por_que=por_que, notas=notas)


def despues(ancla, nuevos):
    i = next(k for k, p in enumerate(PASOS) if ancla(p))
    PASOS[i + 1:i + 1] = nuevos


def es(arch, sim):
    return lambda p: p.get("tipo") == "codigo" and p["archivo"] == arch and p["simbolo"] == sim


def esc(clave):
    return lambda p: p.get("tipo") == "escenario" and p.get("clave") == clave


# ─────────── AVISO: los otros estados, nota, descarte ───────────
S = "_Descartado"
d1 = paso(A, S, "Aviso", "Descartado: un estado del que no se sale",
          "§7.1: un aviso descartado tampoco puede aceptarse después. Aceptado y Descartado son iguales de simples: rechazan todo.",
          [N(A, S, "class _Descartado(_Estado)", "estado final",
             "Un estado del que no se sale: un aviso descartado se queda así para siempre. No devuelve un estado siguiente porque no hay a dónde ir.",
             "El enunciado dice que un aviso descartado no puede aceptarse ni evaluarse de nuevo.",
             "Un estado propio que rechaza todo: la regla queda escrita en una sola clase.",
             "aviso descartado → aceptar()    # AvisoNoPendiente\naviso descartado → descartar()  # AvisoNoPendiente"),
           N(A, S, "no puede agregar notas", "rechazo con motivo",
             "Cada operación prohibida lanza AvisoNoPendiente con un texto que dice qué se intentó.",
             "Un rechazo sin motivo no ayuda a quien opera.",
             "Un error propio con un mensaje distinto por operación.",
             'aviso.agregar_nota(...)   # AvisoNoPendiente: Un aviso descartado no puede agregar notas'),
           N(A, S, "if descarte is None", "descarte obligatorio",
             "Un aviso descartado siempre conserva su descarte con la justificación. Si al reconstruirlo falta, es un dato corrupto.",
             "El reportante tiene que poder consultar la justificación del descarte (§2.1).",
             "El estado comprueba su propio dato: descartado exige descarte; pendiente y aceptado lo prohíben.",
             "Aviso.restaurar(..., estado=DESCARTADO, descarte=None)   # DatoDeAvisoInvalido")])
despues(es(A, "_Pendiente"), [d1])

S = "Nota"
d2 = paso(A, S, "Aviso", "Nota: autor, fecha y hora",
          "§2.1: cada nota conserva autor, fecha y hora, y no reemplaza los datos originales del aviso.",
          [N(A, S, "@dataclass(frozen=True, slots=True)", "dataclass frozen",
             "Inmutable, igual que la ubicación.",
             "Una nota ya escrita no debe poder editarse: se podría cambiar lo que dijo el reportante.",
             "Inmutable: para agregar información se agrega otra nota, nunca se edita una."),
           N(A, S, "autor_id: str", "tres datos obligatorios",
             "Una nota guarda quién la escribió, qué dijo y cuándo: los tres datos que pide el enunciado.",
             "§2.1: cada nota conserva autor, fecha y hora.",
             "Los tres son campos del objeto: no existe una nota sin ellos.",
             'Nota("r1", "Hay más heridos", ahora)   # OK'),
           N(A, S, "if not hay_texto(self.texto)", "nota vacía",
             "Una nota sin texto no aporta nada: se rechaza con NotaInvalida.",
             "Las notas vacías llenarían el aviso de ruido.",
             "Se valida al crear: la nota inválida no existe.",
             'Nota("r1", "   ", ahora)   # NotaInvalida: La nota no puede estar vacía'),
           N(A, S, "if self.fecha_hora is None", "fecha obligatoria",
             "Sin fecha y hora no se sabe cuándo se escribió.",
             "Sin fecha no hay trazabilidad.",
             "Se rechaza al crear, con un error que dice qué falta.")])
S = "Descarte"
d3 = paso(A, S, "Aviso", "Descarte: la justificación es obligatoria",
          "§7.1: un operador descarta un aviso registrando una justificación. Sin motivo no hay descarte.",
          [N(A, S, "if not hay_texto(self.justificacion)", "justificación obligatoria",
             "Un descarte sin motivo no puede existir: la regla vive en el propio Descarte.",
             "El operador no puede descartar un aviso sin dejar escrito por qué (§7.1).",
             "El Descarte se valida al crear: o tiene justificación o no se construye.",
             'Descarte("op1", "", ahora)   # JustificacionVacia'),
           N(A, S, "raise JustificacionVacia", "error específico",
             "JustificacionVacia es un tipo especial de DescarteInvalido: quien atrapa el general atrapa también este.",
             "La API quiere distinguir «falta la justificación» de otros errores del descarte.",
             "Una subclase de error: se puede atrapar el caso general o el específico.",
             "except DescarteInvalido:   # atrapa también JustificacionVacia"),
           N(A, S, "necesita un operador", "quién y cuándo",
             "También se exige quién descartó y cuándo: las dos preguntas de la trazabilidad.",
             "Hay que saber quién tomó la decisión y en qué momento.",
             "Se validan igual que la justificación, con un error propio del descarte.",
             'Descarte("", "Falsa alarma", ahora)   # DescarteInvalido')])
S = "Aviso.agregar_nota"
d4 = paso(A, S, "Aviso", "Agregar una nota: solo el reportante",
          "§2.1: solo el reportante agrega notas, y solo mientras el aviso está pendiente.",
          [N(A, S, "self._estado.permitir_nota()", "pregunta al estado primero",
             "Antes que nada el aviso le pregunta a su estado si admite notas. Si no está pendiente, el estado lanza el error.",
             "Un aviso aceptado o descartado no admite notas.",
             "El Aviso no revisa su propio estado: delega, igual que en aceptar.",
             "aviso aceptado → agregar_nota(...)   # AvisoNoPendiente"),
           N(A, S, "if autor_id != self._reportante_id", "solo el reportante",
             "Compara quién escribe con el reportante del aviso. Otro usuario recibe NotaDeOtroAutor.",
             "Un reportante no puede escribir en avisos ajenos (§2.1).",
             "El aviso conoce a su reportante y lo comprueba él mismo.",
             'aviso.agregar_nota("otro", "texto", ahora)   # NotaDeOtroAutor'),
           N(A, S, "nota = Nota(autor_id, texto, fecha_hora)", "validar antes de tocar",
             "Se crea la nota primero. Si el texto es inválido, el error salta acá y la lista de notas no se tocó.",
             "Si se agregara a la lista y después fallara la validación, quedaría una nota a medias.",
             "Todo lo que puede fallar se construye antes de modificar nada.",
             'aviso.agregar_nota("r1", "", ahora)   # NotaInvalida; el aviso queda igual'),
           N(A, S, "registro = Registro.de(", "historial",
             "Cada operación deja un registro.", "Hay que conservar quién hizo qué y cuándo.",
             "El registro se arma antes de modificar, así no queda historia falsa si algo falla."),
           N(A, S, "self._notas.append(nota)", "modificar al final",
             "Recién acá cambia el aviso.", "Mientras algo pueda fallar no se toca nada.",
             "La nota y su registro se agregan juntos, al final.")])
S = "Aviso.descartar"
d5 = paso(A, S, "Aviso", "Descartar: sin justificación no cambia nada",
          "§7.1: descartar exige justificación y deja el aviso sin posibilidad de aceptarse.",
          [N(A, S, "siguiente = self._estado.descartar()", "delegación",
             "El Aviso le pregunta al estado.", "Solo un aviso pendiente puede descartarse.",
             "El estado decide si se puede y a cuál pasa; el Aviso no revisa nada."),
           N(A, S, "descarte = Descarte(", "validar la justificación",
             "Se crea el Descarte antes de cambiar nada. Si falta la justificación, falla acá.",
             "No se debe cambiar el estado del aviso si el descarte es inválido.",
             "El objeto Descarte se valida solo: el aviso lo recibe ya correcto.",
             'aviso.descartar("op1", "", ahora)   # JustificacionVacia; el aviso sigue pendiente'),
           N(A, S, "registro = Registro.de(", "historial", "Registro de la operación.",
             "Debe quedar quién descartó y por qué.", "El registro guarda la justificación como dato del detalle."),
           N(A, S, "self._descarte = descarte", "modificar al final",
             "Recién acá cambian el descarte, el estado y el historial.",
             "Todo lo que podía fallar ya pasó.", "Los tres cambios se hacen juntos, al final.")])
despues(esc("tupla"), [d2, d3, d4, d5])

# ─────────── HISTORIAL y ERRORES ───────────
S = "Registro"
r1 = paso(H, S, "Registro", "Registro: qué pasó, quién y cuándo",
          "§1: conservar información sobre la evolución de las emergencias. Cada operación importante deja un registro que no se edita ni se borra.",
          [N(H, S, "@dataclass(frozen=True, slots=True)", "dataclass frozen", "Inmutable.",
             "Un historial que se puede editar no sirve como prueba de lo que pasó.", "Un registro es inmutable: se agregan nuevos, nunca se corrigen los viejos."),
           N(H, S, "operacion: Operacion", "operación del catálogo",
             "El tipo de operación sale de una lista cerrada (Operacion), no de un texto libre.",
             "Para poder buscar en el historial por tipo de operación sin depender de cómo se escriba.",
             "Un Enum con todas las operaciones del sistema.",
             "Operacion.AVISO_ACEPTADO   # «aviso_aceptado»"),
           N(H, S, "recursos: tuple[str, ...]", "recursos afectados",
             "Los ids de lo que la operación tocó: el aviso, la emergencia, la misión, la unidad. Es una tupla: no se puede modificar.",
             "Cada registro tiene que decir sobre qué cosas actuó.",
             "Una tupla con los ids protege la colección: nadie la altera.",
             'recursos = ("aviso-1", "emerg-1")'),
           N(H, S, "detalle: tuple[tuple[str, str], ...] = ()", "detalle como pares",
             "Datos extra de cada operación (por ejemplo la justificación) guardados como pares (clave, texto) dentro de una tupla.",
             "Cada operación guarda datos distintos: unidad, justificación, resultado.",
             "Pares inmutables: caben en un registro inmutable. Un diccionario se podría modificar.",
             'detalle = (("justificacion", "Falsa alarma"),)'),
           N(H, S, "if not self.recursos", "registro sin recursos",
             "Un registro que no dice sobre qué actuó no sirve: se rechaza.",
             "Un historial con huecos no es confiable.", "Se valida al crear, como el resto de los valores.")])
S = "Registro.de"
r2 = paso(H, S, "Registro", "Registro.de: un atajo para crear registros",
          "Cada operación crea un registro, y cada una con datos distintos. Este atajo evita repetir el armado.",
          [N(H, S, "@classmethod", "classmethod", "Constructor alternativo.",
             "Crear un Registro a mano es largo y se repite en cada operación.", "Un atajo con nombre corto: Registro.de(...)."),
           N(H, S, "*recursos: str", "cantidad variable de ids",
             "Un `*` antes de un nombre significa «juntá todos los valores sueltos que lleguen en una tupla». Se pueden pasar uno, dos o más ids.",
             "Algunas operaciones afectan un recurso (una nota) y otras tres (una asignación).",
             "Un solo método sirve para todas: los ids se juntan solos en una tupla.",
             'Registro.de("op1", ahora, AVISO_ACEPTADO, "aviso-1", "emerg-1")   # recursos = ("aviso-1", "emerg-1")'),
           N(H, S, "**detalle: str", "datos con nombre",
             "Dos asteriscos juntan los datos con nombre en un diccionario. Cada uno se guarda como un par (clave, texto).",
             "Cada operación guarda datos diferentes: unidad, justificación, resultado.",
             "Se escriben como nombre=valor al llamar, sin armar ninguna estructura aparte.",
             'Registro.de(..., justificacion="Falsa alarma")   # detalle = (("justificacion", "Falsa alarma"),)'),
           N(H, S, "return cls(actor_id", "cls", "Crea con la clase.", "Se evita escribir el nombre de la clase.",
             "Igual que en Aviso.restaurar.")])
S = "UnidadOcupada"
r3 = paso(ER, S, "ErrorDeDominio", "Errores con nombre: cada rechazo dice por qué",
          "§8.2: si una condición no se cumple, la asignación se rechaza indicando el motivo. Cada motivo es su propio tipo de error.",
          [N(ER, S, "class UnidadOcupada(AsignacionRechazada, UnidadComprometida)", "herencia múltiple",
             "La clase hereda de dos errores a la vez. Quien atrapa «asignación rechazada» o «unidad comprometida» atrapa también a este.",
             "Este error es las dos cosas: rechaza una asignación y dice que la unidad está comprometida.",
             "Hereda de las dos: cada capa de arriba atrapa el tipo que le interesa.",
             "except AsignacionRechazada:   # atrapa UnidadOcupada\nexcept UnidadComprometida:    # también")])
r4 = dict(tipo="resumen", titulo="0 · Los errores del dominio",
          puntos=["**ErrorDeDominio** es la base: todo rechazo de una regla del negocio la hereda. Quien lo atrapa los atrapa a todos.",
                  "Cada regla tiene su propio error con nombre: AvisoNoPendiente, NotaDeOtroAutor, JustificacionVacia, RecursoDuplicado, EmergenciaCerrada…",
                  "**AsignacionRechazada** agrupa los motivos de §8.2: UnidadNoHabilitada, UnidadOcupada, VehiculoIncompatible, PersonalInsuficiente, EquipamientoInsuficiente.",
                  "Nunca se usa un error genérico de Python (KeyError, TypeError) para una regla del negocio: no dice qué pasó.",
                  "Así la capa de arriba (la API) traduce por tipo de error, sin leer el texto del mensaje."])
despues(es(A, "Aviso.restaurar"), [r1, r2, r4, r3])

# ─────────── EMERGENCIA ───────────
S = "Emergencia.__init__"
e1 = paso(E, S, "Emergencia", "Emergencia: nace de un aviso aceptado",
          "§7.2: una emergencia conserva su situación, gravedad, ubicación y el aviso de origen. Solo se crea al aceptar un aviso.",
          [N(E, S, "if not hay_texto(aviso_id)", "validar el origen",
             "La emergencia exige aviso de origen, reportante y ubicación: sin ellos no sabe de dónde vino.",
             "Una emergencia siempre nace de un aviso aceptado (§7.1).",
             "El constructor lo comprueba y lanza AceptacionInvalida: la emergencia incorrecta no existe.",
             'Emergencia("", "r1", ubicacion, ...)   # AceptacionInvalida'),
           N(E, S, "if not TipoSituacion.contiene(tipo)", "tipo y gravedad confirmados",
             "El operador confirma o corrige el tipo y la gravedad del aviso. Acá se comprueba que sigan siendo del catálogo.",
             "La emergencia guarda los datos confirmados por el operador, no los del reportante (§2.2).",
             "Se validan con `contiene` del catálogo.",
             'Emergencia(..., tipo="meteorito", ...)   # AceptacionInvalida'),
           N(E, S, "self._estado: _Estado = _ABIERTA", "nace abierta",
             "Toda emergencia empieza abierta. El estado es un objeto, no un texto.",
             "Una emergencia nueva tiene que admitir misiones.",
             "Se arranca en el estado abierto; solo el supervisor la cierra.",
             "Emergencia(...).estado   # ABIERTA"),
           N(E, S, "self._misiones: dict[str, Mision] = {}", "misiones por id",
             "Las misiones se guardan en un diccionario con su id como clave: encontrar una es directo y no hay dos con el mismo id.",
             "Las operaciones reciben el id de la misión y hay que encontrarla rápido.",
             "Un diccionario privado: nadie de afuera lo toca.",
             'self._misiones["m1"]   # la misión m1'),
           N(E, S, "self._registros: list[Registro] = [", "primer registro",
             "La emergencia nace con su primer registro: «emergencia creada». El historial nunca está vacío.",
             "§1: conservar la evolución de las emergencias.",
             "El constructor crea el primer registro; las operaciones siguientes agregan los suyos.",
             "emergencia.registros   # (emergencia_creada,)")])
S = "Emergencia.crear_mision"
e2 = paso(E, S, "Emergencia", "Crear una misión: compatible con la situación",
          "§6.4: una misión debe rechazarse cuando su tipo no está contemplado para la situación de la emergencia.",
          [N(E, S, "self._estado.permitir_modificaciones()", "permitir_modificaciones",
             "Pregunta al estado.", "Una emergencia cerrada no admite misiones nuevas.",
             "Misma pregunta que en cada operación: el estado abierto deja pasar, el cerrado rechaza."),
           N(E, S, "mision.verificar_situacion(self._tipo)", "misión compatible con la situación",
             "La misión responde si admite este tipo de situación. Si no, lanza MisionIncompatible.",
             "§6.4: no toda misión sirve para toda situación (la evacuación no aplica a un accidente vial).",
             "La emergencia le pregunta a la misión; cada tipo declara las situaciones que admite. No hay `if tipo`.",
             "Evacuacion en un accidente vial   # MisionIncompatible"),
           N(E, S, "registro = Registro.de(", "historial", "Registro.", "Debe quedar quién creó la misión.",
             "Se arma antes de guardar la misión."),
           N(E, S, "self._misiones[mision.id] = mision", "modificar al final",
             "Recién acá la misión entra a la emergencia.", "Si algo falló antes, no queda nada a medias.",
             "Misión y registro se agregan juntos, al final.")])
S = "Emergencia.asignar_mision"
e3 = paso(E, S, "Emergencia", "Asignar una misión: la emergencia coordina",
          "§8.2: antes de confirmar se verifican siete condiciones. Si una falla se rechaza indicando el motivo y no cambia nada.",
          [N(E, S, "self._estado.permitir_modificaciones()", "condición 1: emergencia abierta",
             "La primera condición de §8.2: la emergencia tiene que estar abierta.",
             "No se asignan misiones en una emergencia cerrada.", "Se le pregunta a su estado, igual que en las demás operaciones."),
           N(E, S, "mision = self._mision(mision_id)", "buscar la misión",
             "Busca la misión por id. Si no existe, lanza NoEncontrado.",
             "El operador puede pasar un id equivocado.", "Un método interno busca y falla con el id en el mensaje.",
             'emergencia.asignar_mision("zzz", ...)   # NoEncontrado: La emergencia no tiene la misión zzz'),
           N(E, S, "mision.asignar(unidad)", "condiciones 2 a 7",
             "La misión se asigna a la unidad, y ahí se verifican las demás condiciones: misión pendiente, unidad habilitada y libre, vehículo, personal y equipamiento. Si una falla, nada cambia.",
             "Si la emergencia verificara las siete condiciones, tendría que conocer vehículos, personal y equipamiento.",
             "Cada objeto verifica lo suyo: la emergencia solo coordina.",
             "unidad ocupada         # UnidadOcupada\nsin equipo de rescate   # EquipamientoInsuficiente"),
           N(E, S, "self._registros.append(registro)", "modificar al final",
             "El registro entra solo si la asignación salió bien.", "No debe quedar historia de una asignación que no ocurrió.",
             "Va después de mision.asignar: si esa línea lanza, esta no se ejecuta.")])
S = "Emergencia.cerrar"
e4 = paso(E, S, "Emergencia", "Cerrar la emergencia",
          "§7.2: la emergencia solo se cierra cuando todas sus misiones terminaron y al menos una fue exitosa.",
          [N(E, S, "siguiente = self._estado.cerrar(", "el estado decide el cierre",
             "La emergencia le pasa sus misiones al estado, y el estado decide si se puede cerrar y a cuál estado pasa.",
             "La regla de cierre depende del estado: una emergencia ya cerrada no se vuelve a cerrar.",
             "La emergencia no tiene la regla: la tiene el estado."),
           N(E, S, "self._estado = siguiente", "modificar al final",
             "Recién acá cambia.", "Si el cierre falla, la emergencia sigue abierta.",
             "El estado se cambia después de armar el registro.")])
S = "abiertas_por_prioridad"
e5 = paso(E, S, "Emergencia", "Emergencias abiertas, de más a menos urgentes",
          "PV03: el operador necesita ver primero las emergencias de gravedad alta, y a igual gravedad, la más antigua.",
          [N(E, S, "abiertas = (e for e in emergencias", "solo las abiertas",
             "Recorre las emergencias y se queda con las abiertas. No arma una lista intermedia: las va entregando de a una.",
             "Las cerradas no necesitan atención.", "Se filtra por el estado público de cada emergencia."),
           N(E, S, "sorted(abiertas, key=lambda e: e.clave_de_prioridad)", "ordenar por clave",
             "sorted ordena usando la clave que le da cada emergencia: primero la gravedad más alta y, si empatan, la más antigua.",
             "El orden de urgencia es una regla del negocio.",
             "Cada emergencia calcula su propia clave: la función no mira su gravedad.",
             "Alta 10:00 · Media 09:00 · Alta 08:00   →   Alta 08:00 · Alta 10:00 · Media 09:00"),
           N(E, S, "return tuple(", "devuelve una tupla",
             "Entrega una tupla: quien la recibe no puede reordenarla ni modificarla.",
             "Una lista se podría alterar desde afuera.", "Tupla inmutable.")])
despues(es(E, "_Abierta"), [e1, e2, e3, e4, e5])

# ─────────── MISIÓN ───────────
S = "Mision.__init__"
m0 = paso(M, S, "Mision", "Toda misión empieza igual",
          "Lo que comparten las tres misiones (evacuación, rescate, asistencia): un objetivo, nace pendiente y sin unidad.",
          [N(M, S, "if not hay_texto(objetivo)", "objetivo obligatorio",
             "Una misión sin objetivo no se puede crear.", "Sin objetivo no se sabe qué hay que hacer.",
             "Se valida al crear, antes de guardar nada.", 'Evacuacion("", 40)   # MisionInvalida'),
           N(M, S, "self._estado: _Estado = _PENDIENTE", "nace pendiente",
             "Toda misión arranca en Pendiente (§8.1).", "Los estados se recorren en orden, desde el principio.",
             "El estado inicial se fija en el constructor."),
           N(M, S, "self._asignacion: _Asignacion = _SIN_UNIDAD", "nace sin unidad",
             "Arranca con un objeto que representa «no hay unidad», no con None.",
             "Una misión pendiente todavía no tiene unidad.",
             "Con un objeto en lugar de None no hace falta preguntar «¿hay unidad?» cada vez.")])
S = "_Pendiente"
m1 = paso(M, S, "Mision", "Pendiente: solo asignar o cancelar",
          "§8.1: desde Pendiente la misión solo puede asignarse o cancelarse. Todo lo demás lo rechaza la clase base.",
          [N(M, S, "def asignar", "asignar pasa a Asignada",
             "Devuelve el estado Asignada: la transición vive acá.", "Las transiciones no pueden ser arbitrarias (§8.1).",
             "Cada estado lista solo las transiciones que permite.", "Pendiente → asignar()   # Asignada"),
           N(M, S, "def cancelar", "cancelar pasa a Cancelada",
             "Devuelve el estado Cancelada.", "El operador puede cancelar una misión que todavía no empezó.",
             "Es la segunda y última transición que Pendiente habilita.", "Pendiente → cancelar()   # Cancelada")])
S = "_Asignada"
m2 = paso(M, S, "Mision", "Asignada: cuatro salidas posibles",
          "§8.1: una misión asignada puede reasignarse, rechazarse, iniciarse o cancelarse. Cualquier otra cosa se rechaza.",
          [N(M, S, "def reasignar", "reasignar se queda asignada",
             "Reasignar devuelve el mismo estado: sigue Asignada, pero con otra unidad.",
             "El operador puede cambiar de unidad sin pasar por Pendiente.", "La transición vuelve a Asignada.",
             "Asignada → reasignar()   # Asignada"),
           N(M, S, "def rechazar", "rechazar vuelve a pendiente",
             "Si el jefe rechaza la misión, vuelve a Pendiente para poder asignarse a otra unidad.",
             "Una misión rechazada no puede quedar perdida.", "El estado devuelve Pendiente: la regla vive en la transición.",
             "Asignada → rechazar()   # Pendiente"),
           N(M, S, "def iniciar", "iniciar pasa a en ejecución",
             "El jefe inicia la misión y pasa a En ejecución.", "Es el camino normal de una misión asignada.",
             "Solo Asignada habilita iniciar.", "Asignada → iniciar()   # EnEjecucion"),
           N(M, S, "def cancelar", "cancelar desde asignada",
             "También se puede cancelar una misión ya asignada: la unidad queda libre.",
             "El operador puede arrepentirse antes de que empiece.", "Devuelve Cancelada.",
             "Asignada → finalizar()   # MisionEnEstadoInvalido (no está en la lista)")])
S = "_EnEjecucion"
m3 = paso(M, S, "Mision", "En ejecución: novedades y finalizar",
          "§8.1: solo una misión en ejecución registra novedades y puede finalizar.",
          [N(M, S, "def permitir_novedad", "pass es permitido",
             "Un `pass` significa «sí, se puede». Los demás estados heredan el rechazo.",
             "Las novedades solo tienen sentido mientras la misión está en curso.", "Solo En ejecución las habilita.",
             "En ejecución → registrar_novedad(...)   # OK\nPendiente → registrar_novedad(...)       # MisionEnEstadoInvalido"),
           N(M, S, "return _FINALIZADA", "finalizar es la única salida",
             "De acá solo se sale finalizando.", "Una misión en curso no puede cancelarse ni reasignarse.",
             "Una sola transición habilitada.", "En ejecución → finalizar()   # Finalizada")])
S = "_Finalizada"
m4 = paso(M, S, "Mision", "Finalizada: terminó, y puede ser exitosa",
          "§7.2 y §8.1: una finalizada no se reabre. Cuenta como terminada y es la única que puede ser exitosa.",
          [N(M, S, "def verificar_concluida", "ya terminó",
             "No hace nada: significa «esta misión ya terminó, no impide cerrar la emergencia».",
             "La emergencia necesita saber si todas sus misiones terminaron.",
             "Los estados vivos lanzan error; los finales no hacen nada.", "Finalizada → verificar_concluida()   # (sin error)"),
           N(M, S, "return resultado is not None and resultado.satisfactorio", "es exitosa",
             "Es exitosa si tiene un resultado y ese resultado fue satisfactorio.",
             "§7.2: para cerrar, al menos una misión tiene que haber terminado con resultado satisfactorio.",
             "El estado Finalizada responde; los demás heredan «no» por defecto.",
             "Finalizada + satisfactorio      → True\nFinalizada + no satisfactorio   → False\nCancelada                       → False")])
S = "_Cancelada"
m5 = paso(M, S, "Mision", "Cancelada: también termina, pero sin éxito",
          "§8.1: una cancelada no puede reabrirse. Termina la misión, pero nunca cuenta como exitosa.",
          [N(M, S, "class _Cancelada(_Estado)", "estado final", "Estado final.",
             "Una misión cancelada no vuelve a ningún estado anterior.", "No define ninguna transición: todo se rechaza."),
           N(M, S, "def verificar_concluida", "ya terminó", "Ya terminó.",
             "Una misión cancelada no debe impedir el cierre de la emergencia.", "Igual que Finalizada: no lanza error. Pero no define éxito: hereda «no».")])
S = "_SinUnidad"
m6 = paso(M, S, "Mision", "Sin unidad: un objeto que no hace nada",
          "Una misión pendiente no tiene unidad. En lugar de guardar None y preguntar «¿hay unidad?» en cada operación, se usa un objeto vacío.",
          [N(M, S, "class _SinUnidad(_Asignacion)", "Null Object",
             "Un objeto que representa «no hay unidad». Responde a las mismas operaciones que una unidad real, pero con un comportamiento neutro.",
             "Una misión pendiente igual se puede cancelar, y cancelar siempre libera la unidad.",
             "La misión llama a liberar() sin preguntar si hay unidad: el objeto vacío no hace nada.",
             "mision.cancelar()   # funciona con o sin unidad: no hay `if unidad is None`"),
           N(M, S, "unidad_id = None", "sin unidad",
             "Su id es None: quien pregunte por la unidad de la misión recibe None.", "La vista pública muestra «sin unidad».",
             "El dato está en el objeto, no en un campo que haya que revisar."),
           N(M, S, "def liberar(self, mision_id: str) -> None:", "liberar no hace nada",
             "No hay nada que liberar: no hace nada y no falla.", "Cancelar una pendiente no debe fallar ni preguntar nada.",
             "Liberar vacío significa «sin efecto»."),
           N(M, S, "raise NoEsJefeDeLaUnidad", "no hay jefe",
             "Sin unidad no hay jefe: pedirle que confirme un jefe lanza NoEsJefeDeLaUnidad.",
             "Solo el jefe de la unidad puede rechazar, iniciar o finalizar (§2.3).",
             "El objeto vacío rechaza con un motivo del negocio.",
             'mision sin unidad → exigir_jefe("j1")   # NoEsJefeDeLaUnidad: La misión no tiene una unidad asignada')])
S = "_ConUnidad"
m7 = paso(M, S, "Mision", "Con unidad: le pasa las operaciones a la unidad",
          "El otro objeto: cuando hay unidad, liberar y exigir_jefe son de la unidad real. La misión no distingue entre uno y otro.",
          [N(M, S, "class _ConUnidad(_Asignacion)", "guarda la unidad real",
             "Recuerda la unidad y su id.", "Cuando hay unidad, la misión necesita liberarla y consultar a su jefe.",
             "Misma interfaz que _SinUnidad: la misión no pregunta cuál tiene."),
           N(M, S, "self._unidad.liberar(mision_id)", "delegación",
             "Le pasa la operación a la unidad.", "Liberar la unidad es responsabilidad de la unidad.",
             "La misión no toca los datos internos de la unidad.")])
S = "Mision.asignar"
m8 = paso(M, S, "Mision", "Asignar: verificar y reservar en un solo paso",
          "§8.2: asignar compromete la unidad. Si algo falla, la misión queda como estaba.",
          [N(M, S, "siguiente = self._estado.asignar()", "delegación", "El estado decide.",
             "Solo una misión pendiente se puede asignar.", "El estado dice si se puede y a cuál pasa."),
           N(M, S, "unidad.comprometer(self)", "la unidad verifica todo",
             "La misión le pide a la unidad que se comprometa. La unidad revisa las condiciones y recién al final se reserva. Si una falla, lanza y nada cambió.",
             "Verificar y reservar tiene que ser un solo paso: si no, dos misiones podrían reservar la misma unidad.",
             "comprometer verifica todo y reserva al final.",
             "unidad ocupada   # UnidadOcupada; la misión sigue Pendiente"),
           N(M, S, "self._asignacion = _ConUnidad(unidad)", "modificar al final",
             "Recién ahora cambian la unidad y el estado.", "Todo lo que podía fallar ya pasó.",
             "Se cambia la asignación y después el estado, juntos, al final.")])
S = "Mision.reasignar"
m9 = paso(M, S, "Mision", "Reasignar: primero la nueva, después soltar la vieja",
          "§8.2: una misión asignada puede pasar a otra unidad. La anterior solo se libera si la nueva acepta.",
          [N(M, S, "unidad_nueva.comprometer(self)", "primero la nueva",
             "Se compromete la unidad nueva antes de soltar la anterior.",
             "Si la nueva rechaza, la misión no puede quedar sin unidad.",
             "Se verifica la nueva primero; si falla, la anterior sigue asignada y reservada.",
             "nueva unidad ocupada   # UnidadOcupada; la unidad anterior sigue reservada"),
           N(M, S, "anterior.liberar(self._id)", "liberar la anterior",
             "Recién cuando la nueva aceptó, la anterior queda libre.", "La unidad anterior tiene que poder recibir otra misión.",
             "Se libera después de reservar la nueva, nunca antes.")])
S = "Mision.finalizar"
m10 = paso(M, S, "Mision", "Finalizar: solo el jefe, y con tareas descriptas",
           "§2.3: el jefe de la unidad finaliza la misión registrando resultado y tareas realizadas.",
           [N(M, S, "siguiente = self._estado.finalizar()", "delegación", "El estado decide.",
              "Solo una misión en ejecución puede finalizarse.", "El estado dice si se puede."),
            N(M, S, "self._asignacion.exigir_jefe(jefe_id)", "solo el jefe",
              "Solo el jefe de la unidad asignada puede finalizar. La asignación responde: con unidad lo decide la unidad; sin unidad, error.",
              "Otro usuario no debe cerrar una misión ajena (§2.3).",
              "Se le pregunta a la asignación (el objeto «con» o «sin» unidad): no hay `if`.",
              'mision.finalizar("otro", ...)   # NoEsJefeDeLaUnidad'),
            N(M, S, "nuevo = Resultado(", "validar antes de liberar",
              "El resultado se crea y valida antes de liberar la unidad. Si faltan las tareas, falla y la unidad sigue reservada.",
              "Si se liberara primero y el resultado fuera inválido, la unidad quedaría libre con la misión sin terminar.",
              "Lo que puede fallar va antes de lo que modifica.",
              'mision.finalizar("j1", SATISFACTORIO, "", ahora)   # ResultadoInvalido; la unidad sigue reservada'),
            N(M, S, "self._asignacion.liberar(self._id)", "liberar la unidad",
              "La unidad queda disponible para otra misión (§8.4).", "Una misión terminada no debe retener recursos.",
              "Se libera recién cuando todo lo demás salió bien.")])
S = "Resultado"
m11 = paso(M, S, "Mision", "Resultado: qué se logró y qué se hizo",
           "§2.3: al finalizar el jefe declara el resultado y describe las tareas realizadas.",
           [N(M, S, "if not ResultadoMision.contiene", "resultado del catálogo",
              "El resultado tiene que ser «satisfactorio» o «no satisfactorio».", "Un texto libre no permite decidir si la emergencia se puede cerrar.",
              "Lista cerrada con `contiene`, como en los demás catálogos.",
              'Resultado("bien", "...", ahora)   # ResultadoInvalido'),
            N(M, S, "if not hay_texto(self.tareas)", "tareas obligatorias",
              "Finalizar exige describir las tareas realizadas.", "§2.3: el resultado no alcanza, hay que dejar qué se hizo.",
              "Se valida al crear el Resultado.", 'Resultado(SATISFACTORIO, "", ahora)   # ResultadoInvalido'),
            N(M, S, "return self.resultado is ResultadoMision.SATISFACTORIO", "satisfactorio",
              "Una propiedad que dice si el resultado fue satisfactorio: es lo que consulta el cierre de la emergencia.",
              "La emergencia necesita un sí/no, no leer el texto del resultado.",
              "El Resultado responde por sí mismo.", "Resultado(SATISFACTORIO, ...).satisfactorio   # True")])
S = "VistaMision"
m12 = paso(M, S, "Mision", "VistaMision: se mira, no se toca",
           "La Emergencia es la dueña de sus misiones. Hacia afuera entrega fotos de solo lectura, nunca la misión real.",
           [N(M, S, "@dataclass(frozen=True, slots=True)", "dataclass frozen", "Inmutable.",
              "Quien consulta una misión no debe poder cambiarla.", "Una foto inmutable de los datos: nadie la puede modificar."),
            N(M, S, "estado: EstadoMision", "estado público",
              "El estado se expone como un valor del Enum (pendiente, asignada…), no como el objeto interno.",
              "La API y la pantalla necesitan mostrar el estado sin conocer las clases internas.",
              "Un Enum serializable: un texto estable.", "vista.estado   # EstadoMision.ASIGNADA"),
            N(M, S, "novedades: tuple[Novedad, ...]", "tupla de novedades", "Tupla.",
              "Una lista se podría modificar desde afuera.", "Una tupla: se puede leer, no cambiar.")])
despues(es(M, "_Estado"), [m0, m1, m2, m3, m4, m5, m6, m7, m8, m9, m10, m11, m12])

# ─────────── VEHÍCULO / PERSONAL / EQUIPO / MISIONES CONCRETAS / DISTRIBUCIÓN ───────────
S = "Ambulancia"
v1 = paso(V, S, "Vehiculo", "Ambulancia: habilita solo asistencia sanitaria",
          "§5.4: cada categoría habilita lo suyo. La ambulancia sirve para asistencia sanitaria, y no para evacuar ni rescatar.",
          [N(V, S, "def categoria", "su categoría", "Declara de qué categoría es.", "Cada subclase dice quién es.",
             "Devuelve la categoría del catálogo: no se la pasa quien crea el objeto."),
           N(V, S, "def verificar_asistencia", "habilita su operación",
             "Sobrescribe el rechazo con un `pass`: «sí, sirvo». Las demás operaciones siguen rechazadas.",
             "La ambulancia debe poder asignarse a una asistencia sanitaria.",
             "Solo habilita lo suyo; el resto lo rechaza la clase base.",
             "Ambulancia.verificar_asistencia()   # (sin error)\nAmbulancia.verificar_rescate()      # VehiculoIncompatible")])
despues(es(V, "TransportePersonas"), [v1])

S = "Persona"
pe = paso(P, S, "Persona", "Persona: una o varias competencias",
          "§5.3: una persona tiene una o varias competencias, sin niveles ni vencimientos.",
          [N(P, S, "competencias: frozenset[Competencia]", "conjunto de competencias",
             "Un frozenset es un conjunto que no se puede modificar: sin repetidos y fácil de consultar.",
             "Una persona puede tener varias competencias (conducción y rescate).",
             "Un conjunto: no hay repetidos y se consulta con `in`.",
             "{CONDUCCION, RESCATE}"),
           N(P, S, 'object.__setattr__(self, "competencias"', "convertir a frozenset",
             "Acepta cualquier colección (lista, tupla) y la convierte en frozenset. Como la clase es frozen, se escribe de esta forma solo durante la creación.",
             "Quien crea la Persona podría pasar una lista, que se puede modificar después.",
             "Se copia a un frozenset: la persona queda inmutable aunque le pasen una lista.",
             'Persona("p1", "Ana", [CONDUCCION])   # competencias = frozenset({CONDUCCION})'),
           N(P, S, "if not self.competencias", "al menos una",
             "Una persona sin competencias no puede cubrir ningún puesto.", "§5.3: toda persona operativa tiene al menos una competencia.",
             "Se rechaza al crear.", 'Persona("p1", "Ana", [])   # RecursoInvalido'),
           N(P, S, "if not all(Competencia.contiene(c)", "todas del catálogo",
             "`all` es verdadero solo si todas las competencias pertenecen al catálogo.",
             "Una competencia inventada («hacker») no cubriría ningún puesto real.",
             "Cada competencia se valida con `contiene`.", 'Persona("p1", "Ana", ["hacker"])   # RecursoInvalido'),
           N(P, S, "return competencia in self.competencias", "tiene la competencia",
             "Pregunta si la persona tiene una competencia. Es lo que usa la distribución de puestos.",
             "La distribución necesita saber quién puede ocupar cada puesto.",
             "La Persona responde por sí misma; nadie mira su conjunto desde afuera.", 'ana.tiene(RESCATE)   # True')])
S = "Equipo"
eq = paso(EQ, S, "Equipo", "Equipo: categoría y condición",
          "§5.5: el equipamiento especializado tiene una categoría y puede estar operativo o fuera de servicio.",
          [N(EQ, S, "condicion: CondicionOperativa = CondicionOperativa.OPERATIVO", "operativo por defecto",
             "Si no se indica otra cosa, un equipo nuevo está operativo.", "Casi todo el equipamiento se carga en buen estado.",
             "Un valor por defecto sensato evita repetirlo en cada alta."),
           N(EQ, S, "if not CategoriaEquipo.contiene", "categoría del catálogo",
             "La categoría tiene que ser equipo de rescate o equipo sanitario.", "Una categoría inventada no cubriría ningún requisito.",
             "Se valida con `contiene`.", 'Equipo("e1", "radio")   # RecursoInvalido'),
           N(EQ, S, "return replace(", "replace", "Copia con un campo cambiado.",
             "Como el equipo es inmutable, «cambiar la condición» crea uno nuevo.", "La unidad reemplaza el equipo viejo por el nuevo.")])
S = "Rescate"
ms1 = paso(M, S, "Mision", "Rescate: conductor y dos rescatistas distintos",
           "§6.2: un rescate pide un conductor, dos rescatistas distintos entre sí y un equipo de rescate operativo.",
           [N(M, S, "situaciones_admitidas = frozenset(TipoSituacion)", "todas las situaciones",
              "Un rescate sirve para cualquier situación: el conjunto tiene todos los tipos.",
              "A diferencia de la evacuación, el rescate no se limita a ciertas situaciones.",
              "Se declara con el catálogo completo, sin escribir cada tipo."),
            N(M, S, "puestos = (Competencia.CONDUCCION, Competencia.RESCATE, Competencia.RESCATE)", "dos rescatistas distintos",
              "El puesto de rescate aparece dos veces: se necesitan dos personas distintas con esa competencia.",
              "Una sola persona con rescate no alcanza para dos puestos (PV07).",
              "Se lista un puesto por persona necesaria; la distribución no repite personas.",
              "Ana (conducción + rescate) y Bruno (conducción)   → no alcanza\nAna + Carla (rescate) + Bruno                     → sí"),
            N(M, S, "vehiculo.verificar_rescate()", "double dispatch", "Doble despacho.",
              "El rescate necesita un vehículo de rescate.", "La misión le pregunta al vehículo; cada categoría responde."),
            N(M, S, "self._exigir_equipo(unidad, CategoriaEquipo.EQUIPO_DE_RESCATE)", "equipo requerido",
              "Pide un equipo de rescate operativo. El método común comprueba y lanza EquipamientoInsuficiente.",
              "§6.2: sin el equipo no se puede rescatar.",
              "La subclase dice qué categoría necesita; la clase base hace la comprobación.",
              "unidad sin equipo de rescate   # EquipamientoInsuficiente: Falta un equipo_de_rescate operativo")])
S = "AsistenciaSanitaria"
ms2 = paso(M, S, "Mision", "Asistencia sanitaria: ambulancia y primeros auxilios",
           "§6.3: ambulancia, conductor, un integrante con primeros auxilios y un equipo sanitario.",
           [N(M, S, "puestos = (Competencia.CONDUCCION, Competencia.PRIMEROS_AUXILIOS)", "dos puestos",
              "Un conductor y una persona con primeros auxilios.", "§6.3: son las competencias que pide la consigna.",
              "Una tupla con los puestos: cada tipo de misión declara los suyos."),
            N(M, S, "vehiculo.verificar_asistencia()", "double dispatch", "Doble despacho.",
              "Solo una ambulancia sirve para esta misión.", "La misión le pregunta al vehículo; la ambulancia es la única que dice «sí»."),
            N(M, S, "CategoriaEquipo.EQUIPO_SANITARIO", "equipo requerido", "Equipo sanitario.",
              "§6.3: sin equipo sanitario no hay asistencia.", "Mismo método común que en el rescate, con otra categoría.")])
S = "Mision.verificar_personal"
ms3 = paso(M, S, "Mision", "Personal: personas distintas para cada puesto",
           "§5.3 y §8.2: no alcanza con que alguien tenga la competencia. Tiene que haber una persona distinta por cada puesto.",
           [N(M, S, "if not existe_distribucion(self.puestos", "personas distintas",
              "Le pregunta a la función existe_distribucion si se pueden cubrir los puestos de este tipo de misión con las personas de la unidad.",
              "Una persona con dos competencias no puede ocupar dos puestos a la vez.",
              "Una función aparte lo decide: el próximo paso explica cómo.",
              "puestos del rescate + Ana y Bruno   → False"),
            N(M, S, "raise PersonalInsuficiente", "motivo del rechazo",
              "El mensaje lista las competencias que se necesitan. Es un tipo de AsignacionRechazada.",
              "§8.2: si no se cumple una condición, se rechaza indicando el motivo.",
              "Un error propio con las competencias en el mensaje.",
              "PersonalInsuficiente: No hay personas distintas que cubran: conduccion, rescate, rescate")])
S = "existe_distribucion"
di = paso(D, S, "Unidad", "¿Se pueden cubrir los puestos con personas distintas?",
          "§8.2: la asignación necesita saber si EXISTE una forma de repartir personas distintas entre los puestos. No decide quién va a cada puesto, solo si se puede.",
          [N(D, S, "if not puestos", "caso base",
             "Si no quedan puestos por cubrir, ya está: se pudo. Es el punto donde la función deja de llamarse a sí misma.",
             "Una función que se llama a sí misma necesita un lugar donde parar.",
             "Sin puestos pendientes devuelve verdadero.", "existe_distribucion([], personas)   # True"),
           N(D, S, "primero, resto = puestos[0], puestos[1:]", "primer puesto y el resto",
             "Separa el primer puesto de los que quedan. Se intenta cubrir el primero y se pregunta lo mismo con el resto.",
             "Hay que cubrir todos los puestos, de a uno.",
             "El problema chico es igual al grande, pero con un puesto menos.",
             "[conducción, rescate, rescate]   →   primero = conducción, resto = [rescate, rescate]"),
           N(D, S, "for indice, persona in enumerate(personas)", "probar cada persona",
             "Prueba una por una las personas disponibles para el primer puesto. enumerate da también la posición, que hace falta para sacar a la persona elegida.",
             "No se sabe de antemano quién conviene en cada puesto.",
             "Se prueban todas; si una no funciona, se pasa a la siguiente."),
           N(D, S, "persona.tiene(primero)", "tiene la competencia",
             "Solo se considera a quien tiene la competencia que pide el puesto.", "No sirve poner a alguien sin la competencia.",
             "La pregunta se la hace a la Persona."),
           N(D, S, "personas[:indice] + personas[indice + 1:]", "sacar a la elegida",
             "Para los puestos que quedan se pasa la tupla sin esa persona. Así nadie ocupa dos puestos.",
             "Una persona con dos competencias no cuenta doble (§5.3, PV07).",
             "Quien ya fue elegida no está disponible para el siguiente puesto.",
             "Ana (conducción + rescate) y Bruno (conducción), puestos [conducción, rescate]:\nAna conduce → queda Bruno → Bruno no rescata → probar otra opción\nBruno conduce → queda Ana → Ana rescata ✓"),
           N(D, S, "return True", "encontró una forma",
             "Apenas una combinación cubre todos los puestos, devuelve verdadero. No hace falta seguir buscando.",
             "Solo interesa si existe, no cuántas hay.", "Corta la búsqueda en cuanto encuentra una."),
           N(D, S, "return False", "retroceder",
             "Si ninguna persona sirve para este puesto, devuelve falso. La llamada anterior entonces prueba con otra persona: eso es retroceder (backtracking).",
             "Una elección anterior puede haber sido mala: hay que poder volver atrás.",
             "El falso hace que quien llamó pruebe la siguiente persona.")])
esce = dict(tipo="escenario", titulo="0 · Ejemplo concreto", clave="distribucion", clase=None)
# orden: ... Ambulancia, Persona, Equipo, Rescate, Asistencia, verificar_personal, existe_distribucion, escenario
i = next(k for k, p in enumerate(PASOS) if es(V, "Ambulancia")(p))
PASOS[i + 1:i + 1] = [pe, eq, ms1, ms2, ms3, di, esce]
_k = next(k for k, p in enumerate(PASOS) if p.get("tipo") == "escenario" and p.get("clave") == "vehiculo_default")
_esc = PASOS.pop(_k)
PASOS.insert(next(k for k, p in enumerate(PASOS) if es(V, "Ambulancia")(p)) + 1, _esc)

# ─────────── UNIDAD y FLOTA ───────────
S = "_EnMantenimiento"
u1 = paso(UN, S, "Unidad", "La unidad también tiene un estado de servicio",
          "§8.2: una unidad en mantenimiento o fuera de servicio no recibe misiones. Es otro State, igual que el Aviso.",
          [N(UN, S, "class _EnMantenimiento(_Condicion)", "otro State",
             "La condición de servicio (habilitada, en mantenimiento, fuera de servicio) también es un objeto con su comportamiento.",
             "Una unidad no habilitada no puede recibir misiones, y la unidad no debería preguntarse «¿cuál es mi condición?».",
             "Cada condición responde por sí misma: la habilitada deja pasar, las otras lanzan.",
             "unidad en mantenimiento → comprometer(mision)   # UnidadNoHabilitada"),
           N(UN, S, "raise UnidadNoHabilitada", "motivo con nombre",
             "El error dice si está en mantenimiento o fuera de servicio.", "El operador tiene que saber por qué no se pudo asignar.",
             "Un mensaje distinto por condición.", "UnidadNoHabilitada: La unidad está en mantenimiento")])
S = "Unidad.__init__"
u2 = paso(UN, S, "Unidad", "Unidad: jefe, personal, vehículo y equipo",
          "§5.2: una unidad pertenece a una base y se compone de un jefe, personal, un vehículo y equipamiento.",
          [N(UN, S, "if not hay_texto(unidad_id)", "identificación y base",
             "La unidad necesita un id y una base operativa.", "Sin base no se sabe dónde está la unidad.",
             "Se valida al crear.", 'Unidad("", "B1", ...)   # RecursoInvalido'),
           N(UN, S, "if jefe is None or vehiculo is None", "jefe y vehículo obligatorios",
             "Una unidad no existe sin jefe ni vehículo.", "§5.2: son los dos elementos mínimos.", "Se rechaza al crear."),
           N(UN, S, "dotacion = (jefe, *personal)", "el jefe integra la dotación",
             "Arma una tupla con el jefe primero y después el resto del personal. El `*` desempaqueta: pone cada persona suelta dentro de la tupla.",
             "El jefe también cuenta como personal para cubrir puestos.", "Un solo conjunto con todos, jefe incluido.",
             "jefe = Ana ; personal = (Bruno, Carla)   →   dotacion = (Ana, Bruno, Carla)"),
           N(UN, S, "if len({p.id for p in dotacion}) != len(dotacion)", "sin personas repetidas",
             "Compara cuántos ids distintos hay con cuántas personas hay. Si no coinciden, alguien figura dos veces.",
             "Una persona no puede figurar dos veces en la unidad (§5.2).",
             "Un conjunto elimina repetidos: si el tamaño cambia, había repetidos.",
             "{Ana, Ana, Bruno} = 2 ids distintos ≠ 3 personas   # RecursoDuplicado"),
           N(UN, S, "self._personal: dict[str, Persona] = {p.id: p for p in dotacion}", "personal por id",
             "Un diccionario de id a persona, privado.", "Hay que encontrar a una persona por su id.", "Guarda a todos, jefe incluido."),
           N(UN, S, "self._mision_id: str | None = None", "una sola misión",
             "Guarda el id de la misión comprometida, o None si está libre. Es lo que dice si la unidad está ocupada.",
             "§8.4: una unidad tiene a lo sumo una misión.", "Un solo campo: None = libre.",
             "unidad._mision_id   # None → libre   ·   «m1» → ocupada")])
S = "Unidad.comprometer"
u3 = paso(UN, S, "Unidad", "Comprometer: las condiciones, en orden",
          "§8.2: la asignación verifica las condiciones en orden. Si una falla, se rechaza con el motivo y la unidad queda como estaba.",
          [N(UN, S, "self._condicion.verificar_habilitada()", "unidad habilitada",
             "Le pregunta a su condición de servicio si puede recibir misiones.", "Una unidad en mantenimiento no puede salir.",
             "Se delega en el estado de servicio: no hay `if`."),
           N(UN, S, "if self._mision_id is not None", "unidad libre",
             "Si ya tiene una misión, lanza UnidadOcupada con el id de esa misión.", "§8.4: una unidad no atiende dos misiones a la vez.",
             "Se compara con None: es el único campo que dice si está ocupada.",
             "UnidadOcupada: La unidad U1 ya tiene la misión m1"),
           N(UN, S, "self._vehiculo.verificar_operativo()", "vehículo operativo",
             "Le pregunta al vehículo si está operativo.", "§8.2: vehículo compatible y operativo.", "El vehículo responde por sí mismo."),
           N(UN, S, "mision.verificar_vehiculo(self._vehiculo)", "vehículo compatible",
             "La misión le pregunta al vehículo si le sirve.", "Cada tipo de misión necesita una categoría distinta.",
             "Doble despacho: sin `if tipo`."),
           N(UN, S, "mision.verificar_personal(self.personal)", "personal y competencias",
             "La misión comprueba si el personal alcanza para sus puestos.", "§8.2: personal y competencias.", "Usa la distribución de personas distintas."),
           N(UN, S, "mision.verificar_equipamiento(self)", "equipamiento necesario",
             "La misión comprueba que la unidad tenga el equipo que necesita.", "§8.2: equipamiento necesario.",
             "Cada tipo de misión sabe qué categoría pide."),
           N(UN, S, "self._mision_id = mision.id", "reservar al final",
             "Recién cuando todo pasó, la unidad se reserva. Es una sola línea y no puede quedar a medias.",
             "Si se reservara al principio y algo fallara después, la unidad quedaría ocupada sin misión.",
             "Todas las comprobaciones primero, la reserva después.",
             "falla el equipamiento   # EquipamientoInsuficiente; la unidad sigue libre")])
S = "Unidad.liberar"
u4 = paso(UN, S, "Unidad", "Liberar: solo la misión que la reservó",
          "§8.4: cuando la misión termina, se cancela, se rechaza o se reasigna, la unidad vuelve a estar disponible.",
          [N(UN, S, "if self._mision_id != mision_id", "solo libera su misión",
             "Si quien pide liberarla no es la misión que la tiene, lanza error.", "Otra misión no debería poder soltar una unidad ajena.",
             "Compara el id de la misión.", "unidad con m1 → liberar('m2')   # UnidadComprometida"),
           N(UN, S, "self._mision_id = None", "queda libre", "La unidad queda disponible.", "Tiene que poder recibir otra misión.",
             "Poner None es la única forma de liberar.")])
S = "Unidad.incorporar_personal"
u5 = paso(UN, S, "Unidad", "Cambiar la unidad: cuidar los mismos principios",
          "§2.4: el responsable de recursos administra personal, vehículos y equipamiento. Mientras la unidad tiene misión, no se modifica.",
          [N(UN, S, "self._exigir_modificable()", "no se modifica comprometida",
             "§8.4: una unidad con misión asignada o en ejecución no se puede cambiar.", "Cambiar la dotación en pleno servicio rompería la misión.",
             "Se comprueba antes de tocar nada; lanza UnidadComprometida."),
           N(UN, S, "if persona.id in self._personal", "sin repetidos",
             "Una persona no puede integrar la unidad dos veces.", "§5.2: unicidad de recursos.", "RecursoDuplicado con el id.",
             'unidad.incorporar_personal(ana, ...)   # RecursoDuplicado: p1 ya integra la unidad'),
           N(UN, S, "registro = Registro.de(", "historial", "Registro.", "Cada cambio de recursos deja un registro.",
             "Se arma antes de modificar."),
           N(UN, S, "self._personal[persona.id] = persona", "modificar al final",
             "Recién ahora entra la persona.", "Todo lo que podía fallar ya pasó.", "Persona y registro entran juntos.")])
S = "BaseOperativa"
f0 = paso(F, S, "Flota", "Base operativa: identificación, nombre y ubicación",
          "§5.1: el CRCE tiene varias bases operativas, cada una con identificación y ubicación.",
          [N(F, S, "if not hay_texto(self.id) or not hay_texto(self.nombre)", "datos obligatorios",
             "Una base necesita identificación, nombre y ubicación.", "Una base sin ubicación no sirve para decidir de dónde sale una unidad.",
             "Se valida al crear, igual que los demás valores.", 'BaseOperativa("", "Central", ubicacion)   # RecursoInvalido')])
S = "Flota"
f1 = paso(F, S, "Flota", "Flota: lo que ninguna unidad puede garantizar sola",
          "§5.2: una persona, un vehículo o un equipo pertenece a una sola unidad. Una unidad no ve a las demás: por eso lo controla la Flota.",
          [N(F, S, "self._bases: dict[str, BaseOperativa] = {}", "la flota conoce todo",
             "Guarda todas las bases y unidades, cada una en un diccionario por id. Es la única que las ve a todas juntas.",
             "Saber si un recurso ya está en otra unidad exige mirar todas las unidades.",
             "Una raíz de consistencia: la Flota coordina y cada Unidad cuida lo suyo.",
             "Ana ya está en la unidad U1   → no puede entrar a U2"),
           N(F, S, "return tuple(self._bases.values())", "protege la colección",
             "Quien consulta recibe una tupla (una copia inmutable), no el diccionario. Nadie puede agregar o sacar unidades por la espalda.",
             "Si devolviera el diccionario, cualquiera lo modificaría y se saltearía las validaciones.",
             "Se devuelve una tupla nueva en cada consulta.", "flota.unidades.append(x)   # AttributeError: la tupla no tiene append"),
           N(F, S, "if unidad_id not in self._unidades", "unidad inexistente",
             "Si la unidad no existe, lanza NoEncontrado con el id. Así la API puede responder «no encontrada».",
             "Pedir una unidad que no existe es un error esperable.", "Error del dominio con el id en el mensaje.",
             'flota.unidad("U9")   # NoEncontrado: No existe la unidad U9'),
           N(F, S, "if base.id in self._bases", "sin bases duplicadas",
             "Dos bases no pueden tener el mismo id: lanza RecursoDuplicado.", "Un id repetido haría ambigua la base.",
             "Se comprueba antes de guardar."),
           N(F, S, "if unidad.base_id not in self._bases", "la base debe existir",
             "Una unidad tiene que pertenecer a una base ya registrada.", "§5.1 y §5.2: toda unidad está en una base.",
             "NoEncontrado si la base no existe."),
           N(F, S, "for persona in unidad.personal", "unicidad de recursos",
             "Antes de incorporar la unidad se revisa que ninguna de sus personas, su vehículo ni su equipo estén en otra unidad.",
             "§5.2: un recurso no puede estar en dos unidades a la vez.", "Se verifica todo antes de guardar la unidad.",
             "Bruno ya integra U1 → incorporar U2 con Bruno   # RecursoDuplicado: p2 ya integra la unidad U1"),
           N(F, S, "unidad.registrar_alta(actor_id, fecha_hora)", "registrar el alta",
             "Deja el primer registro de la unidad.", "Cada unidad tiene que tener su historial desde que entra.",
             "Va antes de guardarla: si falla, la flota no cambió."),
           N(F, S, "self._unidades[unidad.id] = unidad", "modificar al final",
             "Recién acá la unidad entra a la flota.", "Todo lo que podía fallar ya pasó.", "Guardar es lo último que se hace."),
           N(F, S, "def _exigir_persona_libre", "revisar las demás unidades",
             "Recorre todas las unidades menos la que se está modificando y pregunta si ya tienen a esa persona.",
             "Al incorporar personal a una unidad hay que ignorar a esa misma unidad.",
             "Un parámetro «salvo esta unidad» la excluye de la revisión."),
           N(F, S, "ya integra la unidad", "motivo con la unidad",
             "El mensaje dice en qué unidad ya está.", "El operador tiene que saber dónde buscar.",
             "Un error con el id de la otra unidad.", "RecursoDuplicado: p2 ya integra la unidad U1")])
despues(esc("distribucion"), [u1, u2, u3, u4, u5, f0, f1])
