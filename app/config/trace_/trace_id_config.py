import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.config.trace_.request_context import set_trace_id

"""
FastAPI trace related middleware
"""
class TraceIdMiddleware(BaseHTTPMiddleware):

    """
    request settingstrace id
    """
    async def dispatch(self, request: Request, call_next):
        # 1. Retrieve traceId (such as X-Trace Id) from the header, generate if not available
        trace_id = request.headers.get("X-Trace-Id") or str(uuid.uuid4())
        set_trace_id(trace_id)
        # 2. TraceId can be added with a response header, or it can only be used for logging purposes
        response = await call_next(request)
        response.headers["X-Trace-Id"] = trace_id
        return response