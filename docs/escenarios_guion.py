"""Escenarios concretos: «sin esto pasa tal problema / con esto no pasa».

Cada bloque es (clase, título, texto_o_código). Los bloques `sin` y `con` son código que se
EJECUTA al generar la página: la salida que se ve es la real, no escrita a mano.
  historia  : la situación del negocio
  sin       : cómo sería sin la decisión (ejemplo hipotético, escrito acá)
  problema  : qué sale mal
  con       : el código real del proyecto
  conclusion: cómo explicárselo al profesor
"""

PREAMBULO = "import sys; sys.path.insert(0, RAIZ)"

ESCENARIOS = {
"catalogo": dict(titulo="Catálogos: la lista cerrada en acción", bloques=[
    ("historia", "Situación", "El enunciado fija listas cerradas: tres tipos de situación, tres niveles de gravedad, cuatro competencias, tres categorías de vehículo. Miremos cómo quedaron en el código."),
    ("con", "Los catálogos reales del proyecto", """from dominio.catalogos import TipoSituacion, Gravedad, Competencia, CategoriaVehiculo
print([t.value for t in TipoSituacion])
print([(g.name, g.value) for g in Gravedad])
print([c.value for c in Competencia])
print([c.value for c in CategoriaVehiculo])"""),
    ("historia", "Situación", "Un operador carga tres avisos de la misma inundación, tipeados a mano y de formas distintas. Sin catálogo, el tipo es un texto libre."),
    ("sin", "Sin catálogo: el tipo es un texto libre", """avisos = [{"tipo": "inundacion"}, {"tipo": "Inundación"}, {"tipo": "inundcion"}]
print(len([a for a in avisos if a["tipo"] == "inundacion"]), "de", len(avisos))"""),
    ("problema", "Qué sale mal", "Las tres son la misma situación, pero el sistema encuentra una sola. Las otras dos quedan fuera de las búsquedas, de la prioridad y de la compatibilidad con misiones (§6.4), y nadie se entera."),
    ("con", "Con catálogo: el error aparece al cargar", """from datetime import datetime
from dominio.aviso import Aviso
from dominio.valores import Ubicacion
Aviso("rep1", Ubicacion("Mitre 100", "Rosario"), "inundcion", Gravedad.ALTA, "Calle cortada", datetime(2026, 11, 20, 10, 0))"""),
    ("historia", "Segunda razón: ordenar por gravedad", "§4: las emergencias se atienden de más grave a menos grave. Si la gravedad fuera texto, ¿qué orden darían?"),
    ("sin", "Sin catálogo: gravedad como texto", """print(sorted(["media", "alta", "baja"], reverse=True))"""),
    ("problema", "Qué sale mal", "Alfabéticamente «media» queda primero y «alta» última: se atendería primero lo moderado."),
    ("con", "Con catálogo: cada nivel lleva su número", """print(sorted(Gravedad, key=lambda g: g.value, reverse=True))"""),
    ("conclusion", "Cómo se lo explico al profesor", "Usé Enum porque el enunciado define listas cerradas. Un texto libre deja pasar errores de tipeo sin avisar y no se puede ordenar por prioridad. Con Enum el error aparece al cargar el dato y cada gravedad lleva un número que permite ordenar."),
]),
"frozen": dict(titulo="Por qué la Ubicación no se puede modificar", bloques=[
    ("historia", "Situación", "Entra un aviso en «Mitre 100, Rosario». Al aceptarlo se crea la Emergencia con esa misma ubicación: el aviso y la emergencia comparten el mismo objeto, no una copia."),
    ("sin", "Sin frozen: una ubicación que se puede editar", """class UbicacionMutable:
    def __init__(self, direccion, localidad):
        self.direccion, self.localidad = direccion, localidad

u = UbicacionMutable("Mitre 100", "Rosario")
ubicacion_del_aviso = u
ubicacion_de_la_emergencia = u      # comparten el mismo objeto
ubicacion_del_aviso.localidad = ""  # alguien edita el aviso y borra la localidad
print(repr(ubicacion_de_la_emergencia.localidad))"""),
    ("problema", "Qué sale mal", "Editar el aviso cambió también la emergencia, sin pasar por ninguna validación. La emergencia queda sin localidad y la unidad no sabe adónde ir. Y es un error muy difícil de rastrear: nadie tocó la emergencia."),
    ("con", "Con frozen: el intento falla en el acto", """from dominio.valores import Ubicacion
u = Ubicacion("Mitre 100", "Rosario")
u.localidad = 'Salta'"""),
    ("historia", "Situación", "¿Y si de verdad hay que corregir la localidad? Se crea otra ubicación; las que ya existían no se tocan."),
    ("con", "Corregir = crear una nueva, validada", """from dataclasses import replace
nueva = replace(u, localidad="Funes")
print(u)
print(nueva)
Ubicacion("Mitre 100", "")"""),
    ("conclusion", "Cómo se lo explico al profesor", "No quiero que se modifique porque la ubicación se comparte entre el Aviso y la Emergencia: si alguien la cambiara en un lado, cambiaría en los dos y sin validar. Al ser inmutable se valida una sola vez, al crearla, y desde ahí es válida para todos los que la usan."),
]),
"slots": dict(titulo="Para qué sirve slots", bloques=[
    ("historia", "Situación", "Alguien escribe mal el nombre de un campo al querer corregir un dato (`localidd` en vez de `localidad`)."),
    ("sin", "Sin slots: Python crea un atributo nuevo sin avisar", """from dataclasses import dataclass

@dataclass
class UbicacionSinSlots:
    direccion: str
    localidad: str

u = UbicacionSinSlots("Mitre 100", "Rosario")
u.localidd = "Funes"        # error de tipeo
print(u.localidad, "|", u.__dict__)"""),
    ("problema", "Qué sale mal", "No hay ningún error: se creó un atributo `localidd` que nadie usa, y la localidad real sigue siendo Rosario. La corrección \"se hizo\" pero no tuvo efecto."),
    ("con", "Con slots: no existe lugar donde guardar un campo inventado", """from dominio.valores import Ubicacion
u = Ubicacion("Mitre 100", "Rosario")
print(hasattr(u, "__dict__"))"""),
    ("conclusion", "Cómo se lo explico al profesor", "slots fija los únicos campos que existen. Sin él, un error de tipeo crea un dato fantasma sin aviso. Es una protección barata que se suma a frozen."),
]),
"estado_if": dict(titulo="Por qué el estado decide y no un if", bloques=[
    ("historia", "Situación", "§7.1: un aviso descartado ya no puede recibir notas. Con un campo `estado` de texto, cada operación del Aviso tendría que acordarse de revisarlo."),
    ("sin", "Sin State: un `if` en cada operación", """class AvisoConIf:
    def __init__(self):
        self.estado = "descartado"
        self.notas = []
    def aceptar(self):
        if self.estado != "pendiente":
            raise ValueError("ya no está pendiente")
    def agregar_nota(self, texto):        # acá nos olvidamos el if
        self.notas.append(texto)

a = AvisoConIf()
a.agregar_nota("llegó tarde")
print(a.estado, a.notas)"""),
    ("problema", "Qué sale mal", "Un descartado aceptó una nota. Con diez operaciones y cinco estados, olvidarse un `if` es cuestión de tiempo y el sistema no avisa."),
    ("con", "Con State: es el estado quien responde", """from datetime import datetime
from dominio.aviso import Aviso
from dominio.catalogos import Gravedad, TipoSituacion
from dominio.valores import Ubicacion
ahora = datetime(2026, 11, 20, 10, 0)
aviso = Aviso("rep1", Ubicacion("Mitre 100", "Rosario"), TipoSituacion.INUNDACION, Gravedad.ALTA, "Calle cortada", ahora)
aviso.descartar("op1", "Duplicado de otro aviso", ahora)
aviso.agregar_nota("rep1", "llegó tarde", ahora)"""),
    ("conclusion", "Cómo se lo explico al profesor", "Cada estado es una clase que sabe qué admite. El Aviso no pregunta «¿qué estado sos?»: le pasa la operación y el estado responde. No hay un `if` que se pueda olvidar, y preguntar el tipo con `if` rompe con POO: cada objeto debe responder por sí mismo."),
]),
"fallar_antes": dict(titulo="Fallar antes de modificar", bloques=[
    ("historia", "Situación", "El operador acepta un aviso pero se equivoca al cargar la gravedad (escribe 5)."),
    ("sin", "Sin cuidado: se modifica primero y se valida después", """class AvisoMalo:
    estado = "pendiente"
    def aceptar(self, gravedad):
        self.estado = "aceptado"                  # cambia primero
        if gravedad not in (1, 2, 3):
            raise ValueError("gravedad inválida")  # falla después

a = AvisoMalo()
try:
    a.aceptar(5)
except ValueError:
    pass
print(a.estado)"""),
    ("problema", "Qué sale mal", "El operador vio un error, pero el aviso quedó «aceptado» sin ninguna emergencia. Ya no está pendiente, por lo que no se puede volver a evaluar (§7.1): el aviso queda perdido."),
    ("con", "Con el proyecto: el aviso sigue igual que antes", """from datetime import datetime
from dominio.aviso import Aviso
from dominio.catalogos import Gravedad, TipoSituacion
from dominio.errores import ErrorDeDominio
from dominio.valores import Ubicacion
ahora = datetime(2026, 11, 20, 10, 0)
aviso = Aviso("rep1", Ubicacion("Mitre 100", "Rosario"), TipoSituacion.INUNDACION, Gravedad.ALTA, "Calle cortada", ahora)
try:
    aviso.aceptar("op1", TipoSituacion.INUNDACION, 5, ahora)
except ErrorDeDominio as e:
    print("Error:", e)
print(aviso.estado, len(aviso.registros))"""),
    ("conclusion", "Cómo se lo explico al profesor", "Primero construyo todo lo que puede fallar (la emergencia valida tipo, gravedad y operador) y recién al final cambio el estado. Así un error no deja el aviso a medias: sigue pendiente y se puede evaluar otra vez."),
]),
"tupla": dict(titulo="Por qué se devuelven tuplas y no listas", bloques=[
    ("historia", "Situación", "§2.1: solo el reportante agrega notas y cada nota conserva autor, fecha y hora. Si el aviso entregara su lista interna, cualquiera podría saltearse esas reglas."),
    ("sin", "Sin protección: el aviso entrega su lista", """class AvisoAbierto:
    def __init__(self):
        self.notas = []

a = AvisoAbierto()
a.notas.append("nota sin autor ni fecha")
print(a.notas)"""),
    ("problema", "Qué sale mal", "Se agregó una nota sin autor ni fecha, sin pasar por las reglas. Y también podría borrarse el historial con `a.notas.clear()`."),
    ("con", "Con el proyecto: se entrega una tupla", """from datetime import datetime
from dominio.aviso import Aviso
from dominio.catalogos import Gravedad, TipoSituacion
from dominio.valores import Ubicacion
ahora = datetime(2026, 11, 20, 10, 0)
aviso = Aviso("rep1", Ubicacion("Mitre 100", "Rosario"), TipoSituacion.INUNDACION, Gravedad.ALTA, "Calle cortada", ahora)
aviso.notas.append("nota sin autor ni fecha")"""),
    ("con", "Y por el camino correcto, las reglas se aplican", """aviso.agregar_nota("otro-usuario", "hola", ahora)"""),
    ("conclusion", "Cómo se lo explico al profesor", "La lista vive adentro del Aviso y hacia afuera devuelvo una tupla, que no se puede modificar. Así la única forma de agregar una nota es `agregar_nota`, que controla autor, fecha y estado. Es proteger las colecciones."),
]),
"vehiculo_default": dict(titulo="Por qué el vehículo rechaza por defecto", bloques=[
    ("historia", "Situación", "Mañana el CRCE incorpora una categoría nueva de vehículo (por ejemplo, una lancha) y nadie revisa para qué misiones sirve."),
    ("sin", "Sin rechazo por defecto: se enumeran los que NO sirven", """def sirve_para_evacuar(categoria):
    if categoria == "ambulancia":
        return False
    return True          # el resto sirve

print(sirve_para_evacuar("lancha"))"""),
    ("problema", "Qué sale mal", "La categoría nueva quedó habilitada para evacuar sin que nadie lo decidiera. Se podría asignar una lancha a una evacuación."),
    ("con", "Con rechazo por defecto: lo no declarado queda prohibido", """from dataclasses import dataclass
from dominio.catalogos import CategoriaVehiculo
from dominio.vehiculos import Vehiculo

@dataclass(frozen=True, kw_only=True)
class Lancha(Vehiculo):
    @property
    def categoria(self):
        return CategoriaVehiculo.VEHICULO_DE_RESCATE

Lancha(id="L1").verificar_evacuacion(5)"""),
    ("conclusion", "Cómo se lo explico al profesor", "Prefiero que lo no declarado esté prohibido: si agrego una categoría y me olvido de algo, el sistema rechaza (seguro) en lugar de aceptar por error. Cada categoría habilita explícitamente solo lo suyo."),
]),
"prioridad": dict(titulo="Prioridad en acción: tres emergencias", bloques=[
    ("historia", "Situación", "Hay tres emergencias abiertas: A es media (aceptada 08:00), B es alta (11:00) y C es alta (09:00). ¿En qué orden se atienden?"),
    ("con", "Con el proyecto: se ordenan con la clave de prioridad", """from datetime import datetime
from dominio.catalogos import Gravedad, TipoSituacion
from dominio.emergencia import Emergencia, abiertas_por_prioridad
from dominio.valores import Ubicacion
u = Ubicacion("Mitre 100", "Rosario")
def emergencia(nombre, gravedad, hora):
    return Emergencia(nombre, "rep1", u, TipoSituacion.INCENDIO, gravedad, datetime(2026, 11, 20, hora, 0), "op1")
lista = [emergencia("A (media, 08:00)", Gravedad.MEDIA, 8),
         emergencia("B (alta, 11:00)", Gravedad.ALTA, 11),
         emergencia("C (alta, 09:00)", Gravedad.ALTA, 9)]
for e in abiertas_por_prioridad(lista):
    print(e.aviso_id, "  clave:", -e.gravedad.value, e.creada_en.strftime("%H:%M"))"""),
    ("conclusion", "Cómo se lo explico al profesor", "Primero las altas y, entre las altas, la más antigua: C, después B, al final A aunque haya llegado primero. La clave es una tupla (menos la gravedad, fecha): el signo menos hace que ALTA quede adelante al ordenar de menor a mayor, y la fecha desempata."),
]),
"distribucion": dict(titulo="¿Por qué probar y volver atrás? Ana, Bruno y Carla", bloques=[
    ("historia", "Situación", "Un rescate pide tres puestos: conducción, rescate y rescate. La unidad tiene a Ana (conduce y rescata), Bruno (solo conduce) y Carla (solo rescata). ¿Alcanza?"),
    ("sin", "Sin volver atrás: se elige siempre la primera persona que sirve", """def alcanza_rapido(puestos, personas):
    libres = list(personas)
    for puesto in puestos:
        elegida = next((p for p in libres if puesto in p[1]), None)
        if elegida is None:
            return False
        libres.remove(elegida)
    return True

ana = ("Ana", {"conduccion", "rescate"})
bruno = ("Bruno", {"conduccion"})
carla = ("Carla", {"rescate"})
print(alcanza_rapido(["conduccion", "rescate", "rescate"], [ana, bruno, carla]))"""),
    ("problema", "Qué sale mal", "Dice que no alcanza, pero sí alcanza: Ana fue a conducir (era la primera que servía), Carla tomó un rescate y para el otro rescate no quedó nadie. Si Bruno conducía, Ana y Carla rescataban."),
    ("con", "Con el proyecto: prueba, y si no sirve vuelve atrás", """from dominio.catalogos import Competencia as C
from dominio.distribucion import existe_distribucion
from dominio.personal import Persona
ana = Persona("p1", "Ana", {C.CONDUCCION, C.RESCATE})
bruno = Persona("p2", "Bruno", {C.CONDUCCION})
carla = Persona("p3", "Carla", {C.RESCATE})
print(existe_distribucion((C.CONDUCCION, C.RESCATE, C.RESCATE), (ana, bruno, carla)))
print(existe_distribucion((C.CONDUCCION, C.RESCATE, C.RESCATE), (ana, carla)))"""),
    ("conclusion", "Cómo se lo explico al profesor", "Elegir siempre la primera persona que sirve puede fallar aunque exista un reparto. Por eso la función prueba: pone a alguien en el primer puesto y resuelve el resto; si no sale, vuelve atrás y prueba con otra persona. Con Ana y Carla solas da False, porque Ana no puede conducir y rescatar a la vez."),
]),
}
