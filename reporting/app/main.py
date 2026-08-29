from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import reports

app = FastAPI(
    title="FarmHub Reporting API",
    description="Standalone read-only aggregated reporting service for FarmHub.",
    version="1.0.0",
)

if settings.CORS_ALLOWED_ORIGINS:
    origins = (
        settings.CORS_ALLOWED_ORIGINS
        if isinstance(settings.CORS_ALLOWED_ORIGINS, list)
        else [settings.CORS_ALLOWED_ORIGINS]
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(reports.router, prefix="/api/v1")


@app.get("/health", summary="Health Check")
async def health():
    return {"status": "ok"}
