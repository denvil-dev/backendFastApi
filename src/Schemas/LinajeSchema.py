from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class TipoNodoEnum(str, Enum):
    """Etapas obligatorias que componen la cadena de linaje."""
    FUENTE = "Fuente"
    STAGING = "Staging"
    MODELO = "Modelo"
    METRICA = "Métrica"
    INDICE = "Índice"
    PUBLICACION = "Publicación"


class NodoLinaje(BaseModel):
    """Representa cada eslabón o nodo dentro de la cadena de trazabilidad."""
    identificador: str = Field(
        ..., 
        description="Identificador único del registro, lote o valor en esta fase."
    )
    tipo: TipoNodoEnum = Field(
        ..., 
        description="Categoría o etapa oficial de la cadena de linaje."
    )
    fecha: datetime = Field(
        ..., 
        description="Marca de tiempo UTC exacta en que ocurrió el proceso en esta fase."
    )
    proceso: str = Field(
        ..., 
        description="Detalle del proceso, script, archivo o fórmula responsable."
    )


class LinajeResponse(BaseModel):
    """Esquema de respuesta final para la API de consulta de linaje."""
    valor_id: str = Field(
        ..., 
        description="Identificador único del valor publicado consultado."
    )
    linaje: List[NodoLinaje] = Field(
        ..., 
        description="Lista estricta con los 6 nodos obligatorios de la cadena de trazabilidad."
    )