import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.routes_assessments import router as assessments_router
from app.core.logging import logger, clear_diagnostic_logs

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Truncate and clear old log file on server startup
    os.makedirs(settings.output_dir, exist_ok=True)
    clear_diagnostic_logs()
    logger.info("Cleared previous session log. Diagnostic logging initialized for new server session.")
    yield

app = FastAPI(
    title="AquaTrace API",
    description="Agentic Waterbody Pollution Assessment Platform API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS setup
origins = [origin.strip() for origin in settings.cors_allowed_origins.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(assessments_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {
        "service": "AquaTrace Backend API",
        "status": "online",
        "version": "1.0.0",
        "docs": "/docs"
    }
