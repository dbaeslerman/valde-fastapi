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

# === Base de datos Mongo ===
client = MongoClient(mongo_uri)
db = client["valde_db"]
collection = db["reportes"]

# === App FastAPI ===
app = FastAPI()


# === Función IA para analizar mensaje ===
def analizar_mensaje(mensaje: str) -> str:
    prompt = f"""
Analiza el siguiente mensaje de un usuario y responde con una pregunta clara si falta información (como producto, canal, o si afecta al cliente). Si todo está bien, responde con "OK".

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
        "From": "whatsapp:+14155238886",  # número del sandbox
        "To": to,
        "Body": message
    }
    auth = (twilio_sid, twilio_token)
    response = requests.post(url, data=data, auth=auth)
    return response.status_code, response.text


# === Ruta base para test ===
@app.get("/")
def home():
    return {"msg": "Valde API funcionando 👌"}


# === Webhook de WhatsApp ===
@app.post("/webhook")
async def recibir_mensaje(
    From: str = Form(...),
    Body: str = Form(...),
    NumMedia: str = Form(default="0")
):
    imagen_url = None
    tipo_media = None

    if NumMedia != "0":
        imagen_url = Form("MediaUrl0")
        tipo_media = Form("MediaContentType0")

    # Analizar mensaje con IA
    respuesta_ia = analizar_mensaje(Body)

    # Guardar en Mongo
    reporte = {
        "telefono": From,

