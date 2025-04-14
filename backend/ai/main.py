import base64
import json
import os

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from pydantic import BaseModel
from openai import OpenAI

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MAPPING_PORT = os.getenv("MAPPING_PORT", "8006")
ADSB_PORT = os.getenv("ADSB_PORT", "8001")
MODEL = "gpt-4.1-mini"

app = FastAPI()
client = OpenAI(api_key=OPENAI_API_KEY)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to your domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SummaryInput(BaseModel):
    question: str
    sw_lat: float
    sw_lon: float
    ne_lat: float
    ne_lon: float


async def fetch_image(image_url: str) -> str:
    async with httpx.AsyncClient() as async_client:
        response = await async_client.get(image_url)
        response.raise_for_status()
        return base64.b64encode(response.content).decode("utf-8")


async def fetch_json(ac_url: str) -> dict:
    async with httpx.AsyncClient() as async_client:
        response = await async_client.get(ac_url)
        response.raise_for_status()
        return response.json()


@app.post("/summary")
async def get_summary(data: SummaryInput):
    question = data.question
    sw_lat = data.sw_lat
    sw_lon = data.sw_lon
    ne_lat = data.ne_lat
    ne_lon = data.ne_lon

    aircraft_url = f"http://adsb:{ADSB_PORT}/radius?sw_lat={sw_lat}&sw_lon={sw_lon}&ne_lat={ne_lat}&ne_lon={ne_lon}"
    aircraft = await fetch_json(aircraft_url)

    # Print the aircraft data for debugging
    print(aircraft)

    if not aircraft:
        return Response(content="There are no aircraft in the area.", media_type="text/plain")

    image_url = f"http://mapping:{MAPPING_PORT}/?sw_lat={sw_lat}&sw_lon={sw_lon}&ne_lat={ne_lat}&ne_lon={ne_lon}"
    image = await fetch_image(image_url)

    context = [
        {"role": "system", "content": "You are a Flight Radar summarisation agent. You will be provided with the image of a map (which does not include aircraft icons) and a JSON of all the aircraft in the area. You will be asked summary questions from the user about the image and the JSON. Note the location from the map, and what aircraft are in the area, and what they are doing. You should try use your aviation and military knowledge of the aircraft to try answer questions about what a given aircraft is likely to be doing given its situation and position."},
        {"role": "system", "content": "You can use your get_aircraft_info tool in order to get more information about specific aircraft(s). You may only do this once per chat turn. Do not ask the user first, just use it as you see fit. Try to focus on specific aircraft rather than entering a huge amount of data."},
        {"role": "system", "content": "Always refer to specific aircraft by their flight name/number, rather than their hex number. Never ask the user questions. Always provide direct, conclusive answers to the user. Always use tools if necessary."},
        {"role": "system", "content": str(aircraft)},
        {"role": "user", "content": question},
    ]

    if image:
        context.append({
            "role": "user",
            "content": [
                {
                    "type": "input_image",
                    "image_url": f"data:image/png;base64,{image}",
                }
            ]
        })
    else:
        print("Failed to fetch image from mapping service.")

    tools = [{
        "type": "function",
        "name": "get_aircraft_info",
        "description": "Get more information about aircraft from their 'hex' number. Separate multiple hex numbers with commas.",
        "parameters": {
            "type": "object",
            "properties": {
                "hex": {"type": "string", "description": "The hex number of aircraft, comma seperated."},
            },
            "required": ["hex"],
            "additionalProperties": False
        },
        "strict": True
    }]

    response = client.responses.create(
        model=MODEL,
        input=context,
        tools=tools,
    )

    if response.output[0].type == "function_call":
        # We only have one available function right now, so no need to check which one it is
        tool_call = response.output[0]
        args = json.loads(tool_call.arguments)
        hex_number = args["hex"]

        hex_url = f"http://adsb:{ADSB_PORT}/hex?hex={hex_number}"
        aircraft_info = await fetch_json(hex_url)

        context.append(tool_call)
        context.append({
            "type": "function_call_output",
            "call_id": tool_call.call_id,
            "output": str(aircraft_info),
        })

        response = client.responses.create(
            model=MODEL,
            input=context,
        )

    if response:
        return Response(content=response.output_text, media_type="text/plain")
    else:
        return HTTPException(status_code=500, detail="Failed to get a response from AI.")
