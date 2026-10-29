import jwt
import os
from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

load_dotenv()

ALGORITHM = os.getenv("ALGORITHM")
SECRET_KEY = os.getenv("SECRET_KEY")
EXP_TIME = os.getenv("EXP_TIME")

security = HTTPBearer()
ROLE_CLAIM = "http://schemas.microsoft.com/ws/2008/06/identity/claims/role"


def createToken():
    token = jwt.encode(
        {
            "usuario": "usuario",
            "http://schemas.microsoft.com/ws/2008/06/identity/claims/role": "AnalistaFinanciero",
        },
        SECRET_KEY,
        algorithm="HS256",
    )
    
    return token


def decode_token(credenciales: HTTPAuthorizationCredentials = Depends(security)):
    token = credenciales.credentials

    try:
        return jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            ##issuer="SIFTC.Backend",
            ##audience="SIFTC.Clients"
        )

    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")


def verificar_rol(payload: dict = Depends(decode_token)):
    rol = payload.get(ROLE_CLAIM)
    if rol != "AnalistaFinanciero":
        raise HTTPException(
            status_code=403, detail="No eres analista, no puedes hacer esto "
        )


createToken()
