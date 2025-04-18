import asyncio
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from schemas import RequestBase
from sse_starlette.sse import EventSourceResponse

from utils import *
from db import get_current_user_info


@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(queue_worker())
    yield

app = FastAPI(root_path="/ai", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/summary")
async def enqueue_summary(data: RequestBase, request: Request):

    user_id, user_email = await get_current_user_info(request)
    credit_result = await deduct_credits(user_id, 25)

    job_id = str(uuid.uuid4())
    await redis.rpush("ai_queue", json.dumps({
        "job_id": job_id,
        "sw_lat": data.sw_lat,
        "sw_lon": data.sw_lon,
        "ne_lat": data.ne_lat,
        "ne_lon": data.ne_lon,
        "question": data.question,
        "user_id": user_id,
        "email": user_email
    }))

    print(f"Enqueued job {job_id} for user {user_id} ({user_email})")

    return JSONResponse(status_code=202, content={
        "job_id": f"{job_id}",
        "remaining_credits": credit_result["remaining_credits"],
    })


@app.get("/stream/{job_id}")
async def stream(job_id: str):
    return EventSourceResponse(event_generator(job_id))
