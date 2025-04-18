import base64
import json
import os

import aioredis
import httpx
from db import deduct_credits

from openai import AsyncClient as OpenAI

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMAILS_ENABLED = os.getenv("EMAILS_ENABLED", "false").lower() == "true"
REDIS_URL = "redis://redis:6379"
MODEL = "gpt-4.1-mini"

client = OpenAI(api_key=OPENAI_API_KEY)
redis = aioredis.from_url(REDIS_URL, decode_responses=True)


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


async def get_summary(
        question: str,
        sw_lat: float,
        sw_lon: float,
        ne_lat: float,
        ne_lon: float,
):

    aircraft_url = f"http://adsb/radius?sw_lat={sw_lat}&sw_lon={sw_lon}&ne_lat={ne_lat}&ne_lon={ne_lon}"
    aircraft = await fetch_json(aircraft_url)

    if not aircraft:
        print("No aircraft data found.")
        return "There are no aircraft in the area."

    image_url = f"http://mapping/?sw_lat={sw_lat}&sw_lon={sw_lon}&ne_lat={ne_lat}&ne_lon={ne_lon}"
    image = await fetch_image(image_url)

    context = [
        {"role": "system", "content": "You are a Flight Radar summarisation agent. You will be provided with the image of a map (which does not include aircraft icons) and a JSON of all the aircraft in the area. You will be asked summary questions from the user about the image and the JSON. Note the location from the map, and what aircraft are in the area, and what they are doing. You should try use your aviation and military knowledge of the aircraft to try answer questions about what a given aircraft is likely to be doing given its situation and position."},
        {"role": "system", "content": "You can use your get_aircraft_info tool in order to get more information about specific aircraft(s). You may only do this once per chat turn. Do not ask the user first, just use it as you see fit. Try to focus on specific aircraft rather than entering a huge amount of data."},
        {"role": "system", "content": "Always refer to specific aircraft by their FLIGHT NAME, rather than their hex number. Never ask the user questions. Always provide direct, conclusive answers to the user. Always use tools if necessary."},
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
    else:  # Non-critical, so don't stop but do log.
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

    response = await client.responses.create(
        model=MODEL,
        input=context,
        tools=tools,
    )

    if response.output[0].type == "function_call":
        # We only have one available function right now, so no need to check which one it is
        tool_call = response.output[0]
        args = json.loads(tool_call.arguments)
        hex_number = args["hex"]

        hex_url = f"http://adsb/hex?hex={hex_number}"
        aircraft_info = await fetch_json(hex_url)

        context.append(tool_call)
        context.append({
            "type": "function_call_output",
            "call_id": tool_call.call_id,
            "output": str(aircraft_info),
        })

        response = await client.responses.create(
            model=MODEL,
            input=context,
        )

    return response.output_text


async def queue_worker():
    while True:
        try:
            _, job = await redis.blpop("ai_queue")
            job = json.loads(job)
            job_id = job["job_id"]

            try:
                print("Processing job:", job_id)
                result = await get_summary(
                    question=job["question"],
                    sw_lat=job["sw_lat"],
                    sw_lon=job["sw_lon"],
                    ne_lat=job["ne_lat"],
                    ne_lon=job["ne_lon"],
                )
            except Exception as e:
                print(f"Error processing job {job_id}: {e}")
                await deduct_credits(job["user_id"], -25)  # Refund on error
                result = None

            print("Finished job:", job_id)
            print("Result:", result)

            channel = f"job_{job_id}"
            payload = {"message": result}
            await redis.publish(channel, json.dumps(payload))

            if EMAILS_ENABLED:
                async with httpx.AsyncClient() as http_client:
                    print("Sending email notification!")
                    await http_client.post(
                        url=f"http://notification/internal/notify",
                        json={
                            "to": job["email"],
                            "notification_type": "ai_response",
                            "params": {
                                "ai_response": result,
                            }
                        }
                    )
        except Exception as e:
            import traceback, sys
            traceback.print_exc(file=sys.stdout)
            try:
                print(">>> job payload:", job)
            except NameError:
                print(">>> job payload not available")


async def event_generator(job_id: str):
    pubsub = redis.pubsub()
    channel = f"job_{job_id}"
    await pubsub.subscribe(channel)
    async for message in pubsub.listen():
        print(f"Received message: {message}")
        if message["type"] == "message":
            yield {"data": message["data"]}
            break
    await pubsub.unsubscribe(channel)
