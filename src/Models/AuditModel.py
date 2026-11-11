from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Boolean, Uuid,DateTime, Numeric, Text
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

class Base(DeclarativeBase):
    pass
class auditorias(Base):
    __tablename__ = "auditorias"
    __table_args__ = {"schema": "seguridad"}
    id_bitacora: Mapped[UUID] = mapped_column(Uuid, primary_key=True, nullable=False)
    accion : Mapped[str] = mapped_column(String(40), nullable=False)
    detalle: Mapped[str] = mapped_column(String (250), nullable=False)
    fecha_evento: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )   
    id_usuario: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
