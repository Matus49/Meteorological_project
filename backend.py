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
USER = "sks"
PASS = "kolbe"

async def fetch_data(source, limit):
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            url = f"{API_BASE_URL}?source={source}&sort=timestamp&dir=desc&limit={limit}"
            r = await client.get(url, auth=(USER, PASS))
            
            if r.status_code != 200:
                logger.error(f"Zdroj {source} vrátil kód {r.status_code}")
                return []
            return r.json()
    except Exception as e:
        logger.error(f"Chyba pripojenia k zdroju {source}: {e}")
        return []

@app.get("/api/dashboard")
async def get_dashboard_data():
    try:
        # Paralelné asynchrónne načítanie aktuálnych dát zo všetkých 3 podsystémov
        current_s0 = await fetch_data(source=0, limit=1) # Meteostanica
        current_s1 = await fetch_data(source=1, limit=1) # Trieda
        current_s8 = await fetch_data(source=8, limit=1) # Dvere

        # Vytiahnutie prvého riadku z 'rows' poistite proti prázdnym dátam
        c0 = current_s0.get('rows', [])[0] if isinstance(current_s0, dict) and 'rows' in current_s0 and len(current_s0['rows']) > 0 else {}
        c1 = current_s1.get('rows', [])[0] if isinstance(current_s1, dict) and 'rows' in current_s1 and len(current_s1['rows']) > 0 else {}
        c8 = current_s8.get('rows', [])[0] if isinstance(current_s8, dict) and 'rows' in current_s8 and len(current_s8['rows']) > 0 else {}

        # Návrat kompletných dát s pridanými metadátami pre inteligentné vykreslenie a filtrovanie
        return {
            # --- HLAVNÉ ÚDAJE (Kľúčové pre vrchný grid) ---
            "temperature": {
                "title": "Teplota vzduchu",
                "value": c0.get("temperature", "--"),
                "unit": "°C",
                "icon": "thermometer",
                "group": "meteo",
                "importance": "main"
            },
            "feels_like": {
                "title": "Pocitová teplota",
                "value": c0.get("feels_like", "--"),
                "unit": "°C",
                "icon": "cloud-sun",
                "group": "meteo",
                "importance": "main"
            },
            "pressure": {
                "title": "Atmosférický tlak",
                "value": c0.get("pressure", "--"),
                "unit": "hPa",
                "icon": "gauge",
                "group": "meteo",
                "importance": "main"
            },
            "co2": {
                "title": "Koncentrácia CO2",
                "value": c1.get("co2", "--"),
                "unit": "ppm",
                "icon": "wind",
                "group": "trieda",
                "importance": "main"
            },
            # --- VEDĽAJŠIE ÚDAJE ---
            "humidity": {
                "title": "Vlhkosť vzduchu",
                "value": c0.get("humidity", "--"),
                "unit": "%",
                "icon": "droplet",
                "group": "meteo",
                "importance": "secondary"
            },
            "cloudiness": {
                "title": "Oblačnosť",
                "value": c0.get("cloudiness", "--"),
                "unit": "%",
                "icon": "cloud",
                "group": "meteo",
                "importance": "secondary"
            },
            "wind_speed": {
                "title": "Rýchlosť vetra",
                "value": c0.get("wind_speed", "--"),
                "unit": "m/s",
                "icon": "info", # Bude nahradené Lucide ikonou vetra vo frontende
                "group": "meteo",
                "importance": "secondary"
            },
            "wind_direction": {
                "title": "Smer vetra",
                "value": c0.get("wind_direction", "--"),
                "unit": "°",
                "icon": "compass",
                "group": "meteo",
                "importance": "secondary"
            },
            "rain_1h": {
                "title": "Zrážky (1h)",
                "value": c0.get("rain_1h", "--"),
                "unit": "mm",
                "icon": "cloud-rain",
                "group": "meteo",
                "importance": "secondary"
            },
            "snow_1h": {
                "title": "Sneženie (1h)",
                "value": c0.get("snow_1h", "--"),
                "unit": "mm",
                "icon": "cloud-snow",
                "group": "meteo",
                "importance": "secondary"
            },
            "ghi": {
                "title": "Slnečné žiarenie (GHI)",
                "value": c0.get("ghi", "--"),
                "unit": "W/m²",
                "icon": "sun",
                "group": "meteo",
                "importance": "secondary"
            },
            "clear_sky_ghi": {
                "title": "Jasná obloha (GHI)",
                "value": c0.get("clear_sky_ghi", "--"),
                "unit": "W/m²",
                "icon": "sun-dim",
                "group": "meteo",
                "importance": "secondary"
            },
            # --- MONITOROVANIE VSTUPU ---
            "door_state": {
                "title": "Stav dverí",
                "value": c8.get("state", "--"), # Hodnota (0 alebo 1), frontend si ju transformuje na Otvorené/Zatvorené
                "unit": "",
                "icon": "door-closed",
                "group": "dvere",
                "importance": "secondary"
            }
        }
    except Exception as e:
        logger.error(f"Kritická chyba pri spracovaní dát: {e}")
        return {}
