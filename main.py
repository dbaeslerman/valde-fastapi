from fastapi import FastAPI, Request, Form
from pymongo import MongoClient
from typing import Optional
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

@app.post("/webhook")
async def whatsapp_webhook(
    Body: str = Form(...),
    From: str = Form(...),
    NumMedia: str = Form(...),
    MediaUrl0: Optional[str] = Form(None),
    MediaContentType0: Optional[str] = Form(None)
):
    data = {
        "mensaje": Body,
        "telefono": From,
        "imagen_url": MediaUrl0 if int(NumMedia) > 0 else None,
        "tipo_media": MediaContentType0 if int(NumMedia) > 0 else None
    }
    result = collection.insert_one(data)
    data["_id"] = str(result.inserted_id)
    return {"msg": "Mensaje recibido", "data": data}
