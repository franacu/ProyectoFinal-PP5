"""Excepciones propias del dominio. Los tests usan estas, no ValueError genérico."""


class ErrorDeDominio(Exception):
    """Base de todos los rechazos de reglas de negocio."""


class DatoDeAvisoInvalido(ErrorDeDominio):
    """Un dato obligatorio falta, está vacío o no pertenece al catálogo (R1)."""


class NotaInvalida(ErrorDeDominio):
    """La nota no tiene autor, texto o fecha (R2)."""


class NotaDeOtroAutor(ErrorDeDominio):
    """Solo el reportante del aviso puede agregarle notas (§2.1)."""


class DescarteInvalido(ErrorDeDominio):
    """El descarte no tiene operador, justificación o fecha (R4)."""


class JustificacionVacia(DescarteInvalido):
    """Descartar exige una justificación con contenido (R4)."""


class AvisoNoPendiente(ErrorDeDominio):
    """El aviso ya fue evaluado: no admite notas ni nuevas evaluaciones (R5)."""


# ── Avisos: aceptación ────────────────────────────────────────

class AceptacionInvalida(ErrorDeDominio):
    """Aceptar exige operador, fecha, tipo y gravedad confirmados dentro de catálogo (§2.2)."""


# ── Recursos y unidades (§5) ──────────────────────────────────

class RecursoInvalido(ErrorDeDominio):
    """Persona, vehículo, equipo o unidad con datos incompletos o incoherentes."""


class RecursoDuplicado(ErrorDeDominio):
    """Una persona, vehículo o equipo no puede estar en dos unidades a la vez (§5.2)."""


class NoEncontrado(ErrorDeDominio):
    """El recurso, la unidad o la misión pedidos no existen."""


class UnidadComprometida(ErrorDeDominio):
    """La unidad está reservada o ejecutando una misión: no se asigna ni se modifica (§8.4)."""


# ── Asignación de misiones (§8.2): cada rechazo dice el motivo ─

class AsignacionRechazada(ErrorDeDominio):
    """Base de los motivos por los que una unidad no puede recibir una misión."""


class UnidadNoHabilitada(AsignacionRechazada):
    """La unidad está en mantenimiento o fuera de servicio."""


class UnidadOcupada(AsignacionRechazada, UnidadComprometida):
    """La unidad ya tiene otra misión asignada o en ejecución (PV10)."""


class VehiculoIncompatible(AsignacionRechazada):
    """El vehículo no es de la categoría, no alcanza en capacidad o está fuera de servicio."""


class PersonalInsuficiente(AsignacionRechazada):
    """No existe una distribución de personas distintas que cubra los puestos (PV07)."""


class EquipamientoInsuficiente(AsignacionRechazada):
    """Falta un elemento operativo de la categoría requerida (PV09)."""


class NoEsJefeDeLaUnidad(ErrorDeDominio):
    """Un jefe solo opera misiones asignadas a su propia unidad (§2.3, PV12)."""


# ── Misiones (§6, §8) ─────────────────────────────────────────

class MisionInvalida(ErrorDeDominio):
    """La misión no tiene objetivo o cantidad válidos."""


class MisionIncompatible(ErrorDeDominio):
    """El tipo de misión no está contemplado para el tipo de situación (§6.4, PV05)."""


class MisionEnEstadoInvalido(ErrorDeDominio):
    """La operación no es una transición admitida desde el estado actual (§8.1)."""


class MisionSinConcluir(ErrorDeDominio):
    """La misión sigue pendiente, asignada o en ejecución: impide cerrar la emergencia."""


class ResultadoInvalido(ErrorDeDominio):
    """Finalizar exige resultado dentro de catálogo, descripción de tareas y fecha."""


# ── Emergencias (§7.2) ────────────────────────────────────────

class EmergenciaCerrada(ErrorDeDominio):
    """Una emergencia cerrada no admite misiones ni modificaciones operativas."""


class SinMisionExitosa(ErrorDeDominio):
    """Para cerrar hace falta al menos una misión finalizada con resultado satisfactorio."""


# ── Historial (§9) ────────────────────────────────────────────

class RegistroInvalido(ErrorDeDominio):
    """Un registro histórico necesita actor, fecha, operación y recursos."""
