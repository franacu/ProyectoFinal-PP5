"""Traducción de los errores del dominio a respuestas HTTP.

El dominio no sabe nada de HTTP: lanza sus propias excepciones. Acá se decide qué
código recibe el cliente. Se recorre la jerarquía de la excepción (su MRO) y se usa
el primer código definido, de lo más específico a lo más general:

| Error del dominio                                  | Código | Significado                      |
|----------------------------------------------------|--------|----------------------------------|
| NoEncontrado (y subclases)                         | 404    | El recurso no existe             |
| NotaDeOtroAutor, NoEsJefeDeLaUnidad                | 403    | Existe, pero no le corresponde   |
| AvisoNoPendiente, EmergenciaCerrada, Mision…       | 409    | Choca con el estado actual       |
| Cualquier otro ErrorDeDominio                      | 422    | Datos que violan una regla       |
| EsquemaIncompatible (persistencia)                 | 500    | Documento ilegible en la base    |
"""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.auth.usuario import AccesoDenegado
from app.internal.esquema import EsquemaIncompatible
from dominio import errores

_CODIGOS: dict[type[Exception], int] = {
    errores.NoEncontrado: status.HTTP_404_NOT_FOUND,
    errores.NotaDeOtroAutor: status.HTTP_403_FORBIDDEN,
    errores.NoEsJefeDeLaUnidad: status.HTTP_403_FORBIDDEN,
    errores.AvisoNoPendiente: status.HTTP_409_CONFLICT,
    errores.EmergenciaCerrada: status.HTTP_409_CONFLICT,
    errores.UnidadComprometida: status.HTTP_409_CONFLICT,
    errores.AsignacionRechazada: status.HTTP_409_CONFLICT,
    errores.MisionEnEstadoInvalido: status.HTTP_409_CONFLICT,
    errores.MisionSinConcluir: status.HTTP_409_CONFLICT,
    errores.SinMisionExitosa: status.HTTP_409_CONFLICT,
    errores.RecursoDuplicado: status.HTTP_409_CONFLICT,
    errores.ErrorDeDominio: status.HTTP_422_UNPROCESSABLE_CONTENT,
}


def codigo_para(error: Exception) -> int:
    """Código HTTP que corresponde a un error (lo usa el manejador y lo verifican los tests)."""
    for clase in type(error).__mro__:
        if clase in _CODIGOS:
            return _CODIGOS[clase]
    return status.HTTP_500_INTERNAL_SERVER_ERROR


def _error_de_dominio(_request: Request, error: errores.ErrorDeDominio) -> JSONResponse:
    """Privada: manejador registrado en la aplicación."""
    return JSONResponse(status_code=codigo_para(error),
                        content={"detail": str(error), "error": type(error).__name__})


def _esquema_incompatible(_request: Request, error: EsquemaIncompatible) -> JSONResponse:
    """Privada: manejador registrado en la aplicación."""
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        content={"detail": str(error), "error": "EsquemaIncompatible"})


def _acceso_denegado(_request: Request, error: AccesoDenegado) -> JSONResponse:
    """Privada: el recurso existe pero no le corresponde al usuario."""
    return JSONResponse(status_code=status.HTTP_403_FORBIDDEN,
                        content={"detail": str(error), "error": "AccesoDenegado"})


def registrar_manejadores(aplicacion: FastAPI) -> None:
    aplicacion.add_exception_handler(errores.ErrorDeDominio, _error_de_dominio)
    aplicacion.add_exception_handler(AccesoDenegado, _acceso_denegado)
    aplicacion.add_exception_handler(EsquemaIncompatible, _esquema_incompatible)
