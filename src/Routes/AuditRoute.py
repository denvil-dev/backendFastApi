from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from Config.JwtConfig import ROLE_CLAIM, decode_token
from Controller.Bitacora import consultarBitacora
from Schemas.AuditSchema import AuditQueryResponse

audit = APIRouter(prefix="/api/v1", tags=["Auditoría"])


@audit.get("/auditoria", response_model=AuditQueryResponse)
def consultar_auditoria(
    id_usuario: UUID | None = Query(None),
    accion: str | None = Query(None, max_length=40),
    recurso: str | None = Query(None, max_length=200),
    ip: str | None = Query(None, max_length=45),
    fecha_desde: datetime | None = Query(None),
    fecha_hasta: datetime | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    payload: dict = Depends(decode_token),
):
    """Devuelve eventos filtrados únicamente a usuarios con rol Auditor."""
    if payload.get(ROLE_CLAIM) != "Auditor":
        raise HTTPException(
            status_code=403, detail="Solo el rol Auditor puede consultar la bitácora"
        )

    if fecha_desde and fecha_hasta and fecha_desde > fecha_hasta:
        raise HTTPException(
            status_code=422,
            detail="fecha_desde no puede ser posterior a fecha_hasta",
        )

    return consultarBitacora(
        id_usuario=id_usuario,
        accion=accion,
        recurso=recurso,
        ip=ip,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        limit=limit,
        offset=offset,
    )
