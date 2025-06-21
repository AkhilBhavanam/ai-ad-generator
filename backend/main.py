import logging
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from backend.config.settings import settings
from backend.api.routes import router as api_router

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format=settings.LOG_FORMAT
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting  Video Generator API...")
    
    # Validate API keys
    api_keys = settings.validate_api_keys()
    logger.info(f"🔑 API Keys Status: {api_keys}")
    
    # Create necessary directories
    os.makedirs(settings.TEMP_DIR, exist_ok=True)
    os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
    os.makedirs(settings.STATIC_DIR, exist_ok=True)
    
    logger.info("Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down  Video Generator API...")
    logger.info("Application shutdown complete")

# Create FastAPI application
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description=settings.API_DESCRIPTION,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory=settings.STATIC_DIR), name="static")

# Include API routes
app.include_router(api_router, prefix="/api", tags=["api"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to  Video Generator API",
        "version": settings.API_VERSION,
        "status": "running",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z",
        "version": settings.API_VERSION
    }

@app.get("/config")
async def get_config():
    """Get application configuration (development only)"""
    if not settings.is_development():
        raise HTTPException(status_code=403, detail="Configuration endpoint not available in production")
    
    return {
        "api_keys": settings.validate_api_keys(),
        "aspect_ratios": list(settings.ASPECT_RATIOS.keys()),
        "templates": {k: v["name"] for k, v in settings.VIDEO_TEMPLATES.items()},
        "voice_tones": {k: v["name"] for k, v in settings.VOICE_TONES.items()},
        "karaoke_styles": {k: v["name"] for k, v in settings.KARAOKE_STYLES.items()},
        "background_music": {k: v["name"] for k, v in settings.BACKGROUND_MUSIC.items()}
    }

if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"🌐 Starting server on {settings.HOST}:{settings.PORT}")
    logger.info(f"🔧 Debug mode: {settings.DEBUG}")
    
    uvicorn.run(
        "backend.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    ) 