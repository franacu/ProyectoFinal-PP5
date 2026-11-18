"""DTO de la API de emergencias y misiones."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.internal.schemas import GravedadDTO, RegistroDetalle, UbicacionDTO
from dominio.catalogos import ResultadoMision, TipoMision, TipoSituacion
from dominio.emergencia import Emergencia, EstadoEmergencia
from dominio.mision import EstadoMision, VistaMision

# ── Entrada ───────────────────────────────────────────────────


class MisionCrear(BaseModel):
    tipo: TipoMision = Field(examples=["rescate"])
    objetivo: str = Field(examples=["Rescatar a dos personas atrapadas en el primer piso"])
    cantidad_personas: int | None = Field(default=None, description="Obligatoria solo para evacuación")


class AsignacionCrear(BaseModel):
    unidad_id: str = Field(examples=["U-rescate-1"])


class RechazoCrear(BaseModel):
    justificacion: str = Field(examples=["La unidad está atendiendo un desperfecto mecánico"])


class NovedadCrear(BaseModel):
    texto: str = Field(examples=["Se rescató a la primera persona"])


class FinalizacionCrear(BaseModel):
    resultado: ResultadoMision = Field(examples=["satisfactorio"])
    tareas: str = Field(examples=["Rescate de dos personas y traslado al centro de salud"])


# ── Salida ────────────────────────────────────────────────────


class NovedadDetalle(BaseModel):
    jefe_id: str
    texto: str
    fecha_hora: datetime


class ResultadoDetalle(BaseModel):
    resultado: ResultadoMision
    tareas: str
    fecha_hora: datetime


class MisionDetalle(BaseModel):
    id: str
    tipo: TipoMision
    objetivo: str
    estado: EstadoMision
    unidad_id: str | None
    cantidad_personas: int | None = None
    novedades: list[NovedadDetalle]
    resultado: ResultadoDetalle | None

    @classmethod
    def desde_dominio(cls, m: VistaMision) -> "MisionDetalle":
        return cls(
            id=m.id, tipo=m.tipo, objetivo=m.objetivo, estado=m.estado, unidad_id=m.unidad_id,
            cantidad_personas=dict(m.datos_del_tipo).get("cantidad_personas"),
            novedades=[NovedadDetalle(jefe_id=n.jefe_id, texto=n.texto, fecha_hora=n.fecha_hora) for n in m.novedades],
            resultado=None if m.resultado is None else ResultadoDetalle(
                resultado=m.resultado.resultado, tareas=m.resultado.tareas, fecha_hora=m.resultado.fecha_hora),
        )


class MisionDelJefe(MisionDetalle):
    """Lo que ve el jefe de su misión: también dónde es y de qué se trata (§2.3)."""

    emergencia_id: str
    ubicacion: UbicacionDTO
    tipo_situacion: TipoSituacion

    @classmethod
    def desde(cls, emergencia: Emergencia, m: VistaMision) -> "MisionDelJefe":
        return cls(**MisionDetalle.desde_dominio(m).model_dump(), emergencia_id=emergencia.id,
                   ubicacion=UbicacionDTO.desde_dominio(emergencia.ubicacion), tipo_situacion=emergencia.tipo)


class EmergenciaDetalle(BaseModel):
    id: str
    aviso_id: str
    reportante_id: str
    ubicacion: UbicacionDTO
    tipo: TipoSituacion
    gravedad: GravedadDTO
    creada_en: datetime
    estado: EstadoEmergencia
    misiones: list[MisionDetalle]
    registros: list[RegistroDetalle]

    @classmethod
    def desde_dominio(cls, emergencia: Emergencia) -> "EmergenciaDetalle":
        return cls(
            id=emergencia.id,
            aviso_id=emergencia.aviso_id,
            reportante_id=emergencia.reportante_id,
            ubicacion=UbicacionDTO.desde_dominio(emergencia.ubicacion),
            tipo=emergencia.tipo,
            gravedad=GravedadDTO.desde_dominio(emergencia.gravedad),
            creada_en=emergencia.creada_en,
            estado=emergencia.estado,
            misiones=[MisionDetalle.desde_dominio(m) for m in emergencia.misiones],
            registros=[RegistroDetalle.desde_dominio(r) for r in emergencia.registros],
        )


class EmergenciaResumen(BaseModel):
    """Lo que ve el reportante de la emergencia originada por su aviso (§2.1)."""

    id: str
    tipo: TipoSituacion
    gravedad: GravedadDTO
    ubicacion: UbicacionDTO
    estado: EstadoEmergencia

    @classmethod
    def desde_dominio(cls, emergencia: Emergencia) -> "EmergenciaResumen":
        return cls(id=emergencia.id, tipo=emergencia.tipo, gravedad=GravedadDTO.desde_dominio(emergencia.gravedad),
                   ubicacion=UbicacionDTO.desde_dominio(emergencia.ubicacion), estado=emergencia.estado)
