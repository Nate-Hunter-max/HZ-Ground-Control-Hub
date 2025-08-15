"""
Ground Control Hub (GCH) - Main Application Entry Point
Stratospheric device management and telemetry system
"""

from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.core.logger import setup_logging


# ------------------------------------------------------------------
# Lifespan context manager for startup & shutdown logic
# ------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles application startup and shutdown events.
    Code before 'yield' runs once at startup (before first request).
    Code after 'yield' runs once at shutdown (after last request).
    """
    # --------------- Startup ---------------
    setup_logging()

    # Create GCH directory structure in the user's home folder
    gch_dir = Path.home() / "GCH"
    gch_dir.mkdir(exist_ok=True)

    # Subdirectories for configs, logs, plots, exports
    (gch_dir / "configs").mkdir(exist_ok=True)
    (gch_dir / "logs").mkdir(exist_ok=True)
    (gch_dir / "plots").mkdir(exist_ok=True)
    (gch_dir / "exports").mkdir(exist_ok=True)

    print(f"GCH initialized. Data directory: {gch_dir}")

    yield  # Application is now running

    # --------------- Shutdown ---------------
    # Any graceful cleanup logic can be placed here
    print("GCH is shutting down...")


# ------------------------------------------------------------------
# FastAPI application factory
# ------------------------------------------------------------------
app = FastAPI(
    title="Ground Control Hub",
    description="Stratospheric Device Management System",
    version="0.1.0",
    lifespan=lifespan  # modern lifespan handler
)

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all API routes
app.include_router(router, prefix="/api")

# Serve static React build if it exists
if Path("../frontend/build").exists():
    app.mount("/", StaticFiles(directory="../frontend/build", html=True), name="static")

# ------------------------------------------------------------------
# Entry point for development server
# ------------------------------------------------------------------
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )
