import json
import requests

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

# TODO: Remove deprecated functions that have been offloaded via NGINX

app = FastAPI(root_path="/api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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

            ac_data_url = f"http://adsb/radius"
            response = requests.get(ac_data_url, params=params)
            response_json = response.json()
            await websocket.send_text(json.dumps(response_json))
            
        except WebSocketDisconnect:
            break

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
