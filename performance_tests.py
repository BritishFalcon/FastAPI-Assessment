import time
import asyncio
import httpx
from tqdm import tqdm
import pandas as pd

endpoints = {
    "/auth/me": None,
    "/auth/balance": None,
    "/map/": {
        "sw_lat": 53.15,
        "sw_lon": -0.64,
        "ne_lat": 53.26,
        "ne_lon": -0.46
    },
    "/map/tile": {
        "zoom": 10,
        "x": 510,
        "y": 332,
    },
    "/adsb/radius": {
        "sw_lat": 51.435,
        "sw_lon": -0.519,
        "ne_lat": 51.514,
        "ne_lon": -0.376
    },
    "/adsb/hex": None,
}


def _simplify_hex(endpoint):
    if endpoint.startswith("/adsb/hex"):
        return "/adsb/hex?image=true" if "image=true" in endpoint else "/adsb/hex"
    else:
        return endpoint


async def test(client: httpx.AsyncClient, endpoints):
    results = {}
    hex_code = None

    # INITIALISATION
    start = time.perf_counter()
    response = await client.post("/auth/register", json={"email": "test@example.com", "password": "test"})
    timer = time.perf_counter() - start
    results["/auth/register"] = (timer, response.status_code)

    start = time.perf_counter()
    response = await client.post("/auth/login", data={"username": "test@example.com", "password": "test"})
    timer = time.perf_counter() - start
    results["/auth/login"] = (timer, response.status_code)
    jwt = response.json().get("access_token")
    headers = {"Authorization": f"Bearer {jwt}"}
    # END INITIALISATION

    for endpoint, data in endpoints.items():
        if endpoint == "/adsb/hex":
            url = f"{endpoint}?hex={hex_code}"
            start = time.perf_counter()
            response = await client.get(url, headers=headers)
            timer = time.perf_counter() - start
            results[url] = (timer, response.status_code)

            await asyncio.sleep(1)

            url_img = f"{endpoint}?hex={hex_code}&image=true"
            start = time.perf_counter()
            response = await client.get(url_img, headers=headers)
            timer = time.perf_counter() - start
            results[url_img] = (timer, response.status_code)

            await asyncio.sleep(1)

        else:
            start = time.perf_counter()
            response = await client.get(endpoint, params=data, headers=headers)
            timer = time.perf_counter() - start

            if response.status_code == 405:
                start = time.perf_counter()
                response = await client.post(endpoint, json=data, headers=headers)
                timer = time.perf_counter() - start

            results[endpoint] = (timer, response.status_code)

        if response.status_code != 200:
            print(f"Error: {response.text}")
            continue

        if endpoint == "/adsb/radius":
            json_resp = response.json()
            if "ac" in json_resp:
                hex_code = json_resp["ac"][0]["hex"]
                await asyncio.sleep(1)

    return results


async def main():
    address_results = {}
    addresses = ["http://localhost", "https://adsb.bengriffiths.uk"]

    for address in addresses:
        run_results = []
        # Use a single AsyncClient for all requests to reuse connections
        async with httpx.AsyncClient(base_url=address, timeout=10.0) as client:
            for _ in tqdm(range(10), desc=f"Testing {address}", unit="run"):
                results = await test(client, endpoints)
                run_results.append(results)
        address_results[address] = run_results

    # Prepare pandas output
    pd.options.display.width = 1200
    pd.options.display.max_colwidth = 100
    pd.options.display.max_columns = 100

    rows = []
    for address, runs in address_results.items():
        for run_idx, run in enumerate(runs):
            for endpoint, (elapsed, status_code) in run.items():
                elapsed_ms = round(elapsed * 1000, 2)
                rows.append({
                    "run": run_idx,
                    "address": address,
                    "endpoint": _simplify_hex(endpoint),
                    "elapsed": elapsed_ms,
                    "status_code": status_code,
                })

    df = pd.DataFrame(rows)
    summary = (
        df.groupby(["address", "endpoint"])
        .agg(
            mean_latency=("elapsed", "mean"),
            std_latency=("elapsed", "std"),
            min_latency=("elapsed", "min"),
            max_latency=("elapsed", "max"),
            runs=("elapsed", "count"),
        )
        .reset_index()
    )

    print(df)
    print("\n\n")
    print(summary)

    df.to_csv("performance_test_results.csv", index=False)
    summary.to_csv("performance_test_summary.csv", index=False)

if __name__ == "__main__":
    asyncio.run(main())
