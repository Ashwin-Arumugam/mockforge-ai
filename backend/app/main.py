from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import engine, Base
from app.api import projects, specs, chaos, agents
from app.mock_engine import router as mock_router

# Create database tables automatically on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Intelligent Stateful API Virtualization & Testing Platform",
    version="1.0.0"
)

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "online", "platform": settings.PROJECT_NAME}

# Platform REST Endpoints
app.include_router(projects.router, prefix="/api/v1/projects", tags=["projects"])
app.include_router(specs.router, prefix="/api/v1/specs", tags=["specs"])
app.include_router(chaos.router, prefix="/api/v1/chaos", tags=["chaos"])
app.include_router(agents.router, prefix="/api/v1/agents", tags=["agents"])

# Dynamic Mock Catch-All Router
app.include_router(mock_router.router, tags=["mock_engine"])

@app.get("/health")
def health_check():
    return {"status": "online", "system": settings.PROJECT_NAME, "version": "1.0.0"}

@app.get("/")
def root():
    return {
        "message": "Welcome to MockForge AI Platform API",
        "docs": "/docs",
        "health": "/health"
    }
