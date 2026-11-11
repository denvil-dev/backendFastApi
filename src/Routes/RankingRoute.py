from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse

from Config.JwtConfig import ROLE_CLAIM, decode_token
from Controller.Ranking import obtener_ranking
from Schemas.RankingSchema import (
    DimensionEnum,
    DirEnum,
    OrdenEnum,
    PeriodoEnum,
    RankingResponse,
)

ranking = APIRouter(prefix="/api/v1", tags=["Ranking"])

ROLES_RANKING = {
    "Administrador",
    "Data Steward",
    "Analista financiero",
    "Gerente / Directivo",
    "Auditor",
}
GERENTE = "Gerente / Directivo"


@ranking.get("/ranking", response_model=RankingResponse)
async def getRanking(
    sector: str | None = Query(None, description="Filtro opcional por sector"),
    dimension: DimensionEnum | None = Query(None),
    periodo: PeriodoEnum | None = Query(PeriodoEnum.mensual),
    orden: OrdenEnum = Query(OrdenEnum.ic, description="Columna de orden"),
    dir: DirEnum = Query(DirEnum.desc, description="Dirección: asc o desc"),
    limit: int = Query(
        50, ge=1, le=200, description="Cantidad de registros por página"
    ),
    offset: int = Query(0, ge=0, description="Desplazamiento para la paginación"),
    payload: dict = Depends(decode_token),
):
    rol = payload.get(ROLE_CLAIM)
    if rol not in ROLES_RANKING:
        return JSONResponse(
            status_code=403,
            content={
                "type": "about:blank",
                "title": "Forbidden",
                "status": 403,
                "detail": "No tiene permiso",
            },
            media_type="application/problem+json",
        )

    try:
        return obtener_ranking(
            sector=sector,
            dimension=dimension.value if dimension else None,
            periodo=periodo.value,
            orden=orden.value,
            direccion=dir.value,
            limit=limit,
            offset=offset,
            ocultar_posicion=rol == GERENTE,
        )

    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={
                "type": "about:blank",
                "title": "Bad Request",
                "status": 400,
                "detail": str(e),
            },
            media_type="application/problem+json",
        )
