import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routers import chat, classify, health, search, summarise
from app.config import get_settings
from app.infrastructure.rate_limiter import RateLimitExceededError

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

# Settings 
settings = get_settings()


# Application factory
app = FastAPI(
    title="LibraryMind API",
    description=(
        "An AI-powered library assistant providing semantic book search, "
        "RAG-grounded Q&A, multi-turn chat, ticket classification, "
        "and review summarisation.\n\n"
        "**All endpoints require a valid request body validated by Pydantic.**\n\n"
        "Error codes:\n"
        "- `422` — validation error (missing / invalid fields)\n"
        "- `429` — rate limit exceeded\n"
        "- `503` — AI provider unavailable or returned invalid output"
    ),
    version="7.0.0",
    contact={
        "name": "LibraryMind Team",
    },
    license_info={
        "name": "MIT",
    },
    debug=settings.DEBUG,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # restrict to specific domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# Global exception handlers

@app.exception_handler(RateLimitExceededError)
async def rate_limit_handler(request: Request, exc: RateLimitExceededError):
    """
    Catch RateLimitExceededError raised anywhere in the stack and
    return HTTP 429 with a clear message — even if a router forgot to
    catch it explicitly.
    """
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded. Please wait before retrying."},
    )



# Routers

app.include_router(health.router)
app.include_router(search.router)
app.include_router(chat.router)
app.include_router(classify.router)
app.include_router(summarise.router)

# Root redirect (convenience — sends browser users to /docs)
@app.get(
    "/",
    include_in_schema=False,  # don't pollute Swagger with this redirect
)
async def root():
    """Redirect root to the interactive Swagger UI."""
    return JSONResponse(
        content={
            "project":     settings.APP_NAME,
            "version":     "7.0.0",
            "environment": settings.ENVIRONMENT,
            "docs":        "/docs",
            "health":      "/health",
            "status":      "ready",
        }
    )



# Startup event — log which providers are active

@app.on_event("startup")
async def on_startup():
    logger.info("=" * 60)
    logger.info(f"  LibraryMind API v7.0.0 starting up")
    logger.info(f"  Environment     : {settings.ENVIRONMENT}")
    logger.info(f"  Primary provider: {settings.PRIMARY_PROVIDER}")
    logger.info(f"  Debug mode      : {settings.DEBUG}")
    logger.info(f"  Swagger UI      : http://localhost:8000/docs")
    logger.info("=" * 60)



# Dev entrypoint
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
