from fastapi import FastAPI
from src.Routes.LeerCsvRoute import csv
from src.Routes.RankingRoute import ranking
app = FastAPI()


app.include_router(csv)
app.include_router(ranking)


@app.get("/")
async def root():
    return "hola"
