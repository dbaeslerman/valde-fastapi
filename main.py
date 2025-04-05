from fastapi import FastAPI, Request, Form
from typing import Optional
from pymongo import MongoClient
from dotenv import load_dotenv
import openai
import os
import requests

load_dotenv()

app = FastAPI()

# Carga variables desde el entorno (Render las inyecta automáticamente)
openai.api_key = os.getenv("OPENAI_API_KEY")
mongo_uri = os.getenv("MONGO_URI")from fastapi import FastAPI, Request, Form
from typing import Optional
from pymongo import MongoClient
from dotenv import load_dotenv
import openai
import os
import requests

load_dotenv()
app = FastAPI()

# Cargar claves desde variables de entorno (definidas en Render)
openai.api_key = os.getenv("OPENAI_API_KEY")
mongo_uri = os.getenv("MONGO_URI")
twilio_sid = os.getenv("TWILIO_ACCOUNT_SID")
twilio_token = os.getenv("TWILIO_AUTH_TOKEN")

# Conexión a MongoDB
client = MongoClient(mongo_uri)
db = client["valde_db"]
collection = db["reportes"]

# Función para analizar mensaje con IA
def analizar_mensaje(mensaje: str) -> str:
    prompt = f"""
    Analiza el siguiente mensaje de un usuario:

    "{mensaje}"

    Si falta información como el producto, canal, o si afecta al cliente, responde con una pregunta clara para completarlo.
    Si todo está bien, responde con "OK".
    """

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Eres un asistente que ayuda a completar reportes técnicos."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content.strip()

# Función para responder por WhatsApp usando Twilio
def send_whatsapp_message(to: str, message: str):
    url = f"https://api.twilio.com/2010-04-01/Accounts/{twilio_sid}/Messages.json"
    auth = (twilio_sid, twilio_token)

    data = {
        "From": "whatsapp:+14155238886",  # Número de prueba del sandbox
        "To": to,
        "Body": message
    }

    response = requests.post(url, data=data, auth=auth)
    return response.status_code, response.text

# Ruta de prueba
@app.get("/")
def home():
    return {"msg": "Valde API funcionando 👌"}

# Webhook que recibe los mensajes de WhatsApp
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

    # Analizar con IA
    respuesta_ia = analizar_mensaje(Body)
    if respuesta_ia != "OK":
        send_whatsapp_message(to=From, message=respuesta_ia)

    return {"msg": "Mensaje recibido", "data": data}

