from fastapi import APIRouter, HTTPException, Form
from fastapi.responses import FileResponse
import os
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
import logging

from backend.core.models import ProductData, AdScript
from backend.services.scraping.product_scraper import ProductScraper
from backend.services.ai.script_generator import AdScriptGenerator
from backend.services.video.video_generator import VideoGenerator

logger = logging.getLogger(__name__)

# Initialize services
ai_generator = AdScriptGenerator()
video_generator = VideoGenerator()

# Session storage (in production, use Redis or database)
session_storage: Dict[str, Dict[str, Any]] = {}

router = APIRouter()

@router.post("/scrape-product")
async def scrape_product_data(url: str = Form(...)):
    """Step 1: Scrape product data from URL"""
    try:
        session_id = str(uuid.uuid4())
        
        logger.info(f"Step 1: Starting product scrape for session: {session_id}")
        logger.info(f"URL: {url}")
        
        # Initialize session
        session_storage[session_id] = {
            "session_id": session_id,
            "url": url,
            "status": "scraping",
            "created_at": datetime.now().isoformat(),
            "product_data": None,
            "ad_script": None,
            "video_path": None,
            "error": None
        }
        
        # Scrape product data
        async with ProductScraper(debug=True) as scraper:
            product_data = await scraper.scrape_product(url, session_id=session_id)
        
        if not product_data:
            session_storage[session_id]["status"] = "error"
            session_storage[session_id]["error"] = "Failed to scrape product data"
            raise HTTPException(status_code=400, detail="Failed to scrape product data from URL")
        
        # Update session
        session_storage[session_id]["status"] = "scraped"
        session_storage[session_id]["product_data"] = product_data.model_dump()
        
        logger.info(f"✅ Step 1 completed: Product data scraped for session {session_id}")
        
        return {
            "success": True,
            "session_id": session_id,
            "product_data": product_data.model_dump(),
            "status": "scraped"
        }
        
    except Exception as e:
        logger.error(f"❌ Error in Step 1 - scraping: {str(e)}")
        if 'session_id' in locals():
            session_storage[session_id]["status"] = "error"
            session_storage[session_id]["error"] = str(e)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-script")
async def generate_ad_script(session_id: str = Form(...), tone: str = Form("exciting")):
    """Step 2: Generate AI script from scraped product data"""
    try:
        if session_id not in session_storage:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session = session_storage[session_id]
        if session["status"] != "scraped":
            raise HTTPException(status_code=400, detail="Product data not available. Please scrape first.")
        
        logger.info(f"Step 2: Generating script for session: {session_id} with tone: {tone}")
        
        # Update status
        session["status"] = "generating_script"
        
        # Generate script
        product_data = ProductData(**session["product_data"])
        ad_script = await ai_generator.generate_ad_script(product_data, tone=tone)
        
        # Update session
        session["status"] = "script_generated"
        session["ad_script"] = ad_script.model_dump()
        
        logger.info(f"✅ Step 2 completed: Script generated for session {session_id}")
        
        return {
            "success": True,
            "session_id": session_id,
            "ad_script": ad_script.model_dump(),
            "status": "script_generated"
        }
        
    except Exception as e:
        logger.error(f"❌ Error in Step 2 - script generation: {str(e)}")
        if session_id in session_storage:
            session_storage[session_id]["status"] = "error"
            session_storage[session_id]["error"] = str(e)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create-video")
async def create_video_from_session(
    session_id: str = Form(...),
    aspect_ratio: str = Form("16:9"),
    template: str = Form("modern"),
    voice_tone: str = Form("professional"),
    enable_karaoke: bool = Form(True),
    include_voiceover: bool = Form(True),
    background_music: str = Form("corporate"),
    include_music: bool = Form(True)
):
    """Step 3: Create video from product data and script"""
    try:
        if session_id not in session_storage:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session = session_storage[session_id]
        if session["status"] != "script_generated":
            raise HTTPException(status_code=400, detail="Script not available. Please generate script first.")
        
        logger.info(f"Step 3: Creating video for session: {session_id}")
        
        # Update status
        session["status"] = "creating_video"
        
        # Get data from session
        product_data = ProductData(**session["product_data"])
        ad_script = AdScript(**session["ad_script"])
        
        # Create video
        video_path = await video_generator.create_video(
            product_data=product_data,
            ad_script=ad_script,
            session_id=session_id,
            aspect_ratio=aspect_ratio,
            voice_tone=voice_tone,
            template=template,
            karaoke_style="default",
            enable_karaoke=enable_karaoke,
            include_voice=include_voiceover,
            background_music=background_music,
            include_music=include_music
        )
        
        # Update session
        session["status"] = "completed"
        session["video_path"] = video_path
        session["completed_at"] = datetime.now().isoformat()
        
        logger.info(f"✅ Step 3 completed: Video created for session {session_id}")
        
        return {
            "success": True,
            "session_id": session_id,
            "video_path": video_path,
            "status": "completed",
            "download_url": f"/api/download/{session_id}"
        }
        
    except Exception as e:
        logger.error(f"❌ Error in Step 3 - video creation: {str(e)}")
        if session_id in session_storage:
            session_storage[session_id]["status"] = "error"
            session_storage[session_id]["error"] = str(e)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/session/{session_id}")
async def get_session_data(session_id: str):
    """Get full session data including product data and script"""
    if session_id not in session_storage:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = session_storage[session_id]
    
    return {
        "session_id": session_id,
        "status": session["status"],
        "url": session["url"],
        "product_data": session.get("product_data"),
        "ad_script": session.get("ad_script"),
        "video_path": session.get("video_path"),
        "error": session.get("error"),
        "created_at": session.get("created_at"),
        "completed_at": session.get("completed_at")
    }

@router.get("/status/{session_id}")
async def get_status(session_id: str):
    """Get session status"""
    if session_id not in session_storage:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = session_storage[session_id]
    
    return {
        "session_id": session_id,
        "status": session["status"],
        "error": session.get("error"),
        "created_at": session.get("created_at"),
        "completed_at": session.get("completed_at")
    }

@router.get("/download/{session_id}")
async def download_video(session_id: str):
    """Download generated video file"""
    if session_id not in session_storage:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = session_storage[session_id]
    video_path = session.get("video_path")
    
    if not video_path or not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="Video file not found")
    
    return FileResponse(
        video_path,
        media_type="video/mp4",
        filename=f"ad_video_{session_id}.mp4"
    )

@router.delete("/session/{session_id}")
async def cleanup_session(session_id: str):
    """Clean up session data and associated files"""
    if session_id in session_storage:
        session = session_storage[session_id]
        
        # Clean up video file if exists
        if session.get("video_path") and os.path.exists(session["video_path"]):
            try:
                os.remove(session["video_path"])
                logger.info(f"🗑️ Removed video file for session {session_id}")
            except Exception as e:
                logger.warning(f"Failed to remove video file: {str(e)}")
        
        # Remove session data
        del session_storage[session_id]
        logger.info(f"🧹 Session {session_id} cleaned up")
        
        return {"success": True, "message": "Session cleaned up"}
    
    raise HTTPException(status_code=404, detail="Session not found") 