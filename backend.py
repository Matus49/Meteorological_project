import logging
import asyncio
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

API_BASE = "https://projekttb.sksnr.sk/data/api.php"
AUTH = ("sks", "kolbe")

async def fetch(client: httpx.AsyncClient, source: int, limit: int = 1) -> dict | list:
    url = f"{API_BASE}?source={source}&sort=timestamp&dir=desc&limit={limit}"
    try:
        r = await client.get(url, auth=AUTH, timeout=10.0)
        if r.status_code != 200:
            logger.warning(f"source={source} HTTP {r.status_code}")
            return {}
        return r.json()
    except Exception as e:
        logger.error(f"source={source} chyba: {e}")
        return {}

def row(data: dict) -> dict:
    rows = data.get("rows", []) if isinstance(data, dict) else []
    return rows[0] if rows else {}

def g(d, *keys):
    """Skus viacero nazvov klucov, vrat prvy najdeny."""
    for k in keys:
        v = d.get(k)
        if v is not None:
            return v
    return "--"

@app.get("/api/uvod")
async def get_uvod():
    async with httpx.AsyncClient() as client:
        data = await fetch(client, source=0, limit=1)
    c = row(data)
    return {
        "temperature":    {"title": "Teplota",          "value": g(c, "temperature"),    "unit": "°C",   "icon": "thermometer"},
        "feels_like":     {"title": "Pocitova teplota", "value": g(c, "feels_like"),     "unit": "°C",   "icon": "cloud-sun"},
        "humidity":       {"title": "Vlhkost",          "value": g(c, "humidity"),       "unit": "%",    "icon": "droplet"},
        "pressure":       {"title": "Tlak",             "value": g(c, "pressure"),       "unit": "hPa",  "icon": "gauge"},
        "wind_speed":     {"title": "Rychlost vetra",   "value": g(c, "wind_speed"),     "unit": "m/s",  "icon": "wind"},
        "wind_direction": {"title": "Smer vetra",       "value": g(c, "wind_direction"), "unit": "°",    "icon": "compass"},
        "cloudiness":     {"title": "Oblacnost",        "value": g(c, "cloudiness"),     "unit": "%",    "icon": "cloud"},
        "rain_1h":        {"title": "Zrazky (1h)",      "value": g(c, "rain_1h"),        "unit": "mm",   "icon": "cloud-rain"},
        "snow_1h":        {"title": "Snezenie (1h)",    "value": g(c, "snow_1h"),        "unit": "mm",   "icon": "cloud-snow"},
        "ghi":            {"title": "Ziarenie GHI",     "value": g(c, "ghi"),            "unit": "W/m2", "icon": "sun"},
        "clear_sky_ghi":  {"title": "Jasna obloha GHI", "value": g(c, "clear_sky_ghi"), "unit": "W/m2", "icon": "sun-dim"},
        "timestamp": c.get("timestamp", "--"),
    }

@app.get("/api/skola")
async def get_skola():
    sources = list(range(9, 29))
    async with httpx.AsyncClient() as client:
        tasks = [fetch(client, s, limit=1) for s in sources]
        results = await asyncio.gather(*tasks)

    sensors = []
    temps = []
    for i, data in enumerate(results):
        c = row(data)
        temp = g(c, "TempC_SHT", "TEMPC_SHT", "tempc_sht")
        hum  = g(c, "Hum_SHT",   "HUM_SHT",   "hum_sht")
        batv = g(c, "BatV",      "BATV",       "batv")
        if temp != "--":
            try:
                temps.append(float(temp))
            except (ValueError, TypeError):
                pass
        sensors.append({
            "id":        i + 1,
            "source":    sources[i],
            "label":     f"TH sensor {i + 1:02d}",
            "temp":      temp,
            "hum":       hum,
            "batv":      batv,
            "timestamp": c.get("timestamp", "--"),
        })

    avg_temp = round(sum(temps) / len(temps), 2) if temps else "--"
    return {"sensors": sensors, "avg_temp": avg_temp}

@app.get("/api/trieda")
async def get_trieda():
    async with httpx.AsyncClient() as client:
        amb_d, pwr_d, lux_d, door_d = await asyncio.gather(
            fetch(client, 1, 1),
            fetch(client, 2, 1),
            fetch(client, 3, 1),
            fetch(client, 8, 1),
        )
    amb  = row(amb_d)
    pwr  = row(pwr_d)
    lux  = row(lux_d)
    door = row(door_d)

    door_raw = g(door, "Exti_status", "exti_status")
    if door_raw == "True":
        door_val = "Otvorene"
    elif door_raw == "False":
        door_val = "Zatvorene"
    else:
        door_val = "--"

    return {
        "ambient": {
            "temperature": {"title": "Teplota (vnutri)", "value": g(amb, "temperature", "temp"), "unit": "°C",  "icon": "thermometer", "source": 1, "key": "temperature"},
            "humidity":    {"title": "Vlhkost (vnutri)", "value": g(amb, "humidity", "hum"),     "unit": "%",   "icon": "droplet",     "source": 1, "key": "humidity"},
            "co2":         {"title": "CO2",              "value": g(amb, "co2", "CO2"),          "unit": "ppm", "icon": "wind",        "source": 1, "key": "co2"},
            "pressure":    {"title": "Tlak (vnutri)",    "value": g(amb, "pressure"),            "unit": "hPa", "icon": "gauge",       "source": 1, "key": "pressure"},
        },
        "power": {
            "active_power":      {"title": "Aktivny vykon", "value": g(pwr, "active_power"),      "unit": "W",  "icon": "zap",      "source": 2, "key": "active_power"},
            "voltage":           {"title": "Napatie",       "value": g(pwr, "voltage"),           "unit": "V",  "icon": "activity", "source": 2, "key": "voltage"},
            "current":           {"title": "Prud",          "value": g(pwr, "current"),           "unit": "mA", "icon": "waves",    "source": 2, "key": "current"},
            "power_consumption": {"title": "Spotreba",      "value": g(pwr, "power_consumption"), "unit": "Wh", "icon": "battery",  "source": 2, "key": "power_consumption"},
            "power_factor":      {"title": "Ucinnik",       "value": g(pwr, "power_factor"),      "unit": "%",  "icon": "percent",  "source": 2, "key": "power_factor"},
            "socket_status":     {"title": "Stav zasuvky",  "value": g(pwr, "socket_status"),     "unit": "",   "icon": "plug",     "source": 2, "key": "socket_status"},
        },
        "lux": {
            "ILL_lux":   {"title": "Intenzita svetla", "value": g(lux, "ILL_lux", "ill_lux"), "unit": "lx", "icon": "sun",         "source": 3, "key": "ILL_lux"},
            "TempC_SHT": {"title": "Teplota (lux)",   "value": g(lux, "TempC_SHT"),          "unit": "°C", "icon": "thermometer", "source": 3, "key": "TempC_SHT"},
            "Hum_SHT":   {"title": "Vlhkost (lux)",   "value": g(lux, "Hum_SHT"),            "unit": "%",  "icon": "droplet",     "source": 3, "key": "Hum_SHT"},
        },
        "door": {
            "state":     {"title": "Dvere (IT ucebna)", "value": door_val, "unit": "", "icon": "door-closed", "source": 8, "key": "Exti_status"},
            "timestamp": door.get("timestamp", "--"),
        },
    }

@app.get("/api/history/{source}")
async def get_history(source: int, limit: int = 500):
    async with httpx.AsyncClient() as client:
        data = await fetch(client, source, limit)
    rows = data.get("rows", []) if isinstance(data, dict) else []
    return {"rows": list(reversed(rows)), "columns": data.get("columns", [])}
