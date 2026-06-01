import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import httpx

app = FastAPI(title="GaiaSenzor Core API")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

API_BASE_URL = "https://projekttb.sksnr.sk/data/api.php"
# Tieto údaje sú správne, len ich musíme použiť v správnom formáte
USER = "sks"
PASS = "kolbe"

MOCK_METRICS = {
    "temperature": {"title": "Teplota vzduchu", "value": 21.5, "unit": "°C", "icon": "🌡️", "trend": {"text": "Meteostanica (Záloha)", "type": "good"}},
    "humidity": {"title": "Vlhkosť vzduchu", "value": 55, "unit": "%", "icon": "💧", "trend": {"text": "Meteostanica (Záloha)", "type": "good"}},
    "pressure": {"title": "Atmosférický tlak", "value": 1013, "unit": "hPa", "icon": "⏱️", "trend": {"text": "Meteostanica (Záloha)", "type": "good"}},
    "temp_flower": {"title": "Teplota pri Kvete", "value": 23.1, "unit": "°C", "icon": "🌱", "trend": {"text": "Senzor Kvet (Záloha)", "type": "good"}},
    "hum_flower": {"title": "Vlhkosť pri Kvete", "value": 48, "unit": "%", "icon": "🪴", "trend": {"text": "Senzor Kvet (Záloha)", "type": "good"}}
}

async def fetch_data(source, limit):
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            url = f"{API_BASE_URL}?source={source}&sort=timestamp&dir=desc&limit={limit}"
            # OPRAVA: Používame tuple priamo tu
            r = await client.get(url, auth=(USER, PASS))
            
            if r.status_code != 200:
                logger.error(f"Zdroj {source} vrátil kód {r.status_code}")
                return []
            return r.json()
    except Exception as e:
        logger.error(f"Chyba pripojenia: {e}")
        return []

@app.get("/api/dashboard")
async def get_dashboard_data():
    try:
        # OPRAVA: Voláme správny názov funkcie fetch_data
        current_s0 = await fetch_data(source=0, limit=1)
        current_s1 = await fetch_data(source=1, limit=1)

        c0 = current_s0[0] if (isinstance(current_s0, list) and len(current_s0) > 0) else {}
        c1 = current_s1[0] if (isinstance(current_s1, list) and len(current_s1) > 0) else {}

        if not c0 and not c1:
            return MOCK_METRICS

        return {
            "temperature": {"title": "Teplota vzduchu", "value": c0.get("temp", 21.5), "unit": "°C", "icon": "🌡️", "trend": {"text": "Meteostanica", "type": "good"}},
            "humidity": {"title": "Vlhkosť vzduchu", "value": c0.get("humidity", 55), "unit": "%", "icon": "💧", "trend": {"text": "Meteostanica", "type": "good"}},
            "pressure": {"title": "Atmosférický tlak", "value": c0.get("pressure", 1013), "unit": "hPa", "icon": "⏱️", "trend": {"text": "Meteostanica", "type": "good"}},
            "temp_flower": {"title": "Teplota pri Kvete", "value": c1.get("temp", 23.1), "unit": "°C", "icon": "🌱", "trend": {"text": "Senzor Kvet", "type": "good"}},
            "hum_flower": {"title": "Vlhkosť pri Kvete", "value": c1.get("humidity", 48), "unit": "%", "icon": "🪴", "trend": {"text": "Senzor Kvet", "type": "good"}}
        }
    except Exception as e:
        logger.error(f"Kritická chyba: {e}")
        return MOCK_METRICS
