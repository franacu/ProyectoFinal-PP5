"""Casos de uso de emergencias y misiones (§2.2, §2.3, §2.5).

Cada operación sobre una misión sigue los mismos pasos:
1. cargar la flota y la emergencia (las misiones apuntan a unidades de esa flota);
2. pedirle la operación a la emergencia, que es dueña de sus misiones;
3. si el dominio la acepta, guardar las unidades involucradas y la emergencia.
Si el dominio rechaza, se lanza la excepción y no se guarda nada (PV18).
"""

from collections.abc import Callable

from app.emergencias.repository import RepositorioEmergencias
from app.internal.reloj import Reloj
from app.recursos.fabricas import nueva_mision
from app.recursos.repository import RepositorioFlota
from dominio.catalogos import ResultadoMision, TipoMision
from dominio.emergencia import Emergencia, abiertas_por_prioridad
from dominio.errores import NoEncontrado
from dominio.flota import Flota
from dominio.mision import VistaMision


class EmergenciaNoEncontrada(NoEncontrado):
    """No hay una emergencia con ese identificador."""


class ServicioEmergencias:
    def __init__(self, emergencias: RepositorioEmergencias, flota: RepositorioFlota, reloj: Reloj) -> None:
        self._emergencias = emergencias
        self._flota = flota
        self._reloj = reloj

    # ── Consultas ──────────────────────────────────────────────

    def abiertas_por_prioridad(self) -> tuple[Emergencia, ...]:
        """PV03: Alta, Media, Baja y, a igual gravedad, la aceptada primero."""
        return abiertas_por_prioridad(self._emergencias.listar(self._flota.cargar()))

    def todas(self) -> list[Emergencia]:
        return self._emergencias.listar(self._flota.cargar())

    def obtener(self, emergencia_id: str) -> Emergencia:
        return self._obtener(emergencia_id, self._flota.cargar())

    def de_aviso(self, aviso_id: str) -> Emergencia:
        """La emergencia que originó un aviso aceptado (404 si el aviso no fue aceptado)."""
        for emergencia in self._emergencias.listar(self._flota.cargar()):
            if emergencia.aviso_id == aviso_id:
                return emergencia
        raise EmergenciaNoEncontrada(f"El aviso {aviso_id} no originó una emergencia")

    def misiones_del_jefe(self, jefe_id: str) -> list[tuple[Emergencia, VistaMision]]:
        """Misiones asignadas o en ejecución de la unidad que dirige `jefe_id` (§2.3)."""
        flota = self._flota.cargar()
        unidades = {u.id for u in flota.unidades if u.jefe.id == jefe_id}
        return [(e, m) for e in self._emergencias.listar(flota) for m in e.misiones if m.unidad_id in unidades]

    # ── Operador (§2.2) ────────────────────────────────────────

    def crear_mision(self, emergencia_id: str, operador_id: str, tipo: TipoMision, objetivo: str,
                     cantidad_personas: int | None) -> VistaMision:
        mision = nueva_mision(tipo, objetivo, cantidad_personas)   # el dominio valida los datos
        emergencia = self._operar(emergencia_id, lambda e, flota, ahora: e.crear_mision(mision, operador_id, ahora))
        return self._vista(emergencia, mision.id)

    def asignar(self, emergencia_id: str, mision_id: str, unidad_id: str, operador_id: str) -> VistaMision:
        emergencia = self._operar(emergencia_id, lambda e, flota, ahora:
                                  e.asignar_mision(mision_id, flota.unidad(unidad_id), operador_id, ahora))
        return self._vista(emergencia, mision_id)

    def reasignar(self, emergencia_id: str, mision_id: str, unidad_id: str, operador_id: str) -> VistaMision:
        emergencia = self._operar(emergencia_id, lambda e, flota, ahora:
                                  e.reasignar_mision(mision_id, flota.unidad(unidad_id), operador_id, ahora))
        return self._vista(emergencia, mision_id)

    def cancelar(self, emergencia_id: str, mision_id: str, operador_id: str) -> VistaMision:
        emergencia = self._operar(emergencia_id, lambda e, flota, ahora:
                                  e.cancelar_mision(mision_id, operador_id, ahora))
        return self._vista(emergencia, mision_id)

    # ── Jefe de unidad (§2.3) ──────────────────────────────────

    def rechazar(self, emergencia_id: str, mision_id: str, jefe_id: str, justificacion: str) -> VistaMision:
        emergencia = self._operar(emergencia_id, lambda e, flota, ahora:
                                  e.rechazar_mision(mision_id, jefe_id, justificacion, ahora))
        return self._vista(emergencia, mision_id)

    def iniciar(self, emergencia_id: str, mision_id: str, jefe_id: str) -> VistaMision:
        emergencia = self._operar(emergencia_id, lambda e, flota, ahora: e.iniciar_mision(mision_id, jefe_id, ahora))
        return self._vista(emergencia, mision_id)

    def registrar_novedad(self, emergencia_id: str, mision_id: str, jefe_id: str, texto: str) -> VistaMision:
        emergencia = self._operar(emergencia_id, lambda e, flota, ahora:
                                  e.registrar_novedad(mision_id, jefe_id, texto, ahora))
        return self._vista(emergencia, mision_id)

    def finalizar(self, emergencia_id: str, mision_id: str, jefe_id: str, resultado: ResultadoMision,
                  tareas: str) -> VistaMision:
        emergencia = self._operar(emergencia_id, lambda e, flota, ahora:
                                  e.finalizar_mision(mision_id, jefe_id, resultado, tareas, ahora))
        return self._vista(emergencia, mision_id)

    # ── Supervisor (§2.5, §7.2) ────────────────────────────────

    def cerrar(self, emergencia_id: str, supervisor_id: str) -> Emergencia:
        return self._operar(emergencia_id, lambda e, flota, ahora: e.cerrar(supervisor_id, ahora))

    # ── Privado ────────────────────────────────────────────────

    def _obtener(self, emergencia_id: str, flota: Flota) -> Emergencia:
        """Privado."""
        emergencia = self._emergencias.obtener(emergencia_id, flota)
        if emergencia is None:
            raise EmergenciaNoEncontrada(f"No existe la emergencia {emergencia_id}")
        return emergencia

    def _operar(self, emergencia_id: str, operacion: Callable) -> Emergencia:
        """Privado: aplica la operación y, solo si el dominio la acepta, guarda unidades y emergencia.

        Se guardan las unidades que la emergencia usaba antes y después de la operación:
        así queda registrada tanto la unidad que se reserva como la que se libera.
        """
        flota = self._flota.cargar()
        emergencia = self._obtener(emergencia_id, flota)
        antes = {m.unidad_id for m in emergencia.misiones}
        operacion(emergencia, flota, self._reloj())
        despues = {m.unidad_id for m in emergencia.misiones}
        for unidad_id in (antes | despues) - {None}:
            self._flota.guardar_unidad(flota.unidad(unidad_id))
        self._emergencias.guardar(emergencia)
        return emergencia

    def _vista(self, emergencia: Emergencia, mision_id: str) -> VistaMision:
        """Privado: la foto de solo lectura de una misión de la emergencia."""
        return next(m for m in emergencia.misiones if m.id == mision_id)
