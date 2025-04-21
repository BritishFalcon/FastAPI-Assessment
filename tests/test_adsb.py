import pytest
from unittest.mock import patch, MagicMock
from httpx import AsyncClient, ASGITransport

# Does not work without this
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.adsb.main import app
from examples.airplanes_live import POINT, HEX_SINGLE, HEX_MULTIPLE


# Patch is used to prevent issues arising from rate limits during testing (e.g Airplanes.live is 1Hz)
def get_client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.asyncio
@patch("backend.adsb.main.adsb_request")
async def test_radius(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = POINT
    mock_get.return_value = mock_response

    async with get_client() as ac:
        response = await ac.get("/radius", params={
            "sw_lat": 53.15,
            "sw_lon": -0.64,
            "ne_lat": 53.26,
            "ne_lon": -0.46
        })
        assert response.status_code == 200
        data = response.json()
        assert "ac" in data
        assert len(data["ac"]) == 1


@pytest.mark.asyncio
@patch("backend.adsb.main.adsb_request")
async def test_radius_failure(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 503
    mock_response.text = "Service Unavailable"
    mock_get.return_value = mock_response

    async with get_client() as ac:
        response = await ac.get("/radius", params={
            "sw_lat": 53.15,
            "sw_lon": -0.64,
            "ne_lat": 53.26,
            "ne_lon": -0.46
        })
        assert response.status_code == 503


@pytest.mark.asyncio
@patch("backend.adsb.main.adsb_request")
async def test_hex(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = HEX_SINGLE
    mock_get.return_value = mock_response
    hex_id = "494112"

    async with get_client() as ac:
        response = await ac.get("/hex", params={"hex": hex_id})
        assert response.status_code == 200
        data = response.json()
        assert data["desc"] == "EMBRAER EMB-505 Phenom 300"


@pytest.mark.asyncio
@patch("backend.adsb.main.adsb_request")
async def test_hex_multiple(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = HEX_MULTIPLE
    mock_get.return_value = mock_response
    hex_ids = "494112,45211e"

    async with get_client() as ac:
        response = await ac.get("/hex", params={"hex": hex_ids})
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2


@pytest.mark.asyncio
async def test_hex_missing():
    async with get_client() as ac:
        response = await ac.get("/hex")
        assert response.status_code == 422


@pytest.mark.asyncio
@patch("backend.adsb.main.adsb_request")
async def test_hex_failure(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 503
    mock_response.text = "Service Unavailable"
    mock_get.return_value = mock_response
    hex_id = "407446"

    async with get_client() as ac:
        response = await ac.get("/hex", params={"hex": hex_id})
        assert response.status_code == 503