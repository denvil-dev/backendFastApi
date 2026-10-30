from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from Models.RankingModel import Base


class TblDatoFinanciero(Base):
    __tablename__ = "tbl_datos_financieros"
    __table_args__ = {"schema": "limpia"}

    id_dato: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    periodo: Mapped[date] = mapped_column(Date, nullable=False)
    utilidad_neta: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    patrimonio: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    activos_totales: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    pasivo_total: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    activo_corriente: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    pasivo_corriente: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    inventarios: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    ebitda: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    ebit: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    ingresos: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    gastos_financieros: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    fecha_carga: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    id_lote: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    id_entidad: Mapped[UUID] = mapped_column(
        ForeignKey("limpia.tbl_entidades.id_entidad"), nullable=False
    )
    id_registro_origen: Mapped[UUID] = mapped_column(Uuid, nullable=False)


class FctValorMetrica(Base):
    __tablename__ = "fct_valores_metrica"
    __table_args__ = {"schema": "analitica"}

    id_valor: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    periodo: Mapped[date] = mapped_column(Date, nullable=False)
    valor: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 6))
    valor_normalizado: Mapped[Optional[Decimal]] = mapped_column(Numeric(9, 8))
    fecha_carga: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    id_lote: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    id_entidad: Mapped[UUID] = mapped_column(
        ForeignKey("limpia.tbl_entidades.id_entidad"), nullable=False
    )
    id_metrica: Mapped[UUID] = mapped_column(
        ForeignKey("analitica.dim_metrica.id_metrica"), nullable=False
    )
    id_registro_origen: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("limpia.tbl_datos_financieros.id_dato")
    )


class FctIndiceCompetitividad(Base):
    __tablename__ = "fct_indices_competitividad"
    __table_args__ = {"schema": "analitica"}

    id_indice: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    fecha_carga: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ic: Mapped[Decimal] = mapped_column(Numeric(6, 3), nullable=False)
    id_lote: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    id_entidad: Mapped[UUID] = mapped_column(
        ForeignKey("limpia.tbl_entidades.id_entidad"), nullable=False
    )
