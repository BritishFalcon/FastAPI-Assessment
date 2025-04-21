import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from httpx import AsyncClient, ASGITransport
import uuid
from fastapi import HTTPException

# Does not work without this
import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(project_root, "backend", "ai"))

from backend.ai.main import app, deduct_credits


def get_client():
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.mark.asyncio
@patch("backend.ai.db.httpx.AsyncClient")
async def test_deduct_credits_success(mock_client):
    fake_resp = AsyncMock(status_code=200)
    fake_resp.json = MagicMock(return_value={"remaining_credits": 75})

    # This got confusing, but it works using https://stackoverflow.com/questions/70633584/how-to-mock-httpx-asyncclient-in-pytest
    client = mock_client.return_value.__aenter__.return_value
    client.post.return_value = fake_resp

    user_id = uuid.uuid4()
    result = await deduct_credits(user_id, 25)

    assert result["remaining_credits"] == 75


@pytest.mark.asyncio
@patch("backend.ai.db.httpx.AsyncClient")
async def test_deduct_credits_insufficient(mock_client):
    fake_resp = AsyncMock(status_code=400)
    fake_resp.text = "Not enough credits"

    client = mock_client.return_value.__aenter__.return_value
    client.post.return_value = fake_resp

    user_id = uuid.uuid4()

    with pytest.raises(HTTPException) as exception:
        await deduct_credits(user_id, 25)

    assert exception.value.status_code == 400
    assert exception.value.detail == "Not enough credits"


@pytest.mark.asyncio
async def test_summary_unauthenticated():
    payload = {
        "sw_lat": 53.15,
        "sw_lon": -0.64,
        "ne_lat": 53.26,
        "ne_lon": -0.46,
        "question": "Why are there so many planes?",
    }
    async with get_client() as ac:
        response = await ac.post("/ai/summary", json=payload, headers={"Authorization": ""})
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_summary_erroneous():
    # NE and SW are flipped here, so the dimensions are inside-out
    # This also covers the Pydantic validation test, as that should fail BEFORE authentication
    payload = {
        "ne_lat": 53.15,
        "ne_lon": -0.64,
        "sw_lat": 53.26,
        "sw_lon": -0.46,
        "question": "Why are there so many planes?",
    }
    async with get_client() as ac:
        response = await ac.post("/ai/summary", json=payload, headers={"Authorization": ""})
        assert response.status_code == 422
