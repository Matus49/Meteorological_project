import os
import logging
from typing import Dict, Any, List
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import httpx

# Inicializácia aplikácie a logovania
app = FastAPI(title="GaiaSenzor Core API")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Povolenie CORS pre hladkú komunikáciu s frontendom
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Reálne API linky školskej brány
API_BASE_URL = "https://projekttb.sksnr.sk/data/api.php"
API_USER = "sks"
API_PASSWORD = "kolbe"

# Lokálne záložné dáta pre prípad, že školský server vypadne alebo pošle zlý formát
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
            r = await client.get(url, auth=AUTH)
            
            # TOTO JE KĽÚČOVÁ ČASŤ PRE DIAGNOSTIKU:
            if r.status_code != 200:
                print(f"CHYBA: Zdroj {source} vrátil kód {r.status_code}")
                print(f"Text odpovede servera: {r.text}")
                return []
                
            return r.json()
    except Exception as e:
        print(f"KRITICKÁ CHYBA pri source {source}: {e}")
        return []

@app.get("/api/dashboard")
async def get_dashboard_data():
    try:
        current_s0 = await fetch_api_data(source=0, limit=1)
        current_s1 = await fetch_api_data(source=1, limit=1)

        # Nepriestrelná kontrola: Vytiahni prvok [0] iba ak ide o nezáporný zoznam s dictom vo vnútri
        c0 = current_s0[0] if (isinstance(current_s0, list) and len(current_s0) > 0 and isinstance(current_s0[0], dict)) else {}
        c1 = current_s1[0] if (isinstance(current_s1, list) and len(current_s1) > 0 and isinstance(current_s1[0], dict)) else {}

        # Ak z obidvoch zdrojov neprišlo nič validné, vráť rovno mock dáta
        if not c0 and not c1:
            logger.warning("Školské API neposkytlo dáta. Aktivuje sa lokálny fallback.")
            return MOCK_METRICS

        return {
            "temperature": {
                "title": "Teplota vzduchu",
                "value": c0.get("temp", c0.get("temperature", 21.5)),
                "unit": "°C",
                "icon": "🌡️",
                "trend": {"text": "Meteostanica", "type": "good"}
            },
            "humidity": {
                "title": "Vlhkosť vzduchu",
                "value": c0.get("humidity", c0.get("hum", 55)),
                "unit": "%",
                "icon": "💧",
                "trend": {"text": "Meteostanica", "type": "good"}
            },
            "pressure": {
                "title": "Atmosférický tlak",
                "value": c0.get("pressure", c0.get("barometer", 1013)),
                "unit": "hPa",
                "icon": "⏱️",
                "trend": {"text": "Meteostanica", "type": "good"}
            },
            "temp_flower": {
                "title": "Teplota pri Kvete",
                "value": c1.get("temp", c1.get("temperature", 23.1)),
                "unit": "°C",
                "icon": "🌱",
                "trend": {"text": "Senzor Kvet", "type": "good"}
            },
            "hum_flower": {
                "title": "Vlhkosť pri Kvete",
                "value": c1.get("humidity", c1.get("hum", 48)),
                "unit": "%",
                "icon": "🪴",
                "trend": {"text": "Senzor Kvet", "type": "good"}
            }
        }
    except Exception as general_error:
        # Ak by sa čokoľvek nečakane pokazilo, zachráň to odoslaním MOCK dát namiesto 500-ky
        logger.error(f"Kritická chyba endpointu: {general_error}")
        return MOCK_METRICS

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("backend:app", host="0.0.0.0", port=port)
