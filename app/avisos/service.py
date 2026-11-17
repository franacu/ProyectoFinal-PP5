"""Casos de uso de avisos.

Cada caso de uso sigue los mismos pasos:
1. buscar el aviso en el repositorio;
2. pedirle la operación al dominio (las reglas viven ahí, no acá);
3. si el dominio aceptó, guardar el resultado.
Si el dominio rechaza, se lanza la excepción y no se guarda nada.
"""

from app.avisos.repository import RepositorioAvisos
from app.emergencias.repository import RepositorioEmergencias
from app.internal.reloj import Reloj
from dominio.aviso import Aviso, EstadoAviso, Nota
from dominio.catalogos import Gravedad, TipoSituacion
from dominio.emergencia import Emergencia
from dominio.errores import NoEncontrado
from dominio.valores import Ubicacion


class AvisoNoEncontrado(NoEncontrado):
    """No hay un aviso con ese identificador."""


class ServicioAvisos:
    def __init__(self, avisos: RepositorioAvisos, emergencias: RepositorioEmergencias, reloj: Reloj) -> None:
        self._avisos = avisos
        self._emergencias = emergencias
        self._reloj = reloj

    def registrar(self, reportante_id: str, ubicacion: Ubicacion, tipo: TipoSituacion,
                  gravedad_estimada: Gravedad, descripcion: str) -> Aviso:
        aviso = Aviso(reportante_id, ubicacion, tipo, gravedad_estimada, descripcion, self._reloj())
        self._avisos.guardar(aviso)
        return aviso

    def listar(self, estado: EstadoAviso | None = None) -> list[Aviso]:
        return self._avisos.listar(estado)

    def obtener(self, aviso_id: str) -> Aviso:
        aviso = self._avisos.obtener(aviso_id)
        if aviso is None:
            raise AvisoNoEncontrado(f"No existe el aviso {aviso_id}")
        return aviso

    def agregar_nota(self, aviso_id: str, autor_id: str, texto: str) -> Nota:
        aviso = self.obtener(aviso_id)
        nota = aviso.agregar_nota(autor_id, texto, self._reloj())
        self._avisos.guardar(aviso)
        return nota

    def descartar(self, aviso_id: str, operador_id: str, justificacion: str) -> Aviso:
        aviso = self.obtener(aviso_id)
        aviso.descartar(operador_id, justificacion, self._reloj())
        self._avisos.guardar(aviso)
        return aviso

    def aceptar(self, aviso_id: str, operador_id: str, tipo: TipoSituacion, gravedad: Gravedad) -> Emergencia:
        aviso = self.obtener(aviso_id)
        emergencia = aviso.aceptar(operador_id, tipo, gravedad, self._reloj())
        # Dos escrituras: primero la emergencia, después el aviso. Si la base fallara
        # entre ambas, el aviso seguiría pendiente. Unirlas en una transacción de Mongo
        # (requiere replica set) queda previsto para una etapa posterior.
        self._emergencias.guardar(emergencia)
        self._avisos.guardar(aviso)
        return emergencia
