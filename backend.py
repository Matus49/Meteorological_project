import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import httpx

logging.basicConfig(level=logging.INFO)
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

API_BASE_URL = "https://projekttb.sksnr.sk/data/api.php"
AUTH = ("sks", "kolbe")

async def get_data(source, limit):
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{API_BASE_URL}?source={source}&sort=timestamp&dir=desc&limit={limit}", auth=AUTH)
            return r.json() if r.status_code == 200 else []
    except Exception as e:
        print(f"Chyba pri source {source}: {e}")
        return []

@app.get("/api/dashboard")
async def get_dashboard():
    # Sťahujeme aktuálne dáta a históriu pre oba zdroje
    out_curr = await get_data(0, 1)
    out_hist = await get_data(0, 500)
    in_curr = await get_data(1, 1)
    in_hist = await get_data(1, 500)

    return {
        "outside": {
            "current": out_curr[0] if out_curr else {"temp": 0, "humidity": 0},
            "history": out_hist
        },
        "classroom": {
            "current": in_curr[0] if in_curr else {"temp": 0, "humidity": 0},
            "history": in_hist
        }
    }
