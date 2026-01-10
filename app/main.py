from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from .config import settings
from .database import init_db
from .routes import (
    auth_router,
    organizations_router,
    controls_router,
    evaluations_router,
    dashboard_router,
    dashboard_router,
    history_router,
    bia_router
)

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="NIAP Compliance Assessment Platform - A professional tool for organizations to evaluate their compliance with Qatar's National Information Assurance Policy",
    version=settings.APP_VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Configure CORS
origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(organizations_router)
app.include_router(controls_router)
app.include_router(evaluations_router)
app.include_router(dashboard_router)
app.include_router(history_router)
app.include_router(bia_router)

# Create upload directory
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

# Mount static files for uploads
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Mount frontend static files
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    print(f"✅ LOADED CORS ORIGINS: {origins}")
    init_db()

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "app": settings.APP_NAME, "version": settings.APP_VERSION}
