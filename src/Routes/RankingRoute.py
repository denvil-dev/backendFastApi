from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from sqlalchemy import asc, desc, select
from Config.DatabaseConfig import SessionLocal
from Models.RankingModel import VEntidadesCotizacion, VRanking
from Schemas.RankingSchema import (
    DimensionEnum,
    DirEnum,
    OrdenEnum,
    PeriodoEnum,
    RankingResponse,
)

ranking = APIRouter(prefix="/api/v1", tags=["Ranking"])


@ranking.get("/ranking", response_model=RankingResponse)
async def getRanking(
    sector: str | None = Query(None, description="Filtro opcional por sector"),
    dimension: DimensionEnum | None = Query(None),
    periodo: PeriodoEnum | None = Query(PeriodoEnum.mensual),
    orden: OrdenEnum = Query(OrdenEnum.ic, description="Columna de orden"),
    dir: DirEnum = Query(DirEnum.desc, description="Dirección: asc o desc"),
    limit: int = Query(
        50, ge=1, le=200, description="Cantidad de registros por página"
    ),  # <-- NUEVO (Paginación)
    offset: int = Query(
        0, ge=0, description="Desplazamiento para la paginación"
    ),  # <-- NUEVO (Paginación)
):
  try:
    with SessionLocal() as session:
      stmt = select(
          VRanking.posicion_general.label("posicion"),
          VEntidadesCotizacion.id_entidad.label("entidadId"),
          VEntidadesCotizacion.nombre.label("entidad"),
          VEntidadesCotizacion.sector,
          VEntidadesCotizacion.ic,
          VEntidadesCotizacion.variacion_pct.label("variacionPct"),
      ).join(VRanking, VEntidadesCotizacion.id_entidad == VRanking.id_entidad)

      # 1. Filtros
      if sector:
        stmt = stmt.where(VEntidadesCotizacion.sector == sector)

      # 2. Ordenamiento
      columnas_orden = {
          "posicion": VRanking.posicion_general,
          "entidad": VEntidadesCotizacion.nombre,
          "sector": VEntidadesCotizacion.sector,
          "ic": VEntidadesCotizacion.ic,
          "variacionPct": VEntidadesCotizacion.variacion_pct,
      }

      columna_seleccionada = columnas_orden.get(orden.value, VRanking.ic)

      if dir.value == "asc":
        stmt = stmt.order_by(asc(columna_seleccionada))
      else:
        stmt = stmt.order_by(desc(columna_seleccionada))

      # 3. Paginación aplicándose a la sentencia SQL de SQLAlchemy
      stmt = stmt.limit(limit).offset(offset)

      # Ejecución
      result = session.execute(stmt).mappings().all()
      items = [dict(row) for row in result]

      return {"periodo": periodo.value, "total": len(items), "items": items}

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