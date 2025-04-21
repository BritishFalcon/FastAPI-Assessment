import pytest
from unittest.mock import patch
from starlette.testclient import TestClient
import json

# Does not work without this
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.api.main import app


@pytest.mark.asyncio
@patch("backend.api.main.requests.get")
async def test_aircraft_ws(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {
        "ac": [
            {"hex": "ABC123", "lat": 53.15, "lon": -0.64},
            {"hex": "DEF456", "lat": 53.26, "lon": -0.46}
        ]
    }

    client = TestClient(app)
    with client.websocket_connect("/ws/aircraft") as ws:
        bounds = {
            "sw_lat": 53.15,
            "sw_lon": -0.64,
            "ne_lat": 53.26,
            "ne_lon": -0.46
        }
        ws.send_text(json.dumps(bounds))

        data = ws.receive_text()
        response = json.loads(data)

        assert response["ac"][0]["hex"] == "ABC123"
        assert len(response["ac"]) == 2
