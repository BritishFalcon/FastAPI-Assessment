import os
import io

from fastapi import FastAPI, Query
from fastapi.responses import Response

from osm_stitcher import get_map, get_tile

OSM_API_KEY = os.getenv("OSM_API_KEY")

app = FastAPI(root_path="/map")


# This needs to be moved to WebSockets for real-time updates
@app.get("/")
# Async is NOT used here, as this ensures the function is offloaded to a separate thread due to the blocking nature
# of this relatively slow and I/O-bound function.
def fetch_map(sw_lat: float = Query(...), sw_lon: float = Query(...),
                        ne_lat: float = Query(...), ne_lon: float = Query(...)):

    sw = (sw_lat, sw_lon)
    ne = (ne_lat, ne_lon)
    img, (sw_new, ne_new) = get_map(sw, ne, API_KEY=OSM_API_KEY)

    img_byte_array = io.BytesIO()
    img.save(img_byte_array, format='PNG')
    img_byte_array.seek(0)

    headers = {"Extent": f"{sw_new[1]},{sw_new[0]},{ne_new[1]},{ne_new[0]}"}
    return Response(content=img_byte_array.getvalue(), media_type="image/png", headers=headers)


@app.get("/tile")
def fetch_tile(x: int = Query(...), y: int = Query(...), zoom: int = Query(...)):
    img = get_tile(x, y, zoom, API_KEY=OSM_API_KEY)

    img_byte_array = io.BytesIO()
    img.save(img_byte_array, format='PNG')
    img_byte_array.seek(0)

    return Response(content=img_byte_array.getvalue(), media_type="image/png")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=True)
