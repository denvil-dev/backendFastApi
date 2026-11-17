from datetime import datetime
from uuid import UUID, uuid4

from Config.DatabaseConfig import SessionRolB
from Models.AuditModel import auditorias
from Schemas.AuditSchema import AuditSchema
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError


def registrarBitacora(audit_data: AuditSchema) -> None:
    """Guarda un evento nuevo en la tabla de auditoría de la base local."""
    with SessionRolB() as session_backend:
        id_bitacora = uuid4()
        auditoria = auditorias(
            id_bitacora=id_bitacora,
            accion=audit_data.accion,
            detalle=audit_data.detalle,
            fecha_evento=audit_data.fecha_evento,
            id_usuario=audit_data.id_usuario,
        )
        session_backend.add(auditoria)
        try:
            session_backend.commit()
        except IntegrityError as error:
            session_backend.rollback()
            if (
                audit_data.id_usuario is None
                or getattr(error.orig, "sqlstate", None) != "23503"
            ):
                raise

            detalle_anonimo = audit_data.detalle
            if "anonimo" not in detalle_anonimo.lower():
                marcador = "; actor=anonimo"
                detalle_anonimo = (
                    f"{detalle_anonimo[:250 - len(marcador)]}{marcador}"
                )
            auditoria_anonima = auditorias(
                id_bitacora=id_bitacora,
                accion=audit_data.accion,
                detalle=detalle_anonimo,
                fecha_evento=audit_data.fecha_evento,
                id_usuario=None,
            )
            session_backend.add(auditoria_anonima)
            session_backend.commit()


def consultarBitacora(
    *,
    id_usuario: UUID | None = None,
    accion: str | None = None,
    recurso: str | None = None,
    ip: str | None = None,
    fecha_desde: datetime | None = None,
    fecha_hasta: datetime | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict:
    """Consulta eventos aplicando filtros y paginación, sin modificar registros."""
    filtros = []
    if id_usuario is not None:
        filtros.append(auditorias.id_usuario == id_usuario)
    if accion:
        filtros.append(auditorias.accion == accion)
    if recurso:
        filtros.append(auditorias.detalle.contains(f"recurso={recurso}", autoescape=True))
    if ip:
        filtros.append(auditorias.detalle.contains(f"ip={ip}", autoescape=True))
    if fecha_desde is not None:
        filtros.append(auditorias.fecha_evento >= fecha_desde)
    if fecha_hasta is not None:
        filtros.append(auditorias.fecha_evento <= fecha_hasta)

    with SessionRolB() as session_backend:
        consulta = select(auditorias).where(*filtros)
        total = session_backend.scalar(
            select(func.count()).select_from(auditorias).where(*filtros)
        )
        resultados = session_backend.scalars(
            consulta.order_by(auditorias.fecha_evento.desc())
            .limit(limit)
            .offset(offset)
        ).all()

    return {
        "items": [
            {
                "id_bitacora": registro.id_bitacora,
                "accion": registro.accion,
                "detalle": registro.detalle,
                "fecha_evento": registro.fecha_evento,
                "id_usuario": registro.id_usuario,
            }
            for registro in resultados
        ],
        "total": total or 0,
        "limit": limit,
        "offset": offset,
    }
