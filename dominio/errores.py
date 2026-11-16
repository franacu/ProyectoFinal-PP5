"""Excepciones propias del dominio. Los tests usan estas, no ValueError genérico."""


class ErrorDeDominio(Exception):
    """Base de todos los rechazos de reglas de negocio."""


class DatoDeAvisoInvalido(ErrorDeDominio):
    """Un dato obligatorio falta, está vacío o no pertenece al catálogo (R1)."""


class NotaInvalida(ErrorDeDominio):
    """La nota no tiene autor o texto (R2)."""


class JustificacionVacia(ErrorDeDominio):
    """Descartar exige una justificación con contenido (R4)."""


class AvisoNoPendiente(ErrorDeDominio):
    """El aviso ya fue evaluado: no admite notas ni nuevas evaluaciones (R5)."""
