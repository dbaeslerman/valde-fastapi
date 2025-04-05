from fastapi import FastAPI, Request
from pymongo import MongoClient
from openai import OpenAI
from dotenv import load_dotenv
import os
import requests

load_dotenv()

app = FastAPI()

# Carga variables desde el entorno
openai_api_key = os.getenv("OPENAI_API_KEY")
mongo_uri = os.getenv("MONGO_URI")
twilio_sid = os.getenv("TWILIO_ACCOUNT_SID")
twilio_token = os.getenv("TWILIO_AUTH_TOKEN")

# Conexión MongoDB
client = MongoClient(mongo_uri)
db = client["valde_db"]
collection = db["reportes"]

# Cliente OpenAI
openai_client = OpenAI(api_key=openai_api_key)

# Analiza mensaje con IA
def analizar_mensaje(mensaje: str) -> str:
    prompt = f"""
    Analiza el siguiente mensaje de un usuario:

    "{mensaje}"

    Si falta información como el producto, canal, o si afecta al cliente, responde con una pregunta clara para completarlo.
    Si todo está bien, responde con "OK".
    """

    response = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Eres un asistente que ayuda a completar reportes técnicos."},
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content.strip()

# Envía respuesta por WhatsApp
def send_whatsapp_message(to: str, message: str):
    url = f"https://api.twilio.com/2010-04-01/Accounts/{twilio_sid}/Messages.json"
    data = {
        "From": "whatsapp:+14155238886",  # número sandbox Twilio
        "To": to,
        "Body": message
    }

    response = requests.post(url, data=data, auth=(twilio_sid, twilio_token))
    return response.status_code, response.text

# Ruta de prueba
@app.get("/")
def home():
    return {"msg": "Valde API funcionando 👌"}

# Webhook de WhatsApp
@app.post("/webhook")
async def recibir_mensaje(request: Request):
    form = await request.form()

    mensaje = form.get("Body")
    telefono = form.get("From")
    media_url = form.get("MediaUrl0")
    media_type = form.get("MediaContentType0")

    # Guardar en MongoDB
    reporte = {
        "mensaje": mensaje,
        "telefono": telefono,
        "imagen_url": media_url,
        "tipo_media": media_type
    }
    collection.insert_one(reporte)

    # Procesar con IA y responder
    respuesta_ia = analizar_mensaje(mensaje)
    send_whatsapp_message(telefono, respuesta_ia)

    return {"status": "ok"}

