import json
import asyncio
import requests

from fastapi import FastAPI, Query
from fastapi.responses import Response

from haversine import haversine, Unit

app = FastAPI()

# ADSB source has a 1 per second rate limit, so globally delay requests to avoid being blocked
rate_limit_lock = asyncio.Lock()
last_request_time = 0

# TODO: Retain information about adsb for later use in a LRU cache


# airplanes.live has a 1 request per second rate limit, so this will wait for 1 second between requests
async def adsb_request(url: str, delay: float = 1.0):
    global last_request_time

    # TODO: Make this more complex to maybe take the latest from each user to avoid too much zooming causing issue

    async with rate_limit_lock:
        while True:
            current_time = asyncio.get_event_loop().time()
            if current_time - last_request_time > delay:
                last_request_time = current_time
                return requests.get(url)
            await asyncio.sleep(0.1)


@app.get("/radius")
async def fetch_radius(sw_lat: float = Query(...), sw_lon: float = Query(...),
                       ne_lat: float = Query(...), ne_lon: float = Query(...)):

    central_lat = (sw_lat + ne_lat) / 2
    central_lon = (sw_lon + ne_lon) / 2
    max_radius = haversine((sw_lat, sw_lon), (ne_lat, ne_lon), unit=Unit.NAUTICAL_MILES) / 2

    url = f"https://api.airplanes.live/v2/point/{central_lat}/{central_lon}/{max_radius}"
    aircraft_response = await adsb_request(url)
    content = aircraft_response.json()

    return Response(content=json.dumps(content), media_type="application/json")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
