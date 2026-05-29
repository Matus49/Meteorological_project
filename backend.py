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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API linky a prístupy
API_BASE_URL = "https://projekttb.sksnr.sk/data/api.php"
API_USER = "sks"
API_PASSWORD = "kolbe"

# Fallback dáta pre prípad výpadku siete školskej brány
MOCK_METRICS = {
    "temperature": {"title": "Teplota vzduchu", "value": 21.5, "unit": "°C", "icon": "🌡️", "trend": {"text": "Meteostanica (Záloha)", "type": "good"}, "history": [{"time": "10:00", "value": 19.5}, {"time": "11:00", "value": 20.8}, {"time": "12:00", "value": 21.5}]},
    "humidity": {"title": "Vlhkosť vzduchu", "value": 55, "unit": "%", "icon": "💧", "trend": {"text": "Meteostanica (Záloha)", "type": "good"}, "history": [{"time": "10:00", "value": 58}, {"time": "11:00", "value": 56}, {"time": "12:00", "value": 55}]},
    "pressure": {"title": "Atmosférický tlak", "value": 1013, "unit": "hPa", "icon": "⏱️", "trend": {"text": "Meteostanica (Záloha)", "type": "good"}, "history": [{"time": "10:00", "value": 1012}, {"time": "11:00", "value": 1013}, {"time": "12:00", "value": 1013}]},
    "temp_flower": {"title": "Teplota pri Kvete", "value": 23.1, "unit": "°C", "icon": "🌱", "trend": {"text": "Senzor Kvet (Záloha)", "type": "good"}, "history": [{"time": "10:00", "value": 22.0}, {"time": "11:00", "value": 22.7}, {"time": "12:00", "value": 23.1}]},
    "hum_flower": {"title": "Vlhkosť pri Kvete", "value": 48, "unit": "%", "icon": "🪴", "trend": {"text": "Senzor Kvet (Záloha)", "type": "good"}, "history": [{"time": "10:00", "value": 50}, {"time": "11:00", "value": 49}, {"time": "12:00", "value": 48}]}
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
        logger.error(f"Chyba pri sťahovaní source={source}, limit={limit}: {e}")
    return []

def format_time(timestamp: Optional[str]) -> str:
    """Vytiahne iba HH:MM z timestampu pre čisté zobrazenie."""
    if not timestamp or " " not in timestamp:
        return "--:--"
    try:
        return timestamp.split(" ")[1][:5]
    except Exception:
        return "--:--"

@app.get("/api/dashboard")
async def get_dashboard_data():
    """Hlavný endpoint upravený priamo pre potreby frontend dizajnu."""
    current_s0 = await fetch_api_data(source=0, limit=1)
    history_s0 = await fetch_api_data(source=0, limit=15)
    current_s1 = await fetch_api_data(source=1, limit=1)
    history_s1 = await fetch_api_data(source=1, limit=15)

    # Ak škola nevráti nič, pošleme von lokálne mock dáta s príznakom backup_api
    if not current_s0 and not current_s1:
        logger.warning("Dáta nedostupné. Aktivuje sa lokálny fallback.")
        return {
            "source": "backup_api",
            "weather": MOCK_METRICS
        }

    # Extrakcia aktuálnych hodnôt
    c0 = current_s0[0] if current_s0 else {}
    c1 = current_s1[0] if current_s1 else {}

    h0_reversed = list(reversed(history_s0))
    h1_reversed = list(reversed(history_s1))

    # Tvorba štruktúry presne podla očakávania index.html
    metrics = {
        "temperature": {
            "title": "Teplota vzduchu",
            "value": c0.get("temp", c0.get("temperature", 0)),
            "unit": "°C",
            "icon": "🌡️",
            "trend": {"text": "Meteostanica", "type": "good"},
            "history": [{"time": format_time(x.get("timestamp")), "value": x.get("temp", x.get("temperature", 0))} for x in h0_reversed]
        },
        "humidity": {
            "title": "Vlhkosť vzduchu",
            "value": c0.get("humidity", c0.get("hum", 0)),
            "unit": "%",
            "icon": "💧",
            "trend": {"text": "Meteostanica", "type": "good"},
            "history": [{"time": format_time(x.get("timestamp")), "value": x.get("humidity", x.get("hum", 0))} for x in h0_reversed]
        },
        "pressure": {
            "title": "Atmosférický tlak",
            "value": c0.get("pressure", c0.get("barometer", 0)),
            "unit": "hPa",
            "icon": "⏱️",
            "trend": {"text": "Meteostanica", "type": "good"},
            "history": [{"time": format_time(x.get("timestamp")), "value": x.get("pressure", x.get("barometer", 0))} for x in h0_reversed]
        },
        "temp_flower": {
            "title": "Teplota pri Kvete",
            "value": c1.get("temp", c1.get("temperature", 0)),
            "unit": "°C",
            "icon": "🌱",
            "trend": {"text": "Senzor Kvet", "type": "good"},
            "history": [{"time": format_time(x.get("timestamp")), "value": x.get("temp", x.get("temperature", 0))} for x in h1_reversed]
        },
        "hum_flower": {
            "title": "Vlhkosť pri Kvete",
            "value": c1.get("humidity", c1.get("hum", 0)),
            "unit": "%",
            "icon": "🪴",
            "trend": {"text": "Senzor Kvet", "type": "good"},
            "history": [{"time": format_time(x.get("timestamp")), "value": x.get("humidity", x.get("hum", 0))} for x in h1_reversed]
        }
    }

    return {
        "source": "live_api",
        "weather": metrics
    }

if __name__ == "__main__":
    import uvicorn
    # Opravené z main:app na backend:app
    uvicorn.run("backend:app", host="0.0.0.0", port=8000, reload=True)
