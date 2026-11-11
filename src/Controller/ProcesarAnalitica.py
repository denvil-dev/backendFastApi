from collections import defaultdict
from datetime import date, datetime, time, timezone
from decimal import Decimal, InvalidOperation
from uuid import UUID, uuid4

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert

from Config.DatabaseConfig import SessionRolA
from Models.CsvModel import ext_matriz_financiera_entidades, lotes_carga
from Models.ProcesoLimpiezaModel import (
    FctIndiceCompetitividad,
    FctValorMetrica,
    TblDatoFinanciero,
)
from Models.RankingModel import (
    DimDimension,
    DimMetrica,
    FctCotizacion,
    TblEntidad,
    TblSector,
)

CAMPOS_NUMERICOS = (
    "utilidad_neta",
    "patrimonio",
    "activos_totales",
    "pasivo_total",
    "activo_corriente",
    "pasivo_corriente",
    "inventarios",
    "ebitda",
    "ebit",
    "ingresos",
    "gastos_financieros",
)

METRICAS_FINANCIERAS = (
    "RNT-01",
    "RNT-02",
    "RNT-03",
    "LIQ-01",
    "LIQ-02",
    "END-01",
    "END-02",
    "CRE-01",
)


def _parsear_decimal(valor):
    if valor is None:
        return None

    texto = str(valor).strip()
    if not texto:
        return None

    if "," in texto and "." in texto:
        texto = texto.replace(".", "").replace(",", ".")
    elif "," in texto:
        texto = texto.replace(",", ".")

    try:
        return Decimal(texto)
    except (InvalidOperation, ValueError):
        return None


def _parsear_periodo(valor):
    anio, mes = str(valor).strip().split("-")
    return date(int(anio), int(mes), 1)


def _dividir(numerador, denominador):
    if numerador is None or denominador is None or denominador == 0:
        return None
    return numerador / denominador


def _redondear(valor, decimales):
    if valor is None:
        return None
    return valor.quantize(Decimal(1).scaleb(-decimales))


def _normalizar(registros, codigo):
    por_periodo = defaultdict(list)

    for registro in registros:
        valor = registro["valores"].get(codigo)
        if valor is not None:
            por_periodo[registro["periodo"]].append((registro, valor))

    for items in por_periodo.values():
        valores = [valor for _, valor in items]
        minimo = min(valores)
        maximo = max(valores)

        for registro, valor in items:
            if maximo == minimo:
                registro["normalizados"][codigo] = Decimal("0.5")
            else:
                registro["normalizados"][codigo] = (valor - minimo) / (
                    maximo - minimo
                )


def _cargar_sectores(session, registros):
    sectores = {
        sector.nombre: sector
        for sector in session.execute(select(TblSector)).scalars().all()
    }

    for nombre in sorted({registro["sector"] for registro in registros}):
        if nombre not in sectores:
            sector = TblSector(id_sector=uuid4(), nombre=nombre)
            session.add(sector)
            sectores[nombre] = sector

    session.flush()
    return sectores


def _cargar_entidades(session, registros, sectores):
    entidades = {
        entidad.ticker: entidad
        for entidad in session.execute(select(TblEntidad)).scalars().all()
    }

    for registro in registros:
        sector = sectores[registro["sector"]]
        entidad = entidades.get(registro["ticker"])

        if entidad is None:
            entidad = TblEntidad(
                id_entidad=uuid4(),
                ticker=registro["ticker"],
                nombre=registro["nombre"],
                id_sector=sector.id_sector,
            )
            session.add(entidad)
            entidades[registro["ticker"]] = entidad
        else:
            entidad.nombre = registro["nombre"]
            entidad.id_sector = sector.id_sector

    session.flush()
    return entidades


def _cargar_datos_financieros(session, lote_id, registros, entidades):
    existentes = {
        (dato.id_entidad, dato.periodo): dato
        for dato in session.execute(
            select(TblDatoFinanciero).where(
                TblDatoFinanciero.id_entidad.in_(
                    [entidad.id_entidad for entidad in entidades.values()]
                )
            )
        )
        .scalars()
        .all()
    }

    ahora = datetime.now(timezone.utc)

    for registro in registros:
        entidad = entidades[registro["ticker"]]
        llave = (entidad.id_entidad, registro["periodo"])
        dato = existentes.get(llave)

        if dato is None:
            dato = TblDatoFinanciero(
                id_dato=uuid4(),
                periodo=registro["periodo"],
                fecha_carga=ahora,
                id_lote=lote_id,
                id_entidad=entidad.id_entidad,
                id_registro_origen=registro["id_cruda"],
            )
            session.add(dato)
            existentes[llave] = dato
        else:
            dato.fecha_carga = ahora
            dato.id_lote = lote_id
            dato.id_registro_origen = registro["id_cruda"]

        for campo in CAMPOS_NUMERICOS:
            setattr(dato, campo, registro[campo])

        registro["id_dato"] = dato.id_dato
        registro["id_entidad"] = entidad.id_entidad

    session.flush()
    return existentes


def _calcular_metricas(session, registros):
    metricas = {
        metrica.codigo: metrica
        for metrica in session.execute(select(DimMetrica)).scalars().all()
    }
    dimensiones = {
        dimension.id_dimension: dimension
        for dimension in session.execute(select(DimDimension)).scalars().all()
    }

    por_entidad = defaultdict(list)
    for registro in registros:
        por_entidad[registro["id_entidad"]].append(registro)

    for entidad_registros in por_entidad.values():
        entidad_registros.sort(key=lambda item: item["periodo"])
        ingresos_anteriores = None

        for registro in entidad_registros:
            ingresos = registro["ingresos"]
            registro["valores"] = {
                "RNT-01": _dividir(registro["utilidad_neta"], registro["patrimonio"]),
                "RNT-02": _dividir(
                    registro["utilidad_neta"], registro["activos_totales"]
                ),
                "RNT-03": _dividir(registro["ebitda"], registro["ingresos"]),
                "LIQ-01": _dividir(
                    registro["activo_corriente"], registro["pasivo_corriente"]
                ),
                "LIQ-02": _dividir(
                    (
                        registro["activo_corriente"] - registro["inventarios"]
                        if registro["activo_corriente"] is not None
                        and registro["inventarios"] is not None
                        else None
                    ),
                    registro["pasivo_corriente"],
                ),
                "END-01": _dividir(
                    registro["pasivo_total"], registro["activos_totales"]
                ),
                "END-02": _dividir(
                    registro["ebit"], registro["gastos_financieros"]
                ),
                "CRE-01": _dividir(
                    (
                        ingresos - ingresos_anteriores
                        if ingresos is not None and ingresos_anteriores is not None
                        else None
                    ),
                    ingresos_anteriores,
                ),
            }
            registro["normalizados"] = {}
            ingresos_anteriores = ingresos

    for codigo in METRICAS_FINANCIERAS:
        _normalizar(registros, codigo)

    pesos_dimension = {
        dimension.nombre: Decimal(str(dimension.peso_ic))
        for dimension in dimensiones.values()
    }
    metricas_por_dimension = defaultdict(list)

    for codigo in METRICAS_FINANCIERAS:
        metrica = metricas.get(codigo)
        if metrica is not None:
            metricas_por_dimension[dimensiones[metrica.id_dimension].nombre].append(
                codigo
            )

    for registro in registros:
        peso_total = Decimal("0")
        ponderado = Decimal("0")

        for dimension, codigos in metricas_por_dimension.items():
            valores = [
                registro["normalizados"].get(codigo)
                for codigo in codigos
                if registro["normalizados"].get(codigo) is not None
            ]
            if not valores:
                continue

            peso = pesos_dimension.get(dimension, Decimal("0"))
            promedio = sum(valores) / Decimal(len(valores))
            ponderado += peso * promedio
            peso_total += peso

        if peso_total > 0:
            registro["ic"] = min(
                Decimal("100"),
                max(Decimal("0"), (ponderado / peso_total) * Decimal("100")),
            )
        else:
            registro["ic"] = None

    for entidad_registros in por_entidad.values():
        entidad_registros.sort(key=lambda item: item["periodo"])
        ic_anterior = None

        for registro in entidad_registros:
            ic = registro["ic"]
            registro["valores"]["CRE-02"] = _dividir(
                (ic - ic_anterior if ic is not None and ic_anterior is not None else None),
                ic_anterior,
            )
            registro["normalizados"]["CRE-02"] = None
            ic_anterior = ic if ic is not None else ic_anterior

    _normalizar(registros, "CRE-02")
    return metricas


def _guardar_metricas(session, lote_id, registros, metricas):
    ahora = datetime.now(timezone.utc)
    filas = []

    for registro in registros:
        for codigo in (*METRICAS_FINANCIERAS, "CRE-02"):
            metrica = metricas.get(codigo)
            if metrica is None:
                continue

            filas.append(
                {
                    "id_valor": uuid4(),
                    "periodo": registro["periodo"],
                    "valor": _redondear(registro["valores"].get(codigo), 6),
                    "valor_normalizado": _redondear(
                        registro["normalizados"].get(codigo), 8
                    ),
                    "fecha_carga": ahora,
                    "id_lote": lote_id,
                    "id_entidad": registro["id_entidad"],
                    "id_metrica": metrica.id_metrica,
                    "id_registro_origen": registro["id_dato"],
                }
            )

    if not filas:
        return

    sentencia = insert(FctValorMetrica).values(filas)
    sentencia = sentencia.on_conflict_do_update(
        index_elements=[
            FctValorMetrica.id_entidad,
            FctValorMetrica.id_metrica,
            FctValorMetrica.periodo,
        ],
        set_={
            "valor": sentencia.excluded.valor,
            "valor_normalizado": sentencia.excluded.valor_normalizado,
            "fecha_carga": sentencia.excluded.fecha_carga,
            "id_lote": sentencia.excluded.id_lote,
            "id_registro_origen": sentencia.excluded.id_registro_origen,
        },
    )
    session.execute(sentencia)


def _guardar_cotizaciones(session, registros):
    ahora = datetime.now(timezone.utc)
    por_entidad = defaultdict(list)

    for registro in registros:
        if registro["ic"] is not None:
            por_entidad[registro["id_entidad"]].append(registro)

    filas = []

    for entidad_registros in por_entidad.values():
        entidad_registros.sort(key=lambda item: item["periodo"])
        cierre_anterior = None

        for registro in entidad_registros:
            cierre = _redondear(registro["ic"], 3)
            variacion_pct = None

            if cierre_anterior not in (None, Decimal("0")):
                variacion_pct = _redondear(
                    (cierre - cierre_anterior) / cierre_anterior * Decimal("100"), 4
                )

            filas.append(
                {
                    "id_cotizacion": uuid4(),
                    "fecha": datetime.combine(registro["periodo"], time.min),
                    "apertura": cierre,
                    "maximo": cierre,
                    "minimo": cierre,
                    "cierre": cierre,
                    "variacion_pct": variacion_pct,
                    "volumen_actualizaciones": 1,
                    "fecha_carga": ahora,
                    "id_entidad": registro["id_entidad"],
                }
            )
            cierre_anterior = cierre

    if not filas:
        return

    sentencia = insert(FctCotizacion).values(filas)
    sentencia = sentencia.on_conflict_do_update(
        index_elements=[FctCotizacion.id_entidad, FctCotizacion.fecha],
        set_={
            "apertura": sentencia.excluded.apertura,
            "maximo": sentencia.excluded.maximo,
            "minimo": sentencia.excluded.minimo,
            "cierre": sentencia.excluded.cierre,
            "variacion_pct": sentencia.excluded.variacion_pct,
            "volumen_actualizaciones": sentencia.excluded.volumen_actualizaciones,
            "fecha_carga": sentencia.excluded.fecha_carga,
        },
    )
    session.execute(sentencia)


def _guardar_indices(session, lote_id, registros):
    ahora = datetime.now(timezone.utc)
    ultimos = {}

    for registro in registros:
        if registro["ic"] is None:
            continue

        actual = ultimos.get(registro["id_entidad"])
        if actual is None or registro["periodo"] > actual["periodo"]:
            ultimos[registro["id_entidad"]] = registro

    filas = [
        {
            "id_indice": uuid4(),
            "fecha_carga": ahora,
            "ic": _redondear(registro["ic"], 3),
            "id_lote": lote_id,
            "id_entidad": registro["id_entidad"],
        }
        for registro in ultimos.values()
    ]

    if not filas:
        return

    sentencia = insert(FctIndiceCompetitividad).values(filas)
    sentencia = sentencia.on_conflict_do_update(
        index_elements=[
            FctIndiceCompetitividad.id_entidad,
            FctIndiceCompetitividad.id_lote,
        ],
        set_={
            "ic": sentencia.excluded.ic,
            "fecha_carga": sentencia.excluded.fecha_carga,
        },
    )
    session.execute(sentencia)


def procesar_analitica(id_lote):
    lote_id = UUID(str(id_lote))

    with SessionRolA() as session:
        try:
            crudos = (
                session.execute(
                    select(ext_matriz_financiera_entidades).where(
                        ext_matriz_financiera_entidades.id_lote == lote_id
                    )
                )
                .scalars()
                .all()
            )

            registros = []
            for crudo in crudos:
                if not crudo.codigo_entidad or not crudo.sector or not crudo.periodo:
                    continue

                registro = {
                    "id_cruda": crudo.id_cruda,
                    "ticker": crudo.codigo_entidad.strip().upper(),
                    "nombre": (crudo.nombre_entidad or crudo.codigo_entidad).strip(),
                    "sector": crudo.sector.strip(),
                    "periodo": _parsear_periodo(crudo.periodo),
                }

                for campo in CAMPOS_NUMERICOS:
                    registro[campo] = _parsear_decimal(getattr(crudo, campo))

                registros.append(registro)

            if not registros:
                return {"entidades": 0, "datos": 0, "metricas": 0, "cotizaciones": 0}

            sectores = _cargar_sectores(session, registros)
            entidades = _cargar_entidades(session, registros, sectores)
            _cargar_datos_financieros(session, lote_id, registros, entidades)
            metricas = _calcular_metricas(session, registros)
            _guardar_metricas(session, lote_id, registros, metricas)
            _guardar_cotizaciones(session, registros)
            _guardar_indices(session, lote_id, registros)

            session.execute(
                update(lotes_carga)
                .where(lotes_carga.id_lote == lote_id)
                .values(registros_validos=len(registros))
            )

            session.commit()

            return {
                "entidades": len(entidades),
                "datos": len(registros),
                "metricas": len(registros) * (len(METRICAS_FINANCIERAS) + 1),
                "cotizaciones": len(registros),
            }
        except Exception:
            session.rollback()
            raise
