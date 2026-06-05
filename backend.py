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

# ── Pomocná funkcia: načíta jeden zdroj ──────────────────────────────────────
async def fetch(client: httpx.AsyncClient, source: int, limit: int = 1) -> dict | list:
    url = f"{API_BASE}?source={source}&sort=timestamp&dir=desc&limit={limit}"
    try:
        r = await client.get(url, auth=AUTH, timeout=10.0)
        if r.status_code != 200:
            logger.warning(f"source={source} → HTTP {r.status_code}")
            return {}
        return r.json()
    except Exception as e:
        logger.error(f"source={source} chyba: {e}")
        return {}

def row(data: dict) -> dict:
    """Vytiahne prvý riadok z 'rows', alebo vráti prázdny dict."""
    rows = data.get("rows", []) if isinstance(data, dict) else []
    return rows[0] if rows else {}

# ── /api/uvod – Úvodná obrazovka ─────────────────────────────────────────────
# Meteostanica Hrad (source=0) + kamery
@app.get("/api/uvod")
async def get_uvod():
    async with httpx.AsyncClient() as client:
        data = await fetch(client, source=0, limit=1)
    c = row(data)
    return {
        "temperature":    {"title": "Teplota",           "value": c.get("temperature", "--"),    "unit": "°C",   "icon": "thermometer"},
        "feels_like":     {"title": "Pocitová teplota",  "value": c.get("feels_like", "--"),     "unit": "°C",   "icon": "cloud-sun"},
        "humidity":       {"title": "Vlhkosť",           "value": c.get("humidity", "--"),       "unit": "%",    "icon": "droplet"},
        "pressure":       {"title": "Tlak",              "value": c.get("pressure", "--"),       "unit": "hPa",  "icon": "gauge"},
        "wind_speed":     {"title": "Rýchlosť vetra",    "value": c.get("wind_speed", "--"),     "unit": "m/s",  "icon": "wind"},
        "wind_direction": {"title": "Smer vetra",        "value": c.get("wind_direction", "--"), "unit": "°",    "icon": "compass"},
        "cloudiness":     {"title": "Oblačnosť",         "value": c.get("cloudiness", "--"),     "unit": "%",    "icon": "cloud"},
        "rain_1h":        {"title": "Zrážky (1h)",       "value": c.get("rain_1h", "--"),        "unit": "mm",   "icon": "cloud-rain"},
        "snow_1h":        {"title": "Sneženie (1h)",     "value": c.get("snow_1h", "--"),        "unit": "mm",   "icon": "cloud-snow"},
        "ghi":            {"title": "Žiarenie GHI",      "value": c.get("ghi", "--"),            "unit": "W/m²", "icon": "sun"},
        "clear_sky_ghi":  {"title": "Jasná obloha GHI",  "value": c.get("clear_sky_ghi", "--"), "unit": "W/m²", "icon": "sun-dim"},
        "timestamp":      c.get("timestamp", "--"),
    }

# ── /api/skola – Obrazovka Škola (TH senzory 1–20, source 9–28) ──────────────
@app.get("/api/skola")
async def get_skola():
    # TH senzory: TH01=source9, TH02=source10 … TH20=source28
    sources = list(range(9, 29))  # 9..28 → 20 senzorov

    async with httpx.AsyncClient() as client:
        tasks = [fetch(client, s, limit=1) for s in sources]
        results = await asyncio.gather(*tasks)

    sensors = []
    temps = []
    for i, data in enumerate(results):
        c = row(data)
        temp = c.get("TEMPC_SHT", c.get("tempc_sht", None))
        hum  = c.get("HUM_SHT",   c.get("hum_sht",   None))
        batv = c.get("BATV",      c.get("batv",       None))
        if temp is not None:
            try:
                temps.append(float(temp))
            except (ValueError, TypeError):
                pass
        sensors.append({
            "id":      i + 1,          # TH číslo (1–20)
            "source":  sources[i],     # source ID pre históriu
            "label":   f"TH sensor {i + 1:02d}",
            "temp":    temp if temp is not None else "--",
            "hum":     hum  if hum  is not None else "--",
            "batv":    batv if batv is not None else "--",
            "timestamp": c.get("timestamp", "--"),
        })

    avg_temp = round(sum(temps) / len(temps), 2) if temps else "--"

    return {
        "sensors":  sensors,
        "avg_temp": avg_temp,
    }

# ── /api/trieda – Obrazovka Trieda IT ─────────────────────────────────────────
# Ambient=source1, PowerMeter=source2, Lux=source3, Door05=source8
@app.get("/api/trieda")
async def get_trieda():
    async with httpx.AsyncClient() as client:
        amb_d, pwr_d, lux_d, door_d = await asyncio.gather(
            fetch(client, 1, 1),   # Ambient sensor 01
            fetch(client, 2, 1),   # Power meter 01 (3D tlačiareň)
            fetch(client, 3, 1),   # Lux sensor 01
            fetch(client, 8, 1),   # Door sensor 05
        )

    amb  = row(amb_d)
    pwr  = row(pwr_d)
    lux  = row(lux_d)
    door = row(door_d)

    # Celková energia – ak Power Meter má kumulatívne pole
    energy_keys = ["total_energy", "energy", "kwh", "consumption", "total", "import_energy"]
    total_energy = "--"
    for k in energy_keys:
        v = pwr.get(k) or pwr.get(k.upper())
        if v is not None:
            total_energy = v
            break

    return {
        # ── Ambient sensor ──
        "ambient": {
            "temperature": {"title": "Teplota (vnútri)",  "value": amb.get("temperature", amb.get("temp", "--")),    "unit": "°C",   "icon": "thermometer", "source": 1, "key": "temperature"},
            "humidity":    {"title": "Vlhkosť (vnútri)",  "value": amb.get("humidity",    amb.get("hum", "--")),     "unit": "%",    "icon": "droplet",     "source": 1, "key": "humidity"},
            "co2":         {"title": "CO₂",               "value": amb.get("co2",         amb.get("CO2", "--")),     "unit": "ppm",  "icon": "wind",        "source": 1, "key": "co2"},
            "pressure":    {"title": "Tlak (vnútri)",     "value": amb.get("pressure",    "--"),                     "unit": "hPa",  "icon": "gauge",       "source": 1, "key": "pressure"},
        },
        # ── Power Meter ──
        "power": {
            "raw":         pwr,   # surové dáta pre frontend
            "source":      2,
            "total_energy": {"title": "Súhrnná spotreba",  "value": total_energy,                                    "unit": "kWh",  "icon": "zap",         "source": 2},
        },
        # ── Lux sensor ──
        "lux": {
            "lux":         {"title": "Intenzita svetla",  "value": lux.get("lux", lux.get("LUX", "--")),            "unit": "lx",   "icon": "sun",         "source": 3, "key": "lux"},
        },
        # ── Door sensor ──
        "door": {
            "state":       {"title": "Dvere (IT učebňa)", "value": door.get("state", door.get("STATE", "--")),      "unit": "",     "icon": "door-closed", "source": 8, "key": "state"},
            "timestamp":   door.get("timestamp", "--"),
        },
    }

# ── /api/history/{source} – História pre graf ────────────────────────────────
@app.get("/api/history/{source}")
async def get_history(source: int, limit: int = 500):
    async with httpx.AsyncClient() as client:
        data = await fetch(client, source, limit)
    rows = data.get("rows", []) if isinstance(data, dict) else []
    # Chronologicky vzostupne pre grafy
    return {"rows": list(reversed(rows)), "columns": data.get("columns", [])}
