from fastapi import FastAPI, Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response


class InternalOnlyMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        if not request.client.host.startswith("172.18."):  # Specific to Docker network space
            raise HTTPException(status_code=403, detail="Internal access only.")
        return await call_next(request)
