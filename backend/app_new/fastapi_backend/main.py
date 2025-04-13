import asyncio
import json
import os
import httpx
import requests

from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import Response, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.testing.plugin.plugin_base import logging

app = FastAPI()
# app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "frontend", "index")), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MAPPING_URL = os.getenv("MAPPING_URL", "http://localhost:8006")
AUTH_URL = os.getenv("AUTH_URL", "http://localhost:8004")
ADSB_URL = os.getenv("ADSB_URL", "http://localhost:8001")


# This needs to be moved to WebSockets for real-time updates
@app.get("/map")
async def fetch_map(sw_lat: float = Query(...), sw_lon: float = Query(...),
                    ne_lat: float = Query(...), ne_lon: float = Query(...)):

    params = {
        "sw_lat": sw_lat,
        "sw_lon": sw_lon,
        "ne_lat": ne_lat,
        "ne_lon": ne_lon
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(MAPPING_URL, params=params)

    headers = dict(response.headers)
    headers["Access-Control-Expose-Headers"] = "Extent"

    return Response(content=response.content, media_type="image/png", headers=headers)


def _login(email: str, password: str):
    params = {
        "username": email,
        "password": password
    }

    # Get a token and prepare to return
    token_url = f"{AUTH_URL}/auth/jwt/leaflet"
    response = requests.post(token_url, data=params)

    if not response.ok:
        content = response.json()
        match response.status_code:
            case 422:
                error = content['detail'][0]['msg']
            case 400:
                error = content['detail']
            case _:
                error = "Undefined Error"
        return Response(content=error, status_code=response.status_code)

    return Response(content=response.content, media_type="application/json", headers=response.headers)


@app.post("/signup")
async def register(email: str = Query(...), password: str = Query(...)):

    params = {
        "email": email,
        "password": password
    }

    signup_url = f"{AUTH_URL}/auth/register"
    response = requests.post(signup_url, json=params)

    if not response.ok:
        content = response.json()
        match response.status_code:
            case 422:
                error = content['detail'][0]['msg']
            case 400:
                error = content['detail']
            case _:
                error = "Undefined Error"
        return Response(content=error, status_code=response.status_code)

    return _login(email, password)


@app.post("/login")
async def login(email: str = Query(...), password: str = Query(...)):
    return _login(email, password)


@app.get("/validate")
async def validate(token: str = Query(...)):

    headers = {"Authorization": f"Bearer {token}"}
    validate_url = f"{AUTH_URL}/users/me"
    response = requests.get(validate_url, headers=headers)

    content = response.json()
    print(json.dumps(content, indent=4))

    if not response.ok:
        content = response.json()
        match response.status_code:
            case 422:
                error = content['detail'][0]['msg']
            case 400:
                error = content['detail']
            case _:
                error = "Undefined Error"
        return Response(content=error, status_code=response.status_code)

    return Response(content=response.content, media_type="application/json", headers=response.headers)


@app.websocket("/ws/aircraft")
async def aircraft_ws(websocket: WebSocket):
    await websocket.accept()
    while True:
        try:
            data = await websocket.receive_text()
            bounds = json.loads(data)

            params = {
                "sw_lat": bounds["sw_lat"],
                "sw_lon": bounds["sw_lon"],
                "ne_lat": bounds["ne_lat"],
                "ne_lon": bounds["ne_lon"]
            }

            ac_data_url = f"{ADSB_URL}/radius"
            response = requests.get(ac_data_url, params=params)
            response_json = response.json()
            # TODO: Repack JSON to simplify the data

            await websocket.send_text(json.dumps(response_json))
        except WebSocketDisconnect:
            break


@app.get("/hex")
async def fetch_hex(hex: str = Query(...)):
    url = f"{ADSB_URL}/hex"
    params = {"hex": hex}
    response = requests.get(url, params=params)
    return Response(content=response.content, media_type="application/json", headers=response.headers)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
