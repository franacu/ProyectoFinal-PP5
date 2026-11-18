"""Persistencia: esquemas versionados y repositorios Mongo.

Los repositorios Mongo se prueban con mongomock (una base Mongo simulada en memoria):
el mismo código que corre contra MongoDB real, sin necesidad de levantar Docker.
"""

from datetime import UTC, datetime

import mongomock
import pytest

from app.avisos import esquema_mongo as esquema_avisos
from app.avisos.mongo_repository import RepositorioAvisosMongo
from app.emergencias import esquema_mongo as esquema_emergencias
from app.emergencias.mongo_repository import RepositorioEmergenciasMongo
from app.internal.esquema import EsquemaIncompatible, migrar
from app.recursos import esquema_mongo as esquema_recursos
from app.recursos.mongo_repository import RepositorioFlotaMongo
from dominio.aviso import Aviso, EstadoAviso
from dominio.catalogos import CategoriaEquipo, Competencia, CondicionServicio, Gravedad, ResultadoMision, TipoSituacion
from dominio.emergencia import EstadoEmergencia
from dominio.equipamiento import Equipo
from dominio.errores import MisionInvalida, RecursoDuplicado
from dominio.flota import BaseOperativa, Flota
from dominio.mision import EstadoMision, Rescate
from dominio.personal import Persona
from dominio.unidad import Unidad
from dominio.valores import Ubicacion
from dominio.vehiculos import TransportePersonas, VehiculoRescate

T0 = datetime(2026, 11, 20, 8, 0, tzinfo=UTC)


def hora(minuto: int) -> datetime:
    return T0.replace(minute=minuto)


def aviso_nuevo() -> Aviso:
    return Aviso("ana", Ubicacion("Av. San Martín 450", "Ushuaia"), TipoSituacion.INCENDIO, Gravedad.ALTA,
                 "Humo saliendo de una vivienda", hora(0))


@pytest.fixture
def base():
    return mongomock.MongoClient(tz_aware=True)["crce"]


# ── Esquema: ida y vuelta sin pérdidas ────────────────────────

def test_aviso_con_notas_ida_y_vuelta():
    aviso = aviso_nuevo()
    aviso.agregar_nota("ana", "Se ven llamas", hora(5))

    copia = esquema_avisos.desde_documento(esquema_avisos.a_documento(aviso))

    assert esquema_avisos.a_documento(copia) == esquema_avisos.a_documento(aviso)
    assert copia.notas == aviso.notas and copia.registros == aviso.registros


def test_aviso_descartado_ida_y_vuelta_conserva_el_estado_y_su_comportamiento():
    aviso = aviso_nuevo()
    aviso.descartar("op", "Falsa alarma", hora(3))

    copia = esquema_avisos.desde_documento(esquema_avisos.a_documento(aviso))

    assert copia.estado is EstadoAviso.DESCARTADO
    assert copia.descarte == aviso.descarte


def test_emergencia_ida_y_vuelta():
    emergencia = aviso_nuevo().aceptar("op", TipoSituacion.INCENDIO, Gravedad.MEDIA, hora(4))

    copia = esquema_emergencias.desde_documento(esquema_emergencias.a_documento(emergencia))

    assert esquema_emergencias.a_documento(copia) == esquema_emergencias.a_documento(emergencia)
    assert copia.estado is EstadoEmergencia.ABIERTA


def test_el_documento_guarda_su_version_y_valores_legibles():
    documento = esquema_avisos.a_documento(aviso_nuevo())

    assert documento["version"] == esquema_avisos.VERSION_ESQUEMA
    assert (documento["tipo"], documento["gravedad_estimada"], documento["estado"]) == ("incendio", "alta", "pendiente")


# ── Esquema: versiones ────────────────────────────────────────

def test_documento_de_una_version_futura_se_rechaza():
    documento = esquema_avisos.a_documento(aviso_nuevo()) | {"version": 99}

    with pytest.raises(EsquemaIncompatible):
        esquema_avisos.desde_documento(documento)


def test_migrar_aplica_cada_paso_hasta_la_version_actual():
    """Así se absorbe un cambio de forma: una función por salto de versión, sin tocar el dominio."""
    documento_v1 = {"_id": "a1", "version": 1, "ubicacion": "Av. San Martín 450, Ushuaia"}
    migraciones = {
        1: lambda d: d | {"ubicacion": dict(zip(("direccion", "localidad"), d["ubicacion"].split(", ")))},
        2: lambda d: d | {"notas": []},
    }

    documento_v3 = migrar(documento_v1, 3, migraciones, "avisos")

    assert documento_v3 == {"_id": "a1", "version": 3, "notas": [],
                            "ubicacion": {"direccion": "Av. San Martín 450", "localidad": "Ushuaia"}}


def test_si_falta_un_paso_de_migracion_no_se_adivina():
    with pytest.raises(EsquemaIncompatible):
        migrar({"_id": "a1", "version": 1}, 3, {1: lambda d: d}, "avisos")


# ── Repositorios Mongo ────────────────────────────────────────

def test_repositorio_mongo_guarda_y_recupera_un_aviso(base):
    repositorio = RepositorioAvisosMongo(base)
    aviso = aviso_nuevo()

    repositorio.guardar(aviso)
    aviso.agregar_nota("ana", "Se ven llamas", hora(5))
    repositorio.guardar(aviso)  # guardar dos veces actualiza, no duplica

    recuperado = repositorio.obtener(aviso.id)
    assert base["avisos"].count_documents({}) == 1
    assert recuperado.notas == aviso.notas


def test_repositorio_mongo_filtra_por_estado(base):
    repositorio = RepositorioAvisosMongo(base)
    pendiente, descartado = aviso_nuevo(), aviso_nuevo()
    descartado.descartar("op", "Duplicado", hora(2))
    repositorio.guardar(pendiente)
    repositorio.guardar(descartado)

    assert [a.id for a in repositorio.listar(EstadoAviso.PENDIENTE)] == [pendiente.id]
    assert repositorio.obtener("no-existe") is None


def test_repositorio_mongo_de_emergencias(base):
    repositorio = RepositorioEmergenciasMongo(base)
    emergencia = aviso_nuevo().aceptar("op", TipoSituacion.INCENDIO, Gravedad.ALTA, hora(4))

    repositorio.guardar(emergencia)

    assert [e.id for e in repositorio.listar()] == [emergencia.id]
    assert repositorio.obtener(emergencia.id).registros == emergencia.registros


# ── Recursos y misiones (esquemas de unidades y emergencia v2) ─

BASE = BaseOperativa("B-1", "Base Centro", Ubicacion("Maipú 100", "Ushuaia"))


def unidad_de_rescate(uid="U-1", sufijo="") -> Unidad:
    return Unidad(uid, "B-1", Persona(f"ana{sufijo}", "Ana", {Competencia.RESCATE}),
                  VehiculoRescate(id=f"VR{sufijo}"),
                  (Persona(f"bruno{sufijo}", "Bruno", {Competencia.CONDUCCION}),
                   Persona(f"carla{sufijo}", "Carla", {Competencia.RESCATE})),
                  (Equipo(f"ER{sufijo}", CategoriaEquipo.EQUIPO_DE_RESCATE),))


def test_unidad_ida_y_vuelta_conserva_dotacion_condicion_e_historial():
    flota = Flota()
    flota.registrar_base(BASE)
    unidad = unidad_de_rescate()
    flota.incorporar_unidad(unidad, "resp", hora(0))
    unidad.declarar_en_mantenimiento("resp", hora(1))

    copia = esquema_recursos.unidad_desde_documento(esquema_recursos.unidad_a_documento(unidad))

    assert esquema_recursos.unidad_a_documento(copia) == esquema_recursos.unidad_a_documento(unidad)
    assert copia.condicion is CondicionServicio.EN_MANTENIMIENTO and copia.jefe.id == "ana"


def test_el_transporte_conserva_su_capacidad():
    vehiculo = TransportePersonas(id="TP-1", capacidad_evacuados=12)

    copia = esquema_recursos.vehiculo_desde_documento(esquema_recursos.vehiculo_a_documento(vehiculo))

    assert copia == vehiculo


def test_al_cargar_la_flota_se_vuelve_a_verificar_que_nadie_este_en_dos_unidades(base):
    repositorio = RepositorioFlotaMongo(base)
    repositorio.guardar_base(BASE)
    repositorio.guardar_unidad(unidad_de_rescate("U-1"))
    repositorio.guardar_unidad(unidad_de_rescate("U-2"))   # mismas personas: documento corrupto

    with pytest.raises(RecursoDuplicado):
        repositorio.cargar()


def test_emergencia_de_version_1_se_migra_sin_misiones():
    emergencia = aviso_nuevo().aceptar("op", TipoSituacion.INCENDIO, Gravedad.ALTA, hora(4))
    documento_v1 = esquema_emergencias.a_documento(emergencia) | {"version": 1}
    del documento_v1["misiones"]

    copia = esquema_emergencias.desde_documento(documento_v1)

    assert copia.misiones == ()
    assert esquema_emergencias.a_documento(copia)["version"] == 2


def test_emergencia_con_mision_asignada_ida_y_vuelta_comparte_la_unidad_de_la_flota():
    unidad = unidad_de_rescate()
    emergencia = aviso_nuevo().aceptar("op", TipoSituacion.INCENDIO, Gravedad.ALTA, hora(4))
    mision = Rescate("Rescatar")
    emergencia.crear_mision(mision, "op", hora(5))
    emergencia.asignar_mision(mision.id, unidad, "op", hora(6))
    copia_unidad = esquema_recursos.unidad_desde_documento(esquema_recursos.unidad_a_documento(unidad))

    copia = esquema_emergencias.desde_documento(esquema_emergencias.a_documento(emergencia),
                                                {copia_unidad.id: copia_unidad})
    copia.iniciar_mision(mision.id, "ana", hora(7))
    copia.finalizar_mision(mision.id, "ana", ResultadoMision.SATISFACTORIO, "Rescate", hora(8))

    assert copia.misiones[0].estado is EstadoMision.FINALIZADA
    assert copia_unidad.mision_comprometida_id is None   # la misión liberó la misma unidad de la flota


def test_una_mision_asignada_cuya_unidad_no_la_tiene_reservada_se_rechaza():
    with pytest.raises(MisionInvalida):
        Rescate.restaurar(mision_id="m1", objetivo="Rescatar", estado=EstadoMision.ASIGNADA,
                          unidad=unidad_de_rescate(), novedades=(), resultado=None)
