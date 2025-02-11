import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..")

from fastapi import FastAPI
from app.routes import router

app = FastAPI()
app.include_router(router)

@app.get("/")
async def root():
    return {"message": "Servidor API Guacamole está rodando!"}