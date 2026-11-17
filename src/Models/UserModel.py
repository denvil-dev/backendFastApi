from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Boolean, Uuid,DateTime, Numeric, Text
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID
    
class Base(DeclarativeBase):
    pass
class usuarios(Base):
    __tablename__ = "usuarios"
    __table_args__ = {"schema": "seguridad"}
    id_usuario: Mapped[UUID] = mapped_column(Uuid, primary_key=True, nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    primer_nombre: Mapped[str] = mapped_column(String(30), nullable=False)
    segundo_nombre: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    primer_apellido: Mapped[str] = mapped_column(String(30), nullable=False)
    segundo_apellido: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(100), nullable=False)
    estado: Mapped[str] = mapped_column(String(10), nullable=False, default=True)
    contraseña: Mapped[str] = mapped_column(String(255), nullable=False)
    id_rol: Mapped[UUID] = mapped_column (Uuid, nullable=False)
