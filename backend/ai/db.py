import uuid

import httpx
from fastapi import HTTPException, Request


async def deduct_credits(
    user_id: uuid.UUID,
    credits: int,
):

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://auth:8004/auth/internal/use-credits",
            json={"credits": credits, "user_id": user_id},
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail=response.text,
        )

    return response.json()


async def get_current_user_info(
    request: Request,
):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    bearer_token = auth_header.split(" ")[1]

    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://auth:8004/auth/me",
            headers={"Authorization": f"Bearer {bearer_token}"},
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail=response.text,
        )

    user_info = response.json()
    return user_info["id"], user_info["email"]
