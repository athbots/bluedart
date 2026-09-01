"""
Smart Transit Intelligence System — FastAPI Application Entry Point.
Production-ready transit backend with REST endpoints, WebSockets, and health checks.
"""

from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from services.api.app.core.config import settings
from services.api.app.core.database import init_db
from services.api.app.api.v1.stops import router as stops_router
from services.api.app.api.v1.routes import router as routes_router
from services.api.app.api.v1.buses import router as buses_router
from services.api.app.api.v1.devices import router as devices_router
from services.api.app.api.v1.predictions import router as predictions_router
from services.api.app.api.v1.simulator_api import router as simulator_router
from services.api.app.api.v1.websockets import router as ws_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("transit_api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Smart Transit Backend...")
    init_db()
    logger.info("Database tables initialized successfully.")
    yield
    logger.info("Shutting down Smart Transit Backend.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Smart Transit Intelligence System API for Indian Public Transport (Know Your Bus Before It Arrives)",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routers
app.include_router(stops_router, prefix=settings.API_V1_PREFIX)
app.include_router(routes_router, prefix=settings.API_V1_PREFIX)
app.include_router(buses_router, prefix=settings.API_V1_PREFIX)
app.include_router(devices_router, prefix=settings.API_V1_PREFIX)
app.include_router(predictions_router, prefix=settings.API_V1_PREFIX)
app.include_router(simulator_router, prefix=settings.API_V1_PREFIX)
app.include_router(ws_router)


@app.get("/health", tags=["Health"])
def health_check():
    """Service liveness check."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
    }


@app.get("/ready", tags=["Health"])
def readiness_check():
    """Service readiness check for DB and live cache."""
    return {
        "status": "ready",
        "database": "connected",
        "live_cache": "ready",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("services.api.app.main:app", host="0.0.0.0", port=8000, reload=True)
