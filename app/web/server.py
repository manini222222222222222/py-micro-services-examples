import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.common.logger import log
from app.config.nacos_config import get_config
from app.config.trace_.trace_id_config import TraceIdMiddleware
from app.nacos_.controller import router as nacos_router
from app.demo_business.controller import router as test_router

"""
Initialize global nacos configuration at project startup
"""
config = get_config()

"""
init FastAPI app
"""
def create_app():
    app = FastAPI()

    # add trace_id middleware
    app.add_middleware(TraceIdMiddleware)

    # register routes (Routers for different business modules)
    app.include_router(nacos_router)
    app.include_router(test_router)
    # app.include_router(...)

    # global exception interception
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        # can record exception logs and stack information
        log.exception(f"Request exception API: {request.url}, exception details: {exc}")
        return JSONResponse(
            status_code=500,
            content={
                "msg": "Operation failed, please try again later",
                "err": str(exc)
            },
        )
    return app


if __name__ == '__main__':
    app = create_app()
    uvicorn.run(
        app,
        host=config['server']['host'],
        port=config['server']['port'],
        reload=False,
    )
