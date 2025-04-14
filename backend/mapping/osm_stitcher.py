import math
import threading
from concurrent.futures import ThreadPoolExecutor
from cachetools import LRUCache

import requests
from io import BytesIO
from PIL import Image

# Need to debug, but this should come under 16GB of RAM so plenty fine
# Using cachetools implementation for thread-safe LRU cache, as multiple clients could be requesting the same tile
cache = LRUCache(maxsize=16000)
cache_lock = threading.Lock()


# Borrowed from https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames
def deg2num(lat_deg, lon_deg, zoom):
    lat_rad = math.radians(lat_deg)
    n = 1 << zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return xtile, ytile


# Borrowed from https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames
def num2deg(xtile, ytile, zoom):
    n = 1 << zoom
    lon_deg = xtile / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
    lat_deg = math.degrees(lat_rad)
    return lat_deg, lon_deg


def calculate_zoom(sw, ne, target_width=1):
    lon_diff = ne[1] - sw[1]

    # Original equation from https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames
    # Re-arranging from: target_width = (lon_diff / 360) * 2^zoom
    zoom_float = math.log2((target_width * 360) / lon_diff)

    # Round to the nearest integer zoom level
    zoom = int(round(zoom_float))
    return zoom


def get_tile(x, y, zoom, API_KEY=None):

    assert API_KEY is not None, "Tracestack API_KEY must be provided to fetch tiles!"

    with cache_lock:
        if (zoom, x, y) in cache:
            return cache[(zoom, x, y)]

    url = f"https://tile.tracestrack.com/_/{zoom}/{x}/{y}.png?key={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        img = Image.open(BytesIO(response.content))

        with cache_lock:
            cache[(zoom, x, y)] = img

        return img

    else:
        print(f"Failed to fetch tile {zoom}/{x}/{y}, status code: {response.status_code}")
        return None


def get_map(sw, ne, zoom=None, tile_size=512, API_KEY=None):

    assert API_KEY is not None, "Tracestack API_KEY must be provided to fetch tiles!"

    # Experimental, as PIL isn't known thread-safe, but it appears to work as there is no overlap
    def add_tile(x, y):
        nonlocal zoom, start_x, start_y, API_KEY  # Only for explicitness
        tile = get_tile(x, y, zoom, API_KEY=API_KEY)
        if tile is not None:
            map_img.paste(tile, ((x - start_x) * tile_size, (y - start_y) * tile_size))
        else:
            print(f"Failed to fetch tile {zoom}/{x}/{y}")

    # Some elements from https://stackoverflow.com/questions/28476117/easy-openstreetmap-tile-displaying-for-python
    zoom = calculate_zoom(sw, ne) if zoom is None else zoom
    (start_x, end_y) = deg2num(sw[0], sw[1], zoom)
    (end_x, start_y) = deg2num(ne[0], ne[1], zoom)

    map_img = Image.new('RGB', ((end_x - start_x + 1) * tile_size, (end_y - start_y + 1) * tile_size))

    required_tiles = [(x, y) for x in range(start_x, end_x + 1) for y in range(start_y, end_y + 1)]

    with ThreadPoolExecutor(max_workers=32) as executor:
        executor.map(lambda args: add_tile(*args), required_tiles)

    sw_new = num2deg(start_x, start_y, zoom)
    ne_new = num2deg(end_x + 1, end_y + 1, zoom)

    return map_img, (sw_new, ne_new)


if __name__ == "__main__":
    sw = (53.222825, -0.561362)
    ne = (53.230539, -0.542218)
    resolution = (1920, 1080)

    composite_img, extent = get_map(sw, ne)
    composite_img.save("composite_map.png")
