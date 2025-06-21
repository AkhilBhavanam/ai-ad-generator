from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict, Any
from datetime import datetime

class ProductData(BaseModel):
    """Product data scraped from e-commerce sites"""
    title: str
    description: Optional[str] = None
    price: Optional[str] = None
    brand: Optional[str] = None
    rating: Optional[str] = None
    review_count: Optional[str] = None
    primary_image: Optional[str] = None
    downloaded_images: List[str] = []  # Local file paths of downloaded images
    key_features: List[str] = []
    url: str

class AdScript(BaseModel):
    """Generated advertisement script"""
    hook: str
    problem: str
    solution: str
    benefits: List[str]
    call_to_action: str
    duration_seconds: int = 15
    tone: str = "exciting"
    target_audience: str = "general"

class VideoScene(BaseModel):
    """Video scene with timing and content"""
    start_time: float
    end_time: float
    text: Optional[str] = None
    image_url: Optional[str] = None
    animation_type: str = "fade" 