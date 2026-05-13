import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import OUTPUT_DIR, STATIC_DIR
from app.routers.chat import router as chat_router
from app.routers.comfy import router as comfy_router
from app.routers.storage import router as storage_router
from app.routers.utility import router as utility_router
from app.routers.settings import router as settings_router
from app.runtime import reset_global_loop, set_global_loop


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    set_global_loop(asyncio.get_running_loop())
    try:
        yield
    finally:
        reset_global_loop()


def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    app.mount("/output", StaticFiles(directory=OUTPUT_DIR), name="output")

    app.include_router(utility_router)
    app.include_router(settings_router)
    app.include_router(storage_router)
    app.include_router(chat_router)
    app.include_router(comfy_router)

    return app


app = create_app()
