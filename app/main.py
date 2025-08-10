from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health, metrics, dq_engine, teams_bot
from app.core.db import create_tables
from app.core.settings import settings

# Create FastAPI app
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description=settings.API_DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["health"])
app.include_router(metrics.router, prefix="/api/v1", tags=["metrics"])
app.include_router(dq_engine.router, prefix="/api/v1/dq", tags=["data-quality"])
app.include_router(teams_bot.router, prefix="/api/v1/teams", tags=["teams-bot"])


@app.on_event("startup")
async def startup_event():
    """Create database tables on startup."""
    create_tables()


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "LabOps Metrics API",
        "version": settings.API_VERSION,
        "docs": "/docs"
    }
