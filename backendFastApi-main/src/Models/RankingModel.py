from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, Uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
  pass


# ==========================================
# ESQUEMA: limpia
# ==========================================
class TblSector(Base):
  __tablename__ = "tbl_sectores"
  __table_args__ = {"schema": "limpia"}

  id_sector: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
  nombre: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)

  # Relación inversa opcional
  entidades: Mapped[list["TblEntidad"]] = relationship(
      back_populates="sector_rel"
  )


class TblEntidad(Base):
  __tablename__ = "tbl_entidades"
  __table_args__ = {"schema": "limpia"}

  id_entidad: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
  ticker: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
  nombre: Mapped[str] = mapped_column(String(80), nullable=False)
  id_sector: Mapped[UUID] = mapped_column(
      ForeignKey("limpia.tbl_sectores.id_sector"), nullable=False
  )

  # Relación
  sector_rel: Mapped["TblSector"] = relationship(back_populates="entidades")


# ==========================================
# ESQUEMA: analitica (Dimensiones y Métricas)
# ==========================================
class DimDimension(Base):
  __tablename__ = "dim_dimension"
  __table_args__ = {"schema": "analitica"}

  id_dimension: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
  nombre: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
  peso_ic: Mapped[Decimal] = mapped_column(
      Numeric(precision=4, scale=3), nullable=False, default=0
  )


class DimMetrica(Base):
  __tablename__ = "dim_metrica"
  __table_args__ = {"schema": "analitica"}

  id_metrica: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
  codigo: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
  nombre: Mapped[str] = mapped_column(String(50), nullable=False)
  formula: Mapped[str] = mapped_column(String(120), nullable=False)
  frecuencia: Mapped[str] = mapped_column(String(12), nullable=False)
  id_dimension: Mapped[UUID] = mapped_column(
      ForeignKey("analitica.dim_dimension.id_dimension"), nullable=False
  )


# ==========================================
# ESQUEMA: analitica (Cotizaciones y Ranking)
# ==========================================
class FctCotizacion(Base):
  __tablename__ = "fct_cotizaciones"
  __table_args__ = {"schema": "analitica"}

  id_cotizacion: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
  fecha: Mapped[datetime] = mapped_column(DateTime, nullable=False)  # o Date
  apertura: Mapped[Decimal] = mapped_column(Numeric(6, 3), nullable=False)
  maximo: Mapped[Decimal] = mapped_column(Numeric(6, 3), nullable=False)
  minimo: Mapped[Decimal] = mapped_column(Numeric(6, 3), nullable=False)
  cierre: Mapped[Decimal] = mapped_column(Numeric(6, 3), nullable=False)
  variacion_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 4))
  volumen_actualizaciones: Mapped[int] = mapped_column(
      Integer, nullable=False, default=0
  )
  fecha_carga: Mapped[datetime] = mapped_column(
      DateTime, nullable=False, default=datetime.utcnow
  )
  id_entidad: Mapped[UUID] = mapped_column(
      ForeignKey("limpia.tbl_entidades.id_entidad"), nullable=False
  )




class VEntidadesCotizacion(Base):
  __tablename__ = "v_entidades_cotizacion"
  __table_args__ = {"schema": "analitica"}

  id_entidad: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
  ticker: Mapped[str] = mapped_column(String(10))
  nombre: Mapped[str] = mapped_column(String(80))
  sector: Mapped[str] = mapped_column(String(30))
  fecha: Mapped[Optional[datetime]] = mapped_column(DateTime)
  ic: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 3))
  variacion: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 3))
  variacion_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 4))


# Mapeo de la vista analitica.v_ranking
class VRanking(Base):
  __tablename__ = "v_ranking"
  __table_args__ = {"schema": "analitica"}

  fecha: Mapped[datetime] = mapped_column(DateTime, primary_key=True)
  id_entidad: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
  ticker: Mapped[str] = mapped_column(String(10))
  id_sector: Mapped[UUID] = mapped_column(Uuid)
  ic: Mapped[Decimal] = mapped_column(Numeric(6, 3))
  posicion_general: Mapped[int] = mapped_column(Integer)
  posicion_sector: Mapped[int] = mapped_column(Integer)