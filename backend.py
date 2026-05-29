import os
import logging
from typing import Dict, Any, List, Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import httpx

# Inicializácia aplikácie a logovania
app = FastAPI(title="GaiaSenzor Core API", version="2.0.0")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Povolenie CORS pre hladkú komunikáciu s GitHub Pages frontendom
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Reálne API linky školskej brány
API_BASE_URL = "https://projekttb.sksnr.sk/data/api.php"
API_USER = "sks"
API_PASSWORD = "kolbe"

# Lokálne záložné dáta pre prípad, že školský server vypadne
MOCK_METRICS = {
    "temperature": {"title": "Teplota vzduchu", "value": 21.5, "unit": "°C", "icon": "🌡️", "trend": {"text": "Meteostanica (Záloha)", "type": "good"}},
    "humidity": {"title": "Vlhkosť vzduchu", "value": 55, "unit": "%", "icon": "💧", "trend": {"text": "Meteostanica (Záloha)", "type": "good"}},
    "pressure": {"title": "Atmosférický tlak", "value": 1013, "unit": "hPa", "icon": "⏱️", "trend": {"text": "Meteostanica (Záloha)", "type": "good"}},
    "temp_flower": {"title": "Teplota pri Kvete", "value": 23.1, "unit": "°C", "icon": "🌱", "trend": {"text": "Senzor Kvet (Záloha)", "type": "good"}},
    "hum_flower": {"title": "Vlhkosť pri Kvete", "value": 48, "unit": "%", "icon": "🪴", "trend": {"text": "Senzor Kvet (Záloha)", "type": "good"}}
}

async def fetch_api_data(source: int, limit: int) -> List[Any]:
    """Pomocná funkcia na sťahovanie dát z konkrétneho zdroja s limitom."""
    url = f"{API_BASE_URL}?source={source}&sort=timestamp&dir=desc&limit={limit}"
    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            response = await client.get(url, auth=(API_USER, API_PASSWORD))
            if response.status_code == 200:
                return response.json()
    except Exception as e:
        logger.error(f"Chyba pri sťahovaní source={source}: {e}")
    return []

@app.get("/api/dashboard")
async def get_dashboard_data():
    """Hlavný endpoint posielajúci flat JSON štruktúru priamo pre frontend."""
    current_s0 = await fetch_api_data(source=0, limit=1)
    current_s1 = await fetch_api_data(source=1, limit=1)

    # Ak škola nevráti nič (timeout/chyba), okamžite posielame lokálny fallback
    if not current_s0 and not current_s1:
        logger.warning("Školské API nedostupné. Aktivuje sa lokálny fallback.")
        return MOCK_METRICS

    c0 = current_s0[0] if current_s0 else {}
    c1 = current_s1[0] if current_s1 else {}

    # Vrátenie čistého slovníka metrík napriamo, aby JavaScript na webe nezlyhal
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

if __name__ == "__main__":
    import uvicorn
    # Spúšťanie lokálne (názov súboru uvicorn hľadá ako backend.py)
    uvicorn.run("backend:app", host="0.0.0.0", port=8000, reload=True)
