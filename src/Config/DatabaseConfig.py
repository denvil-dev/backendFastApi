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
DATABASE_LOCALA = os.getenv("DATABASE_LOCALA")
DATABASE_LOCALB = os.getenv("DATABASE_LOCALB")

if not DATABASE_LOCALA:
    raise ValueError(f"No se encontró DATABASE_LOCALA en: {env_path}")
if not DATABASE_LOCALB:
    raise ValueError(f"No se encontró DATABASE_LOCALB en: {env_path}")

# Crear motores únicamente para las bases de datos locales.
engine_local_a = create_engine(DATABASE_LOCALA, pool_pre_ping=True)
engine_local_b = create_engine(DATABASE_LOCALB, pool_pre_ping=True)

# Mantener sesiones separadas para cada rol de acceso local.
SessionRolA = sessionmaker(bind=engine_local_a)
SessionRolB = sessionmaker(bind=engine_local_b)
SessionLocal = sessionmaker(bind=engine_local_a)