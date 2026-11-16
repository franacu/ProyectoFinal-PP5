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