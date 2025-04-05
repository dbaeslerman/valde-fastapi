from fastapi import FastAPI, Request, Form
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import openai
import requests

load_dotenv()

# === Variables de entorno ===
openai.api_key = os.getenv("OPENAI_API_KEY")
mongo_uri = os.getenv("MONGO_URI")
twilio_sid = os.getenv("TWILIO_ACCOUNT_SID")
twilio_token = os.getenv("TWILIO_AUTH_TOKEN")

# === Conexión a MongoDB ===
client = MongoClient(mongo_uri)
db = client["valde_db"]
collection = db["reportes"]

app = FastAPI()

# === Función IA para analizar el mensaje ===
def analizar_mensaje(mensaje: str) -> str:
    prompt = f"""
Analiza el siguiente mensaje de un usuario. Si falta información como el producto, canal, o si afecta al cliente, responde con una pregunta clara para completarlo. 
Si todo está bien, responde con "OK".

"{mensaje}"
"""

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Eres un asistente que ayuda a completar reportes técnicos."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content.strip()

# === Función para responder vía WhatsApp ===
def send_whatsapp_message(to: str, message: str):
    url = f"https://api.twilio.com/2010-04-01/Accounts/{twilio_sid}/Messages.json"
    data = {
        "From": "whatsapp:+14155238886",  # Sandbox Twilio
        "To": to,
        "Body": message
    }
    auth = (twilio_sid, twilio_token)
    response = requests.post(url, data=data, auth=auth)
    return response.status_code, response.text

# === Ruta básica ===
@app.get("/")
def home():
    return {"msg": "Valde API funcionando 👌"}

# === Webhook de Twilio WhatsApp ===
@app.post("/webhook")
async def recibir_mensaje(
    From: str = Form(...),
    Body: str = Form(...),
    NumMedia: str = Form(default="0"),
    MediaUrl0: str = Form(default=None),
    MediaContentType0: str = Form(default=None)
):
    # Analizar mensaje
    respuesta_ia = analizar_mensaje(Body)

    # Guardar en MongoDB
    reporte = {
        "telefono": From,
        "mensaje": Body,
        "respuesta_ia": respuesta_ia,
        "imagen_url": MediaUrl0 if NumMedia != "0" else None,
        "tipo_media": MediaContentType0 if NumMedia != "0" else None
    }
    collection.insert_one(reporte)

    # Enviar respuesta por WhatsApp
    send_whatsapp_message(From, respuesta_ia)

    return {"status": "ok"}
