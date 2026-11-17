from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Uuid, DateTime, Numeric, Text, Date
from datetime import datetime, date
from decimal import Decimal
from typing import Optional
from uuid import UUID

class Base(DeclarativeBase):
    pass

class LinajeCompletoView(Base):
    __tablename__ = "vw_linaje_completo"
    __table_args__ = {"schema": "analitica"}

    id_valor: Mapped[UUID] = mapped_column(Uuid, primary_key=True, nullable=False)
    codigo_entidad: Mapped[str] = mapped_column(String(50), nullable=False)
    nombre_entidad: Mapped[str] = mapped_column(String(150), nullable=False)
    sector: Mapped[str] = mapped_column(String(100), nullable=False)
    periodo: Mapped[date] = mapped_column(Date, nullable=False)
    codigo_metrica: Mapped[str] = mapped_column(String(50), nullable=False)
    nombre_metrica: Mapped[str] = mapped_column(String(150), nullable=False)
    valor_publicado: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    valor_normalizado: Mapped[Optional[Decimal]] = mapped_column(Numeric, nullable=True)
    archivo_fuente: Mapped[str] = mapped_column(String(255), nullable=False)
    id_lote: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    id_registro_cruda: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    id_registro_limpia: Mapped[int] = mapped_column(Integer, nullable=False)  # Ajustable a Uuid si la tabla limpia usa UUID
    transformacion_formula: Mapped[str] = mapped_column(Text, nullable=False)
    version_script: Mapped[str] = mapped_column(String(20), nullable=False)
    fecha_transformacion: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    ejecutado_por: Mapped[str] = mapped_column(String(100), nullable=False)
    fecha_ejecucion_script: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    script_origen: Mapped[str] = mapped_column(String(100), nullable=False)