#!/usr/bin/env python3
"""
 Video Generator - Main Entry Point

This is the main entry point for the  Video Generator application.
It imports and runs the FastAPI application from the backend package.
"""

import uvicorn
from backend.main import app
from backend.config.settings import settings

if __name__ == "__main__":
    print("Starting  Video Generator...")
    print(f"🌐 Server: {settings.HOST}:{settings.PORT}")
    print(f"🔧 Debug: {settings.DEBUG}")
    print(f"📚 API Docs: http://{settings.HOST}:{settings.PORT}/docs")
    print("=" * 50)
    
    uvicorn.run(
        "backend.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    ) 