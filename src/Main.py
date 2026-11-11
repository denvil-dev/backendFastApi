import logging
import os
import sys
from datetime import datetime, timezone
from uuid import UUID

from fastapi import FastAPI, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.security import HTTPAuthorizationCredentials

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.Routes.LeerCsvRoute import csv
from src.Routes.RankingRoute import ranking
from src.Routes.AuditRoute import audit
from Config.JwtConfig import decode_token
from Controller.Bitacora import registrarBitacora
from Schemas.AuditSchema import AuditSchema

logger = logging.getLogger(__name__)

app = FastAPI()


app.include_router(csv)
app.include_router(ranking)
app.include_router(audit)


@app.middleware("http")
async def auditoria_middleware(request: Request, call_next):
    """Registra en la bitácora toda solicitud HTTP que atraviesa la aplicación."""
    usuario_id: UUID | None = None
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials=auth_header.removeprefix("Bearer ").strip()
        )
        try:
            info = decode_token(credentials)
            request.state.user = info
            usuario_id = UUID(str(info["sub"]))
        except HTTPException:
            logger.info("Solicitud con token inválido registrada como anónima")
        except (TypeError, ValueError, KeyError):
            logger.warning("Token válido sin un identificador de usuario UUID")

    ip_cliente = request.client.host if request.client else "desconocida"

    async def registrar_evento(status_code: int) -> bool:
        """Construye y persiste el evento sin guardar el cuerpo de la solicitud."""
        try:
            actor = "anonimo; " if usuario_id is None else ""
            ip_registro = ip_cliente[:45]
            detalle_base = f"; {actor}ip={ip_registro}; estado={status_code}"
            recurso_maximo = max(0, 250 - len("recurso=") - len(detalle_base))
            detalle = f"recurso={request.url.path[:recurso_maximo]}{detalle_base}"
            auditoria = AuditSchema(
                accion=request.method[:40],
                detalle=detalle,
                id_usuario=usuario_id,
                fecha_evento=datetime.now(timezone.utc),
            )
            await run_in_threadpool(registrarBitacora, auditoria)
            return True
        except Exception:
            logger.exception("No se pudo registrar la solicitud en bitácora")
            return False

    try:
        response = await call_next(request)
    except Exception:
        await registrar_evento(500)
        raise

    registrado = await registrar_evento(response.status_code)
    response.headers["X-Audit-Status"] = "Registrado" if registrado else "Error"
    return response


@app.get("/")
async def root():
    return "hola"