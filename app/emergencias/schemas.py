"""DTO de la API de emergencias."""

from datetime import datetime

from pydantic import BaseModel

from app.internal.schemas import GravedadDTO, RegistroDetalle, UbicacionDTO
from dominio.catalogos import TipoSituacion
from dominio.emergencia import Emergencia, EstadoEmergencia


class EmergenciaDetalle(BaseModel):
    id: str
    aviso_id: str
    reportante_id: str
    ubicacion: UbicacionDTO
    tipo: TipoSituacion
    gravedad: GravedadDTO
    creada_en: datetime
    estado: EstadoEmergencia
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
            registros=[RegistroDetalle.desde_dominio(r) for r in emergencia.registros],
        )
