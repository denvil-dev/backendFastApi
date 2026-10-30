from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Boolean, Uuid,DateTime, Numeric, Text
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID
class Base(DeclarativeBase):
    pass

class lotes_carga(Base):
    __tablename__ = "lotes_carga"
    __table_args__ = {"schema": "cruda"}
    id_lote: Mapped[str] = mapped_column(Uuid, primary_key=True, nullable=False)
    nombre_archivo : Mapped[str] = mapped_column(String, nullable=False)
    fecha_carga: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    registros_totales: Mapped[int]= mapped_column(Integer, nullable=False)
    registros_validos: Mapped[int] = mapped_column(Integer, nullable=False)
    id_usuario: Mapped[Optional[str]] = mapped_column (Uuid, nullable=False)
class auditorias(Base):
    __tablename__ = "auditorias"
    __table_args__ = {"schema": "seguridad"}
    id_bitacora: Mapped[UUID] = mapped_column(Uuid, primary_key=True, nullable=False)
    accion : Mapped[str] = mapped_column(String(40), nullable=False)
    detalle: Mapped[str] = mapped_column(String (250), nullable=False)
    fecha_evento: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )   
    id_usuario: Mapped[UUID] = mapped_column (Uuid, nullable=False)

class ext_matriz_financiera_entidades(Base):
    __tablename__ = "ext_matriz_financiera_entidades"
    __table_args__ = {"schema": "cruda"}
    id_cruda: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    id_lote: Mapped[Optional[UUID]] = mapped_column(Uuid, nullable=True)

    # Datos de identificación y métricas (todas tipo Text)
    codigo_entidad: Mapped[str] = mapped_column(Text, nullable=False)
    nombre_entidad: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sector: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    periodo: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    utilidad_neta: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    patrimonio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    activos_totales: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ebitda: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ingresos: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    activo_corriente: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    pasivo_corriente: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    inventarios: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    pasivo_total: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ebit: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    gastos_financieros: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Auditoría / Control de carga (Timestamp)
    fecha_carga: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )


