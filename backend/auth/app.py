import uuid
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from db import User, create_db_and_tables, get_async_session, Usage
from schemas import UserCreate, UserRead, UserUpdate
from users import auth_backend, current_active_user, fastapi_users
from private import InternalOnlyMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan, root_path="/auth")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or restrict to your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/balance")
async def get_balance(
        user: User = Depends(current_active_user),
        session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(
        select(User).where(User.id == user.id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {"credits": user.credits}

app.include_router(
    fastapi_users.get_auth_router(auth_backend), tags=["auth"]
)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_reset_password_router(),
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_verify_router(UserRead),
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    tags=["users"],
)


@app.get("/usage")
async def get_usage(
        user: User = Depends(current_active_user),
        session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(
        select(Usage).where(Usage.user_id == user.id)
    )
    usage = result.scalars().all()

    if not usage:
        raise HTTPException(status_code=404, detail="No usage found")

    return usage


private = FastAPI(lifespan=lifespan)
private.add_middleware(InternalOnlyMiddleware)


class CreditUse(BaseModel):
    credits: int
    user_id: uuid.UUID


@private.post("/use-credits")
async def use_credits(
        data: CreditUse,
        session: AsyncSession = Depends(get_async_session),
        note: str = "credits_used"
):
    credits = data.credits
    user_id = data.user_id

    # Using with_for_update to lock the row for update while checking and updating credits to prevent race conditions
    result = await session.execute(
        select(User).where(User.id == user_id).with_for_update()
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.credits < credits:
        raise HTTPException(status_code=400, detail="Not enough credits")

    user.credits -= credits
    session.add(user)

    usage = Usage(
        user_id=user.id,
        credit_change=-credits,
        note=note
    )
    session.add(usage)
    await session.commit()

    return {
        "message": f"{credits} Credits used successfully!",
        "remaining_credits": user.credits,
    }

app.mount("/internal", private)
