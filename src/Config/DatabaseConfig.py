from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker




DATABASE_URL = (
    "postgresql+psycopg2://rol_backend:backend_password_2026@localhost:5433/siftc1_db"
)


engine= create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

try:
    with engine.connect() as connection:
        resultado = connection.execute(text("SELECT VERSION();")).fetchone()
        print (resultado)
 

except Exception as e :
    print (e)