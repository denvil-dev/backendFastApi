from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from Controller.LeerCsv import procesar_csv
from Config.JwtConfig import decode_token, verificar_rol
from pathlib import Path
from uuid import uuid4

csv = APIRouter()


@csv.post("/v1/validar-matriz")
async def validar_matriz(rol: str = Depends(verificar_rol), file: UploadFile = File(...)):
    id_usuario = rol["sub"]
    print (id_usuario)
    lote_id = str(uuid4())

    # 1. Validar extensión
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Este archivo no es un CSV.")

    # 2. Validar tipo MIME
    tipos_permitidos = ["text/csv", "text/plain", "application/vnd.ms-excel"]

    if file.content_type not in tipos_permitidos:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de contenido no permitido: {file.content_type}",
        )

    try:
        # 3. Leer el archivo una sola vez
        contenido_bytes = await file.read()

        if not contenido_bytes:
            raise HTTPException(status_code=400, detail="El archivo CSV está vacío.")

        # 4. Delegar el procesamiento al controlador
        resultado = await procesar_csv(id_usuario,lote_id, contenido_bytes, file.filename)

        if resultado["errores"]:
            raise HTTPException(
                status_code=422,
                detail={
                    "mensaje": "El CSV contiene errores de validación",
                    "errores": resultado["errores"],
                },
            )
        
        # 5 Guardar el csv valido
        carpeta = Path("src/Csv/Crudos")
        carpeta.mkdir(parents=True, exist_ok=True)
        ruta_archivo = carpeta / f"{lote_id}.csv"
        ruta_archivo.write_bytes(contenido_bytes)

        return {
            "mensaje": "CSV procesado correctamente",
            "lote": lote_id,
            "nombre_archivo": file.file,
            "ruta": str(ruta_archivo),
            "total_filas": resultado["total_filas"],
            "columnas_detectadas": resultado["columnas_detectadas"],
            "validacion": "correcta",
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Error al procesar el CSV: {str(e)}"
        )

    finally:
        await file.close()
