import os
import math
import logging
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx

# Inicializácia aplikácie a logovania
app = FastAPI(title="Boho School Weather Station API", version="1.0.0")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Povolenie CORS pre hladkú komunikáciu s frontendom
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Konfigurácia externého API
SCHOOL_API_URL = "https://projekttb.sksnr.sk/data"
API_USER = "sks"
API_PASSWORD = "kolbe"

# Realistické mockované dáta pre prípad výpadku (Fallback)
MOCK_DATA = {
    "weather": {
        "temperature_out": 22.4,
        "humidity_out": 55.0,
        "pressure": 1013.25,
        "rain_1h": 0.0,  # mm/h, ak > 0 -> prší
        "cloudiness": 20, # v %
        "ghi": 450,       # Globálne horizontálne žiarenie (W/m2)
    },
    "classrooms": [
        {"id": "A204", "name": "Učebňa Informatiky", "co2": 850, "temperature": 21.8, "humidity": 45, "noise": 42, "door_open": False},
        {"id": "B101", "name": "Fyzikálne Laboratórium", "co2": 1350, "temperature": 23.1, "humidity": 52, "noise": 65, "door_open": True},
        {"id": "C302", "name": "Jazyková Class", "co2": 580, "temperature": 20.5, "humidity": 40, "noise": 30, "door_open": False}
    ],
    "history": [
        {"time": "08:00", "temp": 18.2, "co2_avg": 620},
        {"time": "10:00", "temp": 19.5, "co2_avg": 950},
        {"time": "12:00", "temp": 21.1, "co2_avg": 1100},
        {"time": "14:00", "temp": 22.4, "co2_avg": 1250},
        {"time": "16:00", "temp": 21.8, "co2_avg": 800},
    ]
}

def calculate_productivity_index(co2: float, temp: float, humidity: float) -> int:
    """
    Vypočíta Index produktivity (0-100%) na základe environmentálnych faktorov.
    Optimal: CO2 < 600ppm, Temp: 20-22°C, Humidity: 40-60%
    """
    # 1. CO2 penalizácia (najväčší vplyv na kognitívne funkcie)
    if co2 <= 600:
        co2_score = 100
    elif co2 > 2500:
        co2_score = 10
    else:
        co2_score = 100 - ((co2 - 600) / 1900) * 80

    # 2. Teplotná penalizácia
    if 20.0 <= temp <= 22.5:
        temp_score = 100
    else:
        deviation = min(abs(temp - 21.2), 10)
        temp_score = max(100 - (deviation * 15), 20)

    # 3. Vlhkostná penalizácia
    if 40 <= humidity <= 60:
        hum_score = 100
    else:
        deviation = min(abs(humidity - 50), 40)
        hum_score = max(100 - (deviation * 1.5), 40)

    # Vážený priemer: CO2 (50%), Teplota (35%), Vlhkosť (15%)
    index = (co2_score * 0.50) + (temp_score * 0.35) + (hum_score * 0.15)
    return round(max(0, min(100, index)))

async def fetch_school_data() -> Optional[Dict[str, Any]]:
    """Bezpečne stiahne dáta zo školskej meteostanice s timeoutom."""
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(SCHOOL_API_URL, auth=(API_USER, API_PASSWORD))
            if response.status_code == 200:
                return response.json()
            logger.warning(f"School API returned status {response.status_code}. Using fallback.")
    except Exception as e:
        logger.error(f"Failed to fetch school data due to: {str(e)}. Activating fallback mockup.")
    return None

def map_raw_to_boho_schema(raw_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Transformuje surové dáta z API do čistého formátu pre náš frontend.
    Ak sú dáta nedostupné, vstrekne validnú štruktúru z mocku.
    """
    if not raw_data:
        # Vstreknutie výpočtu indexu aj do mock dát
        processed_classrooms = []
        for room in MOCK_DATA["classrooms"]:
            room_copy = room.copy()
            room_copy["productivity_index"] = calculate_productivity_index(room["co2"], room["temperature"], room["humidity"])
            processed_classrooms.append(room_copy)
        
        return {
            "source": "fallback_mock",
            "weather": MOCK_DATA["weather"],
            "classrooms": processed_classrooms,
            "history": MOCK_DATA["history"]
        }

    # TU PREBIEHA MAPOVANIE REÁLNEHO API (Prispôsob podľa presnej štruktúry vášho JSONu)
    # Predpokladajme ideálne mapovanie z reálneho JSONu:
    try:
        weather_part = {
            "temperature_out": raw_data.get("outside_temp", raw_data.get("temp", 22.4)),
            "humidity_out": raw_data.get("outside_hum", 55.0),
            "pressure": raw_data.get("pressure", 1013.2),
            "rain_1h": raw_data.get("rain", 0.0),
            "cloudiness": raw_data.get("clouds", 20),
            "ghi": raw_data.get("ghi", 450)
        }
        
        # Iterácia cez interiérové senzory školskej siete
        classrooms_part = []
        raw_rooms = raw_data.get("rooms", [])
        
        if not raw_rooms: # Ak štruktúra neobsahuje izby, vygenerujeme ich zo surových dát
            return map_raw_to_boho_schema(None)

        for room in raw_rooms:
            co2 = room.get("co2", 800)
            t = room.get("temp", 22.0)
            h = room.get("hum", 45)
            classrooms_part.append({
                "id": room.get("id"),
                "name": room.get("name"),
                "co2": co2,
                "temperature": t,
                "humidity": h,
                "noise": room.get("noise", 40),
                "door_open": room.get("door", False),
                "productivity_index": calculate_productivity_index(co2, t, h)
            })

        return {
            "source": "live_api",
            "weather": weather_part,
            "classrooms": classrooms_part,
            "history": raw_data.get("history", MOCK_DATA["history"])
        }
    except Exception as e:
        logger.error(f"Error parsing raw data: {e}. Falling back.")
        return map_raw_to_boho_schema(None)

# --- API ENDPOINTY ---

@app.get("/api/weather/current")
async def get_current_weather():
    raw = await fetch_school_data()
    data = map_raw_to_boho_schema(raw)
    return data["weather"]

@app.get("/api/classrooms")
async def get_classrooms():
    raw = await fetch_school_data()
    data = map_raw_to_boho_schema(raw)
    return data["classrooms"]

@app.get("/api/dashboard")
async def get_full_dashboard():
    """Hlavný endpoint pre frontend – vracia všetko naraz, šetrí requesty."""
    raw = await fetch_school_data()
    return map_raw_to_boho_schema(raw)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
