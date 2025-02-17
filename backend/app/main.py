import json
import os
import httpx
import requests

from fastapi import FastAPI, Query
from fastapi.responses import Response, FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "frontend", "index")), name="static")

MAPPING_URL = os.getenv("MAPPING_URL")
AUTH_URL = os.getenv("AUTH_URL")


@app.get("/", response_class=FileResponse)
async def fetch_index():
    index_path = os.path.join(os.path.dirname(__file__), "frontend", "index", "index.html")
    return FileResponse(index_path)


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

    return Response(content=response.content, media_type="image/png", headers=response.headers)


@app.post("/signup")
async def register(email: str = Query(...), password: str = Query(...)):

    params = {
        "email": email,
        "password": password
    }

    signup_url = f"{AUTH_URL}/auth/register"
    response = requests.post(signup_url, json=params)

    # TODO: Probably want to re-pack the response to be more user-friendly
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

    params = {
        "username": email,
        "password": password
    }

    # Get a token and prepare to return
    token_url = f"{AUTH_URL}/auth/jwt/login"
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
