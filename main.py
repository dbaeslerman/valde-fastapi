from fastapi import FastAPI, Request
from pymongo import MongoClient
import os

from dotenv import load_dotenv
load_dotenv()

app = FastAPI()

# Conexión a MongoDB
client = MongoClient(os.getenv("MONGO_URI"))
db = client["valde_db"]
collection = db["reportes"]

@app.get("/")
def home():
    return {"msg": "Valde API funcionando 👌"}

@app.post("/reporte")
async def nuevo_reporte(request: Request):
    data = await request.json()
    result = collection.insert_one(data)
    data["_id"] = str(result.inserted_id)
    return {"msg": "Reporte guardado", "data": data}
