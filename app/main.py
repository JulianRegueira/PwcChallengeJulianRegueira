'''
PRIOS

1-Crear FastAPI básico con endpoints de prueba.

2-Ingestar un CSV y almacenarlo como Parquet en tu “bronze layer”.

3-Transformar esos datos usando pandas y cargar en SQLite con SQLModel.

4-Diseñar un star schema con 1 tabla de hechos + 5 dimensiones.

5-Exponer un endpoint para consultar Gold layer.

6-Levantar Typesense con Docker y permitir búsquedas desde FastAPI.

Autenticación básica HTTP en la API.'
'''

from fastapi import FastAPI
from app.api.players import router as players_router

app = FastAPI(title="Soccer Player Market Analysis")

app.include_router(players_router)
