import io
from datetime import datetime, timezone
from src.Config.JwtConfig import decode_token
import polars as pl
from Config.DatabaseConfig import SessionLocal
from Models.CsvModel import lotes_carga, ext_matriz_financiera_entidades, auditorias
from sqlalchemy import select, insert
from uuid import uuid4

# Bitácora temporal: se pierde al reiniciar el servidor
bitacora = []


def registrarCsv(id_lote: uuid4, nombreArchivo: str, df: pl.DataFrame):
    filas = df.to_dicts()

    with SessionLocal() as session:
        nuevo_lote = lotes_carga(
            id_lote=id_lote,
            nombre_archivo=nombreArchivo,
            fecha_carga=datetime.now(timezone.utc),
            registros_totales=len(df),
            registros_validos=0,
            id_usuario="7fd06165-38ea-4f89-bcc6-6a146aad670e",
        )

        auditoria = auditorias(
            id_bitacora=uuid4(),
            accion="Subir",
            detalle="Usuario intento subir matriz financiera cruda",
            fecha_evento=datetime.now(timezone.utc),  # <--- Recomendable con UTC
            id_usuario="7fd06165-38ea-4f89-bcc6-6a146aad670e",
        )
        session.add(auditoria)
        session.add(nuevo_lote)
        session.flush()

        for fila in filas:
            fila["id_lote"] = id_lote

        session.execute(
            insert(ext_matriz_financiera_entidades),
            filas,
        )

        session.commit()


def registrar_intento(nombre, resultado, errores=None):
    bitacora.append(
        {
            "fecha": datetime.now(timezone.utc).isoformat(),
            "nombre_archivo": nombre,
            "resultado": resultado,
            "errores": errores or [],
        }
    )


async def procesar_csv(lote_id: uuid4, contenido: bytes, nombre_archivo: str):
    print(nombre_archivo)
    errores = []

    try:
        # Leer el CSV
        try:
            df = pl.read_csv(
                io.BytesIO(contenido),
                separator=";",
                encoding="utf8",
                infer_schema=False,
            )
        except Exception as e:
            errores.append({"tipo": "csv_ilegible", "detalle": str(e)})
            return {"errores": errores, "total_filas": 0, "columnas_detectadas": []}

        # Columnas obligatorias
        # Se usa activo_corriente porque así aparece en tu CSV.
        columnas_requeridas = [
            "codigo_entidad",
            "nombre_entidad",
            "sector",
            "periodo",
            "utilidad_neta",
            "patrimonio",
            "activos_totales",
            "ebitda",
            "ingresos",
            "activo_corriente",
            "inventarios",
            "pasivo_total",
            "ebit",
            "gastos_financieros",
        ]

        faltantes = [c for c in columnas_requeridas if c not in df.columns]

        if faltantes:
            errores.append({"tipo": "columnas_faltantes", "columnas": faltantes})

            return {
                "errores": errores,
                "total_filas": len(df),
                "columnas_detectadas": df.columns,
            }

        # Normalizar espacios en las columnas obligatorias
        df = df.with_columns(
            [
                pl.col(c).cast(pl.String).str.strip_chars().alias(c)
                for c in columnas_requeridas
            ]
        )

        # Validar campos vacíos y nulos
        for columna in columnas_requeridas:
            valores = df[columna]

            vacios = valores.is_null() | (valores == "")

            if vacios.any():
                errores.append(
                    {
                        "columna": columna,
                        "tipo": "valores_vacios",
                        "filas": [
                            i + 2 for i, valor in enumerate(vacios.to_list()) if valor
                        ],
                    }
                )

        # Validar columnas numéricas.
        # Convención asumida: 1.234,56 = mil doscientos treinta y cuatro
        # con cincuenta y seis. Ajustar si el CSV usa otro formato.
        columnas_numericas = [
            "utilidad_neta",
            "patrimonio",
            "activos_totales",
            "ebitda",
            "ingresos",
            "activo_corriente",
            "inventarios",
            "pasivo_total",
            "ebit",
            "gastos_financieros",
        ]

        for columna in columnas_numericas:
            original = df[columna]

            normalizado = original.str.replace_all(
                ".", "", literal=True
            ).str.replace_all(",", ".", literal=True)

            convertido = normalizado.cast(pl.Float64, strict=False)

            invalidos = original.is_not_null() & (original != "") & convertido.is_null()

            if invalidos.any():
                errores.append(
                    {
                        "columna": columna,
                        "tipo": "valores_no_numericos",
                        "filas": [
                            i + 2
                            for i, valor in enumerate(invalidos.to_list())
                            if valor
                        ],
                    }
                )

        # Validar activos_totales > 0
        activos = (
            df["activos_totales"]
            .str.replace_all(".", "", literal=True)
            .str.replace_all(",", ".", literal=True)
            .cast(pl.Float64, strict=False)
        )

        invalidos_activos = (activos.is_null() | (activos <= 0)).fill_null(True)

        if invalidos_activos.any():
            errores.append(
                {
                    "columna": "activos_totales",
                    "tipo": "debe_ser_numerico_y_mayor_que_cero",
                    "filas": [
                        i + 2
                        for i, valor in enumerate(invalidos_activos.to_list())
                        if valor
                    ],
                }
            )

        # Validar código: ENT seguido de tres dígitos
        codigo = df["codigo_entidad"]

        codigo_invalido = (~codigo.str.contains(r"^ENT\d{3}$")).fill_null(True)

        if codigo_invalido.any():
            errores.append(
                {
                    "columna": "codigo_entidad",
                    "tipo": "formato_invalido",
                    "formato_esperado": "ENT seguido de 3 dígitos",
                    "filas": [
                        i + 2
                        for i, valor in enumerate(codigo_invalido.to_list())
                        if valor
                    ],
                }
            )

        # Validar periodo: YYYY/MM y mes entre 01 y 12
        periodo = df["periodo"]

        formato_invalido = (~periodo.str.contains(r"^\d{4}-\d{2}$")).fill_null(True)

        mes = periodo.str.slice(5, 2).cast(pl.Int32, strict=False)

        mes_invalido = (mes.is_null() | (mes < 1) | (mes > 12)).fill_null(True)

        periodo_invalido = formato_invalido | mes_invalido

        if periodo_invalido.any():
            errores.append(
                {
                    "columna": "periodo",
                    "tipo": "formato_invalido",
                    "formato_esperado": "YYYY/MM, por ejemplo 2025/03",
                    "filas": [
                        i + 2
                        for i, valor in enumerate(periodo_invalido.to_list())
                        if valor
                    ],
                }
            )

        # Detectar duplicados por entidad y periodo
        duplicados = df.select(
            pl.struct(["codigo_entidad", "periodo"]).is_duplicated()
        ).to_series()

        if duplicados.any():
            errores.append(
                {
                    "columnas": ["codigo_entidad", "periodo"],
                    "tipo": "registros_duplicados",
                    "filas": [
                        i + 2 for i, valor in enumerate(duplicados.to_list()) if valor
                    ],
                }
            )

        if len(errores) == 0:

            registrarCsv(lote_id, nombre_archivo, df)

        return {
            "errores": errores,
            "total_filas": len(df),
            "columnas_detectadas": df.columns,
        }

    finally:
        # Registrar tanto las cargas correctas como las fallidas
        registrar_intento(
            nombre_archivo, "rechazado" if errores else "exitoso", errores
        )
