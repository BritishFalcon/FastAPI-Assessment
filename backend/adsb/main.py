import json
import asyncio
import threading

import requests

from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import Response

from haversine import haversine, Unit

from cachetools import LRUCache

app = FastAPI(root_path="/adsb")

# ADSB source has a 1 per second rate limit, so globally delay requests to avoid being blocked
rate_limit_lock = asyncio.Lock()
last_request_time = 0

hex_cache = LRUCache(maxsize=16000)
cache_lock = threading.Lock()


def update_cache(aircraft):
    with cache_lock:
        hex_cache.update({aircraft["hex"]: aircraft})


# airplanes.live has a 1 request per second rate limit, so this will wait for 1 second between requests
async def adsb_request(url: str, delay: float = 1.0):
    global last_request_time
    async with rate_limit_lock:
        while True:
            current_time = asyncio.get_event_loop().time()
            if current_time - last_request_time > delay:
                last_request_time = current_time
                return requests.get(url)
            else:
                await asyncio.sleep(delay - (current_time - last_request_time))


@app.get("/radius")
async def fetch_radius(sw_lat: float = Query(...), sw_lon: float = Query(...),
                       ne_lat: float = Query(...), ne_lon: float = Query(...)):

    central_lat = (sw_lat + ne_lat) / 2
    central_lon = (sw_lon + ne_lon) / 2
    max_radius = haversine((sw_lat, sw_lon), (ne_lat, ne_lon), unit=Unit.NAUTICAL_MILES) / 2

    url = f"https://api.airplanes.live/v2/point/{central_lat}/{central_lon}/{max_radius}"
    aircraft_response = await adsb_request(url)

    if aircraft_response.status_code != 200:
        raise HTTPException(status_code=aircraft_response.status_code, detail=aircraft_response.text)

    content = aircraft_response.json()

    filtered_content = {"ac": []}
    for aircraft in content["ac"]:

        # Offload this to a separate thread as it's a secondary task
        threading.Thread(target=lambda: update_cache(aircraft)).start()

        # Some military aircraft don't seem to fill track, wacky
        if "track" in aircraft:
            track = aircraft["track"]
        else:
            try:
                track = aircraft["calc_track"]
            except KeyError:
                continue

        flight = aircraft["flight"] if "flight" in aircraft else "N/A"

        try:
            # Expecting a KeyError and skip here if there really is no data
            lat = aircraft["lat"] if "lat" in aircraft else aircraft["lastPosition"]["lat"]
            lon = aircraft["lon"] if "lon" in aircraft else aircraft["lastPosition"]["lon"]

            subset = {
                "hex": aircraft["hex"],
                "lat": lat,
                "lon": lon,
                "track": track,
                "flight": flight,
            }
            filtered_content["ac"].append(subset)
        except KeyError:
            print("ERROR: Missing key in aircraft data")
            print(json.dumps(aircraft, indent=4))

    return Response(content=json.dumps(filtered_content), media_type="application/json")


@app.get("/hex")
async def fetch_hex(hex: str = Query(...), image: bool = Query(False)):

    hex_list = [h.strip() for h in hex.split(",") if h.strip()]
    if not hex_list:
        raise HTTPException(status_code=400, detail="No hex provided.")

    if image and len(hex_list) > 1:
        raise HTTPException(status_code=400, detail="Image only supported for a single hex.")

    results = {}
    missing = []

    with cache_lock:
        for h in hex_list:
            if h in hex_cache:
                results[h] = hex_cache[h]
            else:
                missing.append(h)

    # Only use API for missing hexes
    if missing:
        url = f"https://api.airplanes.live/v2/hex/{','.join(missing)}"
        aircraft_response = await adsb_request(url)

        if aircraft_response.status_code != 200:
            raise HTTPException(status_code=aircraft_response.status_code, detail=aircraft_response.text)

        try:
            new_data = aircraft_response.json()["ac"]
        except (KeyError, IndexError):
            raise HTTPException(status_code=404, detail="No aircraft found with the given hex values.")

        for ac in new_data:
            h = ac.get("hex")
            if h:
                with cache_lock:
                    hex_cache[h] = ac
                results[h] = ac

    values_to_keep = ["r", "t", "dbFlags", "gs", "ias", "tas", "desc", "alt_baro", "alt_geom", "seen"]

    # Maintains original format, easier for backward-compat with the frontend code
    if len(hex_list) == 1:
        hex_val = hex_list[0]
        content = results.get(hex_val)
        if not content:
            raise HTTPException(status_code=404, detail="No aircraft found with that hex.")

        filtered_content = {key: content.get(key, None) for key in values_to_keep}

        if image:
            image_url = f"https://airport-data.com/api/ac_thumb.json?m={hex_val}"
            image_response = await adsb_request(image_url)

            if image_response.status_code == 200:
                try:
                    filtered_content["image"] = image_response.json()["data"][0]["image"]
                except (IndexError, KeyError):
                    filtered_content["image"] = None
            else:
                filtered_content["image"] = None

        return Response(content=json.dumps(filtered_content), media_type="application/json")

    # Multiple hexes output
    output = []
    for h in hex_list:
        if h in results:
            ac = results[h]
            output.append({key: ac.get(key, None) for key in values_to_keep})

    return Response(content=json.dumps(output), media_type="application/json")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)