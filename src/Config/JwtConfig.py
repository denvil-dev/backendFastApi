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
            audience="SIFTC.Clients"
        )

    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")


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
    
def verificar_rol(payload: dict = Depends(decode_token)):
    rol = payload.get(ROLE_CLAIM)
    if rol != "AnalistaFinanciero" and rol != "Administrador":
        raise HTTPException(
            status_code=403, detail="No eres analista, no puedes hacer esto "
        )
    return payload

resultado = createToken()
token  = resultado ["token"]
print (token)
 