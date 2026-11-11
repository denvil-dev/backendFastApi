import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Obtener la ruta absoluta del archivo actual y calcular la raíz del proyecto.
BASE_DIR = Path(__file__).resolve().parent.parent.parent
env_path = BASE_DIR / ".env"

# Cargar las variables desde el archivo .env del proyecto.
load_dotenv(dotenv_path=env_path)

# Leer las conexiones locales usadas por los roles de la aplicación.
DATABASE_URL_A = os.getenv("DATABASE_URL_A")
DATABASE_URL_B = os.getenv("DATABASE_URL_B")

if not DATABASE_URL_A:
    raise ValueError(f"No se encontró DATABASE_URL_A en: {env_path}")
if not DATABASE_URL_B:
    raise ValueError(f"No se encontró DATABASE_URL_B en: {env_path}")

# Crear motores únicamente para las bases de datos locales.
engine_local_a = create_engine(DATABASE_URL_A, pool_pre_ping=True)
engine_local_b = create_engine(DATABASE_URL_B, pool_pre_ping=True)

# Mantener sesiones separadas para cada rol de acceso local.
SessionRolA = sessionmaker(bind=engine_local_a)
SessionRolB = sessionmaker(bind=engine_local_b)
SessionLocal = sessionmaker(bind=engine_local_a)