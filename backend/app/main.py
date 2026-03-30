from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from app.config import get_settings
from app.rate_limit import limiter
from app.services.account_store import AccountStoreError
from app.routers.auth import router as auth_router
from app.routers.health import router as health_router
from app.routers.openrouter import router as openrouter_router
from app.routers.payments import router as payments_router
from app.routers.upload import router as upload_router

settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    state={"limiter": limiter},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Account-Points", "X-Account-User-Id"],
)


@app.exception_handler(AccountStoreError)
async def handle_account_store_error(_, exc: AccountStoreError):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
            }
        },
    )


@app.exception_handler(RateLimitExceeded)
async def handle_rate_limit_exceeded(_, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={
            "error": {
                "code": "rate_limit_exceeded",
                "message": "Too many requests. Please try again later.",
            }
        },
        headers={"Retry-After": "60"},
    )


app.include_router(health_router)
app.include_router(auth_router)
app.include_router(openrouter_router)
app.include_router(payments_router)
app.include_router(upload_router)
