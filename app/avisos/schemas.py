"""DTO de la API de avisos (lo que entra y sale como JSON)."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.internal.schemas import GravedadDTO, RegistroDetalle, UbicacionDTO
from dominio.aviso import Aviso, Descarte, EstadoAviso, Nota
from dominio.catalogos import TipoSituacion

# ── Entrada ───────────────────────────────────────────────────


class AvisoCrear(BaseModel):
    ubicacion: UbicacionDTO
    tipo: TipoSituacion = Field(examples=["incendio"])
    gravedad_estimada: GravedadDTO = Field(examples=["alta"])
    descripcion: str = Field(examples=["Humo saliendo de una vivienda"])


class NotaCrear(BaseModel):
    texto: str = Field(examples=["Ahora se ven llamas en el techo"])


class DescarteCrear(BaseModel):
    justificacion: str = Field(examples=["Aviso duplicado de uno ya atendido"])


class AceptacionCrear(BaseModel):
    """El operador confirma o corrige el tipo y la gravedad."""

    tipo: TipoSituacion = Field(examples=["incendio"])
    gravedad: GravedadDTO = Field(examples=["alta"])


# ── Salida ────────────────────────────────────────────────────


class NotaDetalle(BaseModel):
    autor_id: str
    texto: str
    fecha_hora: datetime

    @classmethod
    def desde_dominio(cls, nota: Nota) -> "NotaDetalle":
        return cls(autor_id=nota.autor_id, texto=nota.texto, fecha_hora=nota.fecha_hora)


class DescarteDetalle(BaseModel):
    operador_id: str
    justificacion: str
    fecha_hora: datetime

    @classmethod
    def desde_dominio(cls, descarte: Descarte) -> "DescarteDetalle":
        return cls(operador_id=descarte.operador_id, justificacion=descarte.justificacion,
                   fecha_hora=descarte.fecha_hora)


class AvisoDetalle(BaseModel):
    id: str
    reportante_id: str
    ubicacion: UbicacionDTO
    tipo: TipoSituacion
    gravedad_estimada: GravedadDTO
    descripcion: str
    registrado_en: datetime
    estado: EstadoAviso
    notas: list[NotaDetalle]
    descarte: DescarteDetalle | None
    registros: list[RegistroDetalle]

    @classmethod
    def desde_dominio(cls, aviso: Aviso) -> "AvisoDetalle":
        return cls(
            id=aviso.id,
            reportante_id=aviso.reportante_id,
            ubicacion=UbicacionDTO.desde_dominio(aviso.ubicacion),
            tipo=aviso.tipo,
            gravedad_estimada=GravedadDTO.desde_dominio(aviso.gravedad_estimada),
            descripcion=aviso.descripcion,
            registrado_en=aviso.registrado_en,
            estado=aviso.estado,
            notas=[NotaDetalle.desde_dominio(n) for n in aviso.notas],
            descarte=None if aviso.descarte is None else DescarteDetalle.desde_dominio(aviso.descarte),
            registros=[RegistroDetalle.desde_dominio(r) for r in aviso.registros],
        )
