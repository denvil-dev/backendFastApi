from fastapi import APIRouter, HTTPException, status, Depends
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select
from Controller.LinajeController import obtenerLinaje
from Schemas.LinajeSchema import LinajeResponse
linaje = APIRouter()

@linaje.get("/linaje/{id_valor}", response_model=LinajeResponse)
def consultar_linaje(id_valor: UUID):
    linajeDb = obtenerLinaje(id_valor)
    
    # 2. Manejo de error 404 exigido por el Criterio de Aceptación (CA-3)
    if not linajeDb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El linaje para el valor con ID {id_valor} no fue encontrado."
        )
    
    # 3. Transformar la fila plana en la lista de los 6 nodos obligatorios de la HU-BE-10
    nodos = [
        {
            "identificador": str(linajeDb.id_lote),
            "tipo": "Fuente",
            "fecha": linajeDb.fecha_transformacion, # O la fecha de carga del lote
            "proceso": f"Carga del archivo CSV: {linajeDb.archivo_fuente}"
        },
        {
            "identificador": str(linajeDb.id_registro_limpia),
            "tipo": "Staging",
            "fecha": linajeDb.fecha_transformacion,
            "proceso": f"Homologación de entidad: {linajeDb.codigo_entidad} - {linajeDb.nombre_entidad}"
        },
        {
            "identificador": str(linajeDb.id_valor),
            "tipo": "Modelo",
            "fecha": linajeDb.fecha_transformacion,
            "proceso": f"Procesamiento analítico para el periodo {linajeDb.periodo}"
        },
        {
            "identificador": str(linajeDb.id_valor),
            "tipo": "Métrica",
            "fecha": linajeDb.fecha_transformacion,
            "proceso": f"Cálculo de {linajeDb.nombre_metrica} usando fórmula: {linajeDb.transformacion_formula}"
        },
        {
            "identificador": str(linajeDb.id_valor),
            "tipo": "Índice",
            "fecha": linajeDb.fecha_transformacion,
            "proceso": f"Consolidación en sector {linajeDb.sector} (Valor normalizado: {linajeDb.valor_normalizado or 'N/A'})"
        },
        {
            "identificador": str(linajeDb.id_valor),
            "tipo": "Publicación",
            "fecha": linajeDb.fecha_ejecucion_script,
            "proceso": f"Publicado exitosamente (Ejecutado por: {linajeDb.ejecutado_por} bajo script {linajeDb.script_origen})"
        }
    ]
    
    # 4. Retornar la estructura exacta requerida
    return {
        "valor_id": str(linajeDb.id_valor),
        "linaje": nodos
    }