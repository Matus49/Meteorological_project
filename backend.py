import os
import logging
import httpx
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

# Nastavenie logovania pre lepšiu diagnostiku na Renderi
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("GaiaSenzorAPI")

app = FastAPI(title="GaiaSenzor Production API", version="2.1.0")

# CORS middleware pre komunikáciu
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

API_BASE_URL = "https://projekttb.sksnr.sk/data/api.php"
API_AUTH = ("sks", "kolbe")

def get_fallback_data() -> Dict[str, Any]:
    """Definícia štruktúrovaných dát pre prípad výpadku."""
    return {
        "temperature": {"title": "Teplota vzduchu", "value": 0.0, "unit": "°C", "icon": "🌡️", "trend": "Offline"},
        "humidity": {"title": "Vlhkosť vzduchu", "value": 0, "unit": "%", "icon": "💧", "trend": "Offline"},
        "pressure": {"title": "Tlak", "value": 1000, "unit": "hPa", "icon": "⏱️", "trend": "Offline"},
        "temp_flower": {"title": "Teplota Kvet", "value": 0.0, "unit": "°C", "icon": "🌱", "trend": "Offline"},
        "hum_flower": {"title": "Vlhkosť Kvet", "value": 0, "unit": "%", "icon": "🪴", "trend": "Offline"}
    }

async def fetch_source(source_id: int) -> Dict[str, Any]:
    """Bezpečné stiahnutie dát z konkrétneho zdroja."""
    url = f"{API_BASE_URL}?source={source_id}&limit=1"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url, auth=API_AUTH)
            if response.status_code == 200:
                data = response.json()
                return data[0] if isinstance(data, list) and len(data) > 0 else {}
            logger.error(f"Source {source_id} vrátil kód {response.status_code}")
    except Exception as e:
        logger.error(f"Spojenie so zdrojom {source_id} zlyhalo: {str(e)}")
    return {}

@app.get("/api/dashboard")
async def get_dashboard():
    logger.info("Prijatá požiadavka na /api/dashboard")
    
    # Paralelné načítanie dát zo zdrojov
    s0 = await fetch_source(0)
    s1 = await fetch_source(1)
    
    # Ak sú oba zdroje prázdne, vrátime fallback
    if not s0 and not s1:
        logger.warning("Všetky zdroje offline, vraciam fallback dáta.")
        return get_fallback_data()
    
    # Mapovanie dát s ochranou proti chýbajúcim kľúčom
    return {
        "temperature": {
            "title": "Teplota vzduchu", 
            "value": s0.get("temp") or s0.get("temperature", 21.5), 
            "unit": "°C", "icon": "🌡️", "trend": "Aktívne"
        },
        "humidity": {
            "title": "Vlhkosť vzduchu", 
            "value": s0.get("humidity") or s0.get("hum", 55), 
            "unit": "%", "icon": "💧", "trend": "Aktívne"
        },
        "pressure": {
            "title": "Atmosférický tlak", 
            "value": s0.get("pressure") or s0.get("barometer", 1013), 
            "unit": "hPa", "icon": "⏱️", "trend": "Aktívne"
        },
        "temp_flower": {
            "title": "Teplota pri Kvete", 
            "value": s1.get("temp") or s1.get("temperature", 23.1), 
            "unit": "°C", "icon": "🌱", "trend": "Aktívne"
        },
        "hum_flower": {
            "title": "Vlhkosť pri Kvete", 
            "value": s1.get("humidity") or s1.get("hum", 48), 
            "unit": "%", "icon": "🪴", "trend": "Aktívne"
        }
    }

# Zdravotná kontrola pre Render
@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "GaiaSenzor-Core"}
