import jwt
import os
from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import datetime
from uuid import uuid4

load_dotenv()

ALGORITHM = os.getenv("ALGORITHM")
SECRET_KEY = os.getenv("SECRET_KEY")
EXP_TIME = os.getenv("EXP_TIME")

security = HTTPBearer()
ROLE_CLAIM = "http://schemas.microsoft.com/ws/2008/06/identity/claims/role"


def createToken():
    ahora = datetime.datetime.now(datetime.timezone.utc)
    tiempo_expiracion = ahora + datetime.timedelta(hours=24)  # Por ejemplo, 24 horas

    # Este es el payload que irá dentro del JWT
    payload = {
        "sub": "98c097d9-a661-4c29-ae77-b7a41945548a",
        "email": "admin@siftc.local",
        "name": "Admin SIFTC",
        "http://schemas.microsoft.com/ws/2008/06/identity/claims/role": (
            "Administrador"
        ),
        "jti": str(uuid4()),  # Genera un ID único para este token
        "exp": tiempo_expiracion,
        "iss": "SIFTC.Backend",
        "aud": "SIFTC.Clients",
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    # Lo que devuelves a tu cliente/frontend
    return {
        "token": token,
        "expiraEn": int(
            (tiempo_expiracion - ahora).total_seconds()
        ),  # Segundos de vida
        "usuario": {
            "id": payload["sub"],
            "nombre": payload["name"],
            "email": payload["email"],
            "rol": payload[
                "http://schemas.microsoft.com/ws/2008/06/identity/claims/role"
            ],
        },
    }


def decode_token(credenciales: HTTPAuthorizationCredentials = Depends(security)):
    token = credenciales.credentials

    try:
        return jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            issuer="SIFTC.Backend",
            audience="SIFTC.Clients",
        )

    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")

def decode(token: str):
    """
    Función exclusiva para auditoría: Lee el payload incluso si el token está expirado 
    o si fallan las validaciones estrictas de issuer/audience.
    """
    try:
        # Intentamos decodificar verificando la firma pero omitiendo issuer/audience estrictos si es necesario
        return jwt.decode(
            token, 
            SECRET_KEY, 
            algorithms=[ALGORITHM],
            options={"verify_iss": False, "verify_aud": False}
        )
    except jwt.ExpiredSignatureError:
        # Si expiró, usamos verify_signature=False para al menos rescatar el nombre del usuario en el log
        try:
            return jwt.decode(token, options={"verify_signature": False})
        except Exception:
            raise Exception("Token malformado o expirado")
    except jwt.InvalidTokenError:
        # Si la firma no coincide o es inválido, intentamos leer los datos sin verificar firma para el log
        try:
            return jwt.decode(token, options={"verify_signature": False})
        except Exception:
            raise Exception("Token inválido")

def detokinizador(
    token: str,
):  # Cambiado a str, ya que jwt.decode espera el string del token
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="El token ha expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")


ROLES_PERMITIDOS = {
    "Analista financiero",
    "AnalistaFinanciero",
    "Administrador",
}


def verificar_rol(payload: dict = Depends(decode_token)):
    rol = payload.get(ROLE_CLAIM)
    if rol not in ROLES_PERMITIDOS:
        raise HTTPException(
            status_code=403, detail="No eres analista, no puedes hacer esto "
        )
    return payload


#token= createToken()
#print (token)  # Llamada a la función para generar el token al iniciar la aplicación