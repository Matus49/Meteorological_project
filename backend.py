import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import httpx

# Konfigurácia logovania pre prehľadnosť v Render.com
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="GaiaSenzor Core API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Konfigurácia pripojenia
API_BASE_URL = "https://projekttb.sksnr.sk/data/api.php"
AUTH = ("sks", "kolbe")

# Mapovanie zdrojov podľa požiadaviek
SOURCES = {
    "meteo": 0,
    "trieda": 1,
    "dvere": 8
}

async def fetch_api_data(source_id, limit=1):
    """Univerzálna funkcia na fetchovanie dát z API"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            url = f"{API_BASE_URL}?source={source_id}&sort=timestamp&dir=desc&limit={limit}"
            response = await client.get(url, auth=AUTH)
            if response.status_code == 200:
                data = response.json()
                return data.get('rows', [])
            return []
    except Exception as e:
        logger.error(f"Chyba pripojenia k zdroju {source_id}: {e}")
        return []

@app.get("/api/dashboard")
async def get_dashboard_data():
    # Načítanie aktuálnych dát
    meteo = await fetch_api_data(0, 1) # Meteo stanica
    trieda = await fetch_api_data(1, 1) # Trieda
    dvere = await fetch_api_data(8, 1)  # Dvere
    
    m = meteo[0] if meteo else {}
    t = trieda[0] if trieda else {}
    d = dvere[0] if dvere else {}

    return {
        "main_sensors": {
            "temperature": {"val": m.get("temperature"), "unit": "°C", "title": "Teplota"},
            "feels_like": {"val": m.get("feels_like"), "unit": "°C", "title": "Pocitová teplota"},
            "pressure": {"val": m.get("pressure"), "unit": "hPa", "title": "Tlak"},
            "co2": {"val": t.get("co2"), "unit": "ppm", "title": "CO2"}
        },
        "secondary_sensors": {
            "humidity": {"val": m.get("humidity"), "unit": "%", "title": "Vlhkosť"},
            "cloudiness": {"val": m.get("cloudiness"), "unit": "%", "title": "Oblačnosť"},
            "wind_speed": {"val": m.get("wind_speed"), "unit": "m/s", "title": "Rýchlosť vetra"},
            "wind_dir": {"val": m.get("wind_direction"), "unit": "°", "title": "Smer vetra"},
            "rain_1h": {"val": m.get("rain_1h"), "unit": "mm", "title": "Dážď (1h)"},
            "snow_1h": {"val": m.get("snow_1h"), "unit": "mm", "title": "Sneh (1h)"},
            "ghi": {"val": m.get("ghi"), "unit": "W/m²", "title": "GHI"},
            "clear_sky_ghi": {"val": m.get("clear_sky_ghi"), "unit": "W/m²", "title": "Clear Sky GHI"}
        },
        "door_status": {
            "state": {"val": d.get("state"), "title": "Stav dverí"}
        }
    }

@app.get("/api/history/{sensor_type}")
async def get_sensor_history(sensor_type: str):
    """Endpoint pre získanie histórie 500 záznamov pre grafy"""
    source_id = SOURCES.get(sensor_type, 0)
    return await fetch_api_data(source_id, 500)
