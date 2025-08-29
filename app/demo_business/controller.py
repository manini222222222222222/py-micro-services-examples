from datetime import datetime

import pytz
from fastapi import APIRouter, Request

router = APIRouter(prefix="/demo", tags=['demo'])

"""
test api demo
"""
@router.get("/hell/world")
async def hello(request: Request):
    now = datetime.now(tz=pytz.timezone('Asia/Shanghai')).strftime("%Y-%m-%d %H:%M:%S")
    host = request.client.host
    return {
        "msg": "hello world",
        "time": now,
        "host": host
    }
