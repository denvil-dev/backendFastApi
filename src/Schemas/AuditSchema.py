from datetime import datetime, timezone
from uuid import UUID
from pydantic import BaseModel, Field


class UserAudit(BaseModel):
    # Nota: El tipo correcto para anotaciones es UUID, no uuid4 (que es la función)
    id: UUID = Field(..., description="ID del usuario")


class AuditSchema(BaseModel):
    accion: str = Field(
        ..., description="Información del usuario que realizó la acción"
    )
    detalle: str = Field(..., description="Acción realizada por el usuario")

    # Aquí cambiamos a datetime. Puedes asignarle un valor por defecto con zona horaria UTC
    fecha_evento: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Marca de tiempo de la acción",
    )
    id_usuario: UUID | None = Field(
        None, description="ID del usuario que realizó la acción, si está autenticado"
    )


class AuditRecordResponse(BaseModel):
    id_bitacora: UUID
    accion: str
    detalle: str
    fecha_evento: datetime | None
    id_usuario: UUID | None


class AuditQueryResponse(BaseModel):
    items: list[AuditRecordResponse]
    total: int
    limit: int
    offset: int
