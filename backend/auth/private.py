from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response
from fastapi.responses import JSONResponse


class InternalOnlyMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        if not request.client.host.startswith("172."):  # Specific to Docker network space
            return JSONResponse(status_code=403, content="Internal access only.")
        return await call_next(request)
