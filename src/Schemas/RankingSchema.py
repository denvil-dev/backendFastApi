from enum import Enum
from pydantic import BaseModel


class DimensionEnum(str, Enum):
  rentabilidad = "Rentabilidad"
  liquidez = "Liquidez"
  solvencia = "Solvencia"
  crecimiento = "Crecimiento"


class PeriodoEnum(str, Enum):
  diario = "diario"
  mensual = "mensual"
  trimestral = "trimestral"


class OrdenEnum(str, Enum):
  posicion = "posicion"
  entidad = "entidad"
  sector = "sector"
  ic = "ic"
  variacion_pct = "variacionPct"


class DirEnum(str, Enum):
  asc = "asc"
  desc = "desc"


class RankingItem(BaseModel):
  posicion: int
  cambioPosicion: int  # Positivo = subió, negativo = bajó, 0 = igual
  entidadId: int
  entidad: str
  sector: str
  ic: float
  variacionPct: float


class RankingResponse(BaseModel):
  periodo: str
  total: int
  items: list[RankingItem]