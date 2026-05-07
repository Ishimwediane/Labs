from fastapi import FastAPI
from app.config import get_settings

# Initialize settings
settings = get_settings()

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG
)


@app.get("/")
async def root():
    """
    Root endpoint for system health check and setup verification.
    """
    return {
        "project": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG,
        "primary_provider": settings.PRIMARY_PROVIDER,
        "message": "LibraryMind setup complete",
        "status": "ready"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
