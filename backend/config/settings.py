import os
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    """Application settings and configuration"""
    
    # API Settings
    API_TITLE = " Video Generator API"
    API_VERSION = "1.0.0"
    API_DESCRIPTION = "AI-powered video advertisement generator"
    
    # Server Settings
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8000))
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    
    # CORS Settings
    CORS_ORIGINS = [
        "http://localhost:3000",
        "http://localhost:5173",  # Vite dev server
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]
    
    # API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
    
    # File Paths
    TEMP_DIR = os.getenv("TEMP_DIR", "temp_assets")
    OUTPUT_DIR = os.getenv("OUTPUT_DIR", "generated_videos")
    STATIC_DIR = os.getenv("STATIC_DIR", "static")
    
    # Video Settings
    DEFAULT_FPS = 30
    DEFAULT_DURATION = 15
    MAX_DURATION = 60
    
    # Supported Aspect Ratios
    ASPECT_RATIOS = {
        "16:9": (1920, 1080),
        "9:16": (1080, 1920),
        "1:1": (1080, 1080),
        "4:3": (1440, 1080),
        "21:9": (2560, 1080)
    }
    
    # Video Templates
    VIDEO_TEMPLATES = {
        "modern": {
            "name": "Modern",
            "description": "Clean, professional design",
            "colors": {
                "primary": "#4CAF50",
                "secondary": "#2196F3",
                "accent": "#FF9800",
                "text": "#FFFFFF",
                "background": "#1A1A1A"
            }
        },
        "vibrant": {
            "name": "Vibrant",
            "description": "Bright, energetic design",
            "colors": {
                "primary": "#FF5722",
                "secondary": "#9C27B0",
                "accent": "#FFEB3B",
                "text": "#FFFFFF",
                "background": "#000000"
            }
        },
        "minimal": {
            "name": "Minimal",
            "description": "Simple, elegant design",
            "colors": {
                "primary": "#FFFFFF",
                "secondary": "#CCCCCC",
                "accent": "#333333",
                "text": "#000000",
                "background": "#FFFFFF"
            }
        },
        "corporate": {
            "name": "Corporate",
            "description": "Professional business design",
            "colors": {
                "primary": "#2C3E50",
                "secondary": "#34495E",
                "accent": "#3498DB",
                "text": "#FFFFFF",
                "background": "#ECF0F1"
            }
        }
    }
    
    # Voice Tones
    VOICE_TONES = {
        "professional": {
            "name": "Professional",
            "description": "Clear, authoritative voice",
            "elevenlabs_voice_id": "pNInz6obpgDQGcFmaJgB"  # Adam
        },
        "friendly": {
            "name": "Friendly",
            "description": "Warm, approachable voice",
            "elevenlabs_voice_id": "21m00Tcm4TlvDq8ikWAM"  # Rachel
        },
        "energetic": {
            "name": "Energetic",
            "description": "High-energy, enthusiastic voice",
            "elevenlabs_voice_id": "AZnzlk1XvdvUeBnXmlld"  # Domi
        },
        "casual": {
            "name": "Casual",
            "description": "Relaxed, conversational voice",
            "elevenlabs_voice_id": "EXAVITQu4vr4xnSDxMaL"  # Bella
        }
    }
    
    # Karaoke Styles
    KARAOKE_STYLES = {
        "default": {
            "name": "Default",
            "description": "Standard highlighting",
            "highlight_color": "#FFD700",
            "background_color": "rgba(0,0,0,0.7)"
        },
        "energetic": {
            "name": "Energetic",
            "description": "Bright, dynamic highlighting",
            "highlight_color": "#FF5722",
            "background_color": "rgba(0,0,0,0.8)"
        },
        "professional": {
            "name": "Professional",
            "description": "Clean, business-like highlighting",
            "highlight_color": "#2196F3",
            "background_color": "rgba(0,0,0,0.6)"
        },
        "warm": {
            "name": "Warm",
            "description": "Soft, friendly highlighting",
            "highlight_color": "#FF9800",
            "background_color": "rgba(0,0,0,0.5)"
        }
    }
    
    # Background Music Styles
    BACKGROUND_MUSIC = {
        "corporate": {
            "name": "Corporate",
            "description": "Professional, business-like music"
        },
        "energetic": {
            "name": "Energetic",
            "description": "High-energy, upbeat music"
        },
        "relaxed": {
            "name": "Relaxed",
            "description": "Calm, soothing music"
        },
        "modern": {
            "name": "Modern",
            "description": "Contemporary, trendy music"
        }
    }
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
    
    # Session Management
    SESSION_TIMEOUT_HOURS = int(os.getenv("SESSION_TIMEOUT_HOURS", "24"))
    MAX_SESSIONS_PER_USER = int(os.getenv("MAX_SESSIONS_PER_USER", "10"))
    
    # File Upload Limits
    MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
    ALLOWED_IMAGE_FORMATS = [".jpg", ".jpeg", ".png", ".webp"]
    ALLOWED_VIDEO_FORMATS = [".mp4", ".avi", ".mov", ".mkv"]
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    @classmethod
    def get_voice_tone_config(cls, tone: str) -> Dict[str, Any]:
        """Get voice tone configuration"""
        return cls.VOICE_TONES.get(tone, cls.VOICE_TONES["professional"])
    
    @classmethod
    def get_template_config(cls, template: str) -> Dict[str, Any]:
        """Get video template configuration"""
        return cls.VIDEO_TEMPLATES.get(template, cls.VIDEO_TEMPLATES["modern"])
    
    @classmethod
    def get_karaoke_style_config(cls, style: str) -> Dict[str, Any]:
        """Get karaoke style configuration"""
        return cls.KARAOKE_STYLES.get(style, cls.KARAOKE_STYLES["default"])
    
    @classmethod
    def get_aspect_ratio_dimensions(cls, ratio: str) -> tuple:
        """Get dimensions for aspect ratio"""
        return cls.ASPECT_RATIOS.get(ratio, cls.ASPECT_RATIOS["16:9"])
    
    @classmethod
    def is_development(cls) -> bool:
        """Check if running in development mode"""
        return cls.DEBUG
    
    @classmethod
    def validate_api_keys(cls) -> Dict[str, bool]:
        """Validate that required API keys are present"""
        return {
            "openai": bool(cls.OPENAI_API_KEY),
            "elevenlabs": bool(cls.ELEVENLABS_API_KEY)
        }

# Global settings instance
settings = Settings() 