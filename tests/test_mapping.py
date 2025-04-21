import io

import pytest
from unittest.mock import patch
from starlette.testclient import TestClient
from PIL import Image

import os
import sys
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(project_root, "backend", "mapping"))

from backend.mapping.main import app

client = TestClient(app)


@pytest.fixture
def mock_map():
    img = Image.new('RGB', (100, 100), color='red')
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return buffer.getvalue(), img


def test_map(mock_map):
    sw_lat = 53.15
    sw_lon = -0.64
    ne_lat = 53.26
    ne_lon = -0.46
    data, img = mock_map

    with patch("backend.mapping.main.get_map") as mock_get_map:
        mock_get_map.return_value = (img, ((sw_lat, sw_lon), (ne_lat, ne_lon)))

        response = client.get("/map", params={
            "sw_lat": sw_lat,
            "sw_lon": sw_lon,
            "ne_lat": ne_lat,
            "ne_lon": ne_lon
        })

        assert response.status_code == 200
        assert response.headers["Content-Type"] == "image/png"
        assert response.headers["Extent"] == f"{sw_lon},{sw_lat},{ne_lon},{ne_lat}"
        assert response.content.startswith(b"\x89PNG")


# Missing either everything or some of the parameters
@pytest.mark.parametrize("missing", ["/", "/?x=1", "/?x=1&y=1"])
def test_validation(missing):
    response = client.get(missing)
    assert response.status_code == 422

