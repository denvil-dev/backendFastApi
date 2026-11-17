from Models.LinajeModel import LinajeCompletoView
from Config.DatabaseConfig import SessionRolB
from uuid import UUID
from Schemas import LinajeSchema
from sqlalchemy import select


 
def obtenerLinaje(id: UUID):
    with SessionRolB() as session:
        stmt = select(LinajeCompletoView).where(LinajeCompletoView.id_valor == id)
        resultado = session.scalars(stmt).first()
        return resultado  # Devuelve el objeto o None automáticamente