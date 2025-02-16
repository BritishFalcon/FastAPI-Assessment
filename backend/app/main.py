import os
import httpx

from fastapi import FastAPI, Query
from fastapi.responses import Response, FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "frontend", "index")), name="static")

MAPPING_URL = "http://localhost:8001/map"


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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
