from collections import defaultdict

from sqlalchemy import func, select

from Config.DatabaseConfig import SessionRolB
from Models.ProcesoLimpiezaModel import FctValorMetrica
from Models.RankingModel import (
    DimDimension,
    DimMetrica,
    VEntidadesCotizacion,
    VRanking,
)


def _ocultar_posiciones(items):
    for item in items:
        item["posicion"] = None
        item["cambioPosicion"] = None


def _ordenar(items, orden, direccion):
    claves = {
        "posicion": lambda item: item["posicion"],
        "entidad": lambda item: item["entidad"].lower(),
        "sector": lambda item: item["sector"].lower(),
        "ic": lambda item: item["ic"],
        "variacionPct": lambda item: item["variacionPct"],
    }
    clave = claves.get(orden, claves["posicion"])

    items.sort(key=lambda item: (item["entidad"].lower(), str(item["entidadId"])))
    items.sort(key=clave, reverse=direccion == "desc")
    return items


def _ranking_general(
    sector, orden, direccion, limit, offset, periodo, ocultar_posicion=False
):
    with SessionRolB() as session:
        fecha_maxima = session.scalar(select(func.max(VRanking.fecha)))
        if fecha_maxima is None:
            return {"periodo": periodo, "total": 0, "items": []}

        fecha_anterior = session.scalar(
            select(func.max(VRanking.fecha)).where(VRanking.fecha < fecha_maxima)
        )

        stmt = (
            select(
                VRanking.id_entidad,
                VRanking.posicion_general.label("posicion"),
                VRanking.ic,
                VEntidadesCotizacion.nombre.label("entidad"),
                VEntidadesCotizacion.sector,
                VEntidadesCotizacion.variacion_pct,
            )
            .join(
                VEntidadesCotizacion,
                VEntidadesCotizacion.id_entidad == VRanking.id_entidad,
            )
            .where(VRanking.fecha == fecha_maxima)
        )

        if sector:
            stmt = stmt.where(VEntidadesCotizacion.sector == sector)

        filas = session.execute(stmt).mappings().all()

        posiciones_anteriores = {}
        if fecha_anterior is not None:
            posiciones_anteriores = {
                id_entidad: posicion
                for id_entidad, posicion in session.execute(
                    select(
                        VRanking.id_entidad,
                        VRanking.posicion_general,
                    ).where(VRanking.fecha == fecha_anterior)
                ).all()
            }

        items = []
        for fila in filas:
            posicion = int(fila["posicion"])
            anterior = posiciones_anteriores.get(fila["id_entidad"])
            items.append(
                {
                    "posicion": posicion,
                    "cambioPosicion": (anterior - posicion) if anterior is not None else 0,
                    "entidadId": fila["id_entidad"],
                    "entidad": fila["entidad"],
                    "sector": fila["sector"],
                    "ic": float(fila["ic"]),
                    "variacionPct": float(fila["variacion_pct"] or 0),
                }
            )

        total = len(items)
        items = _ordenar(items, orden, direccion)

        if ocultar_posicion:
            _ocultar_posiciones(items)

        return {
            "periodo": periodo,
            "total": total,
            "items": items[offset : offset + limit],
        }


def _ranking_dimension(
    dimension, sector, orden, direccion, limit, offset, periodo, ocultar_posicion=False
):
    with SessionRolB() as session:
        periodo_maximo = session.scalar(select(func.max(FctValorMetrica.periodo)))
        if periodo_maximo is None:
            return {"periodo": periodo, "total": 0, "items": []}

        periodo_anterior = session.scalar(
            select(func.max(FctValorMetrica.periodo)).where(
                FctValorMetrica.periodo < periodo_maximo
            )
        )

        periodos = [periodo_maximo]
        if periodo_anterior is not None:
            periodos.append(periodo_anterior)

        stmt = (
            select(
                FctValorMetrica.id_entidad,
                VEntidadesCotizacion.nombre.label("entidad"),
                VEntidadesCotizacion.sector,
                FctValorMetrica.periodo,
                FctValorMetrica.valor_normalizado,
            )
            .join(DimMetrica, DimMetrica.id_metrica == FctValorMetrica.id_metrica)
            .join(
                DimDimension,
                DimDimension.id_dimension == DimMetrica.id_dimension,
            )
            .join(
                VEntidadesCotizacion,
                VEntidadesCotizacion.id_entidad == FctValorMetrica.id_entidad,
            )
            .where(
                FctValorMetrica.periodo.in_(periodos),
                DimDimension.nombre == dimension,
                FctValorMetrica.valor_normalizado.is_not(None),
            )
        )

        datos = defaultdict(
            lambda: {
                "actual": [],
                "anterior": [],
                "entidad": "",
                "sector": "",
            }
        )

        for fila in session.execute(stmt).mappings().all():
            entidad = datos[fila["id_entidad"]]
            entidad["entidad"] = fila["entidad"]
            entidad["sector"] = fila["sector"]

            if fila["periodo"] == periodo_maximo:
                entidad["actual"].append(float(fila["valor_normalizado"]))
            elif fila["periodo"] == periodo_anterior:
                entidad["anterior"].append(float(fila["valor_normalizado"]))

        actuales = {}
        anteriores = {}

        for id_entidad, dato in datos.items():
            if dato["actual"]:
                actuales[id_entidad] = (
                    sum(dato["actual"]) / len(dato["actual"]) * 100
                )
            if dato["anterior"]:
                anteriores[id_entidad] = (
                    sum(dato["anterior"]) / len(dato["anterior"]) * 100
                )

        ranking_actual = {
            id_entidad: posicion
            for posicion, (id_entidad, _) in enumerate(
                sorted(
                    actuales.items(),
                    key=lambda item: (
                        -item[1],
                        datos[item[0]]["entidad"].lower(),
                        str(item[0]),
                    ),
                ),
                start=1,
            )
        }
        ranking_anterior = {
            id_entidad: posicion
            for posicion, (id_entidad, _) in enumerate(
                sorted(
                    anteriores.items(),
                    key=lambda item: (
                        -item[1],
                        datos[item[0]]["entidad"].lower(),
                        str(item[0]),
                    ),
                ),
                start=1,
            )
        }

        items = []
        for id_entidad, valor in actuales.items():
            posicion = ranking_actual[id_entidad]
            posicion_anterior = ranking_anterior.get(id_entidad)

            if posicion_anterior is None:
                cambio_posicion = 0
            else:
                cambio_posicion = posicion_anterior - posicion

            valor_anterior = anteriores.get(id_entidad)
            if valor_anterior in (None, 0):
                variacion_pct = 0.0
            else:
                variacion_pct = (valor - valor_anterior) / valor_anterior * 100

            if sector and datos[id_entidad]["sector"] != sector:
                continue

            items.append(
                {
                    "posicion": posicion,
                    "cambioPosicion": cambio_posicion,
                    "entidadId": id_entidad,
                    "entidad": datos[id_entidad]["entidad"],
                    "sector": datos[id_entidad]["sector"],
                    "ic": round(valor, 3),
                    "variacionPct": round(variacion_pct, 4),
                }
            )

        total = len(items)
        items = _ordenar(items, orden, direccion)

        if ocultar_posicion:
            _ocultar_posiciones(items)

        return {
            "periodo": periodo,
            "total": total,
            "items": items[offset : offset + limit],
        }


def obtener_ranking(
    sector,
    dimension,
    periodo,
    orden,
    direccion,
    limit,
    offset,
    ocultar_posicion=False,
):
    if dimension:
        return _ranking_dimension(
            dimension,
            sector,
            orden,
            direccion,
            limit,
            offset,
            periodo,
            ocultar_posicion,
        )

    return _ranking_general(
        sector,
        orden,
        direccion,
        limit,
        offset,
        periodo,
        ocultar_posicion,
    )