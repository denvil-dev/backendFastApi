from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os 
from dotenv import load_dotenv
load_dotenv()
DATABASE_URL_A = os.getenv("DATABASE_URL_A")
DATABASE_URL_B = os.getenv("DATABASE_URL_B")
# 1. URLs para cada usuario/rol
DATABASE_URL_A = os.getenv("DATABASE_URL_A")
DATABASE_URL_B = os.getenv("DATABASE_URL_B")

# 2. Motores independientes para cada rol
engine_a = create_engine(DATABASE_URL_A, pool_pre_ping=True)
engine_b = create_engine(DATABASE_URL_B, pool_pre_ping=True)

# 3. Fábricas de sesiones separadas
SessionRolA = sessionmaker(bind=engine_a)
SessionRolB = sessionmaker(bind=engine_b)

# --- Ejemplo de uso para el Rol A ---
try:
    with engine_a.connect() as connection_a:
        resultado_a = connection_a.execute(text("SELECT VERSION();")).fetchone()
        print("Conexión Rol A exitosa:", resultado_a)
except Exception as e:
    print("Error en Rol A:", e)

# --- Ejemplo de uso para el Rol B ---
try:
    with engine_b.connect() as connection_b:
        resultado_b = connection_b.execute(text("SELECT VERSION();")).fetchone()
        print("Conexión Rol B exitosa:", resultado_b)
except Exception as e:
    print("Error en Rol B:", e)