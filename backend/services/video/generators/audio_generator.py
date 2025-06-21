import os
import logging
import re
import json
import base64
import requests
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from gtts import gTTS  # Fallback
from datetime import datetime
from backend.core.models import AdScript

logger = logging.getLogger(__name__)

@dataclass
class WordTiming:
    """Word-level timing information from ElevenLabs"""
    word: str
    start: float
    end: float
    confidence: float = 1.0

@dataclass
class AudioResult:
    """Result of ElevenLabs audio generation with native timing"""
    audio_path: str
    duration: float
    word_timings: List[WordTiming]
    character_timings: List[Dict]
    transcript: str

class ElevenLabsAudioGenerator:
    """
    Audio generator using ElevenLabs' native timing capabilities via HTTP API.
    
    Uses raw HTTP requests to access ElevenLabs TTS with timestamps endpoint
    since the SDK doesn't support it yet.
    """
    
    def __init__(self, temp_dir: str = "temp_assets"):
        self.temp_dir = temp_dir
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # ElevenLabs configuration
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        self.base_url = "https://api.elevenlabs.io/v1"
        
        # Headers for HTTP requests
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        if self.api_key:
            self.headers["xi-api-key"] = self.api_key
            logger.info("ElevenLabs HTTP client initialized")
        else:
            logger.warning("ElevenLabs API key not found")
        
        # Voice profiles with ElevenLabs voice IDs (optimized for exciting ads)
        self.voice_profiles = {
            "professional": "21m00Tcm4TlvDq8ikWAM",  # Rachel - Clear, professional
            "energetic": "AZnzlk1XvdvUeBnXmlld",     # Domi - Energetic, young (PRIMARY AD VOICE)
            "exciting": "AZnzlk1XvdvUeBnXmlld",      # Domi - Same as energetic but with different settings
            "warm": "EXAVITQu4vr4xnSDxMaL",          # Bella - Warm, engaging
            "authoritative": "ErXwobaYiN019PkySvjV",  # Antoni - Authoritative, deep
            "casual": "MF3mGyEYCl7XYWbV9V6O",        # Elli - Casual, friendly
            "announcer": "ErXwobaYiN019PkySvjV",      # Antoni - TV announcer style
        }
    
    async def generate_audio_with_timing(self, ad_script: AdScript, session_id: str, 
                                       voice_tone: str = "energetic") -> Optional[AudioResult]:
        """
        Generate high-quality audio with native ElevenLabs timing using HTTP API.
        
        Args:
            ad_script: The advertisement script to convert to speech
            session_id: Unique session identifier
            voice_tone: Voice tone (professional, energetic, warm, etc.)
            
        Returns:
            AudioResult with audio path, duration, and precise timing
        """
        try:
            # Create script from ad components
            full_script = self._create_full_script(ad_script)
            cleaned_script = self._clean_script_for_speech(full_script)
            
            logger.info(f"Generating ElevenLabs audio with timing: {voice_tone}")
            logger.info(f"Script: {cleaned_script[:100]}...")
            
            # Try ElevenLabs with native timing
            if self.api_key:
                audio_result = await self._generate_with_http_timing(
                    cleaned_script, session_id, voice_tone
                )
                if audio_result:
                    return audio_result
            
            # Fallback to gTTS
            logger.warning("Falling back to gTTS")
            return await self._generate_gtts_fallback(cleaned_script, session_id, full_script)
            
        except Exception as e:
            logger.error(f"💥 Error in audio generation: {str(e)}")
            return None
    
    async def _generate_with_http_timing(self, text: str, session_id: str, 
                                       voice_tone: str) -> Optional[AudioResult]:
        """Generate audio using ElevenLabs HTTP API with timestamps"""
        try:
            voice_id = self.voice_profiles.get(voice_tone, self.voice_profiles["professional"])
            
            logger.info(f"🎙️ Calling ElevenLabs HTTP API with timestamps...")
            
            # Prepare request data
            url = f"{self.base_url}/text-to-speech/{voice_id}/with-timestamps"
            
            # Optimize voice settings for exciting ad delivery
            voice_settings = self._get_voice_settings(voice_tone)
            
            payload = {
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": voice_settings
            }
            
            # Make HTTP request
            response = requests.post(url, json=payload, headers=self.headers, timeout=30)
            
            if response.status_code != 200:
                logger.error(f"ElevenLabs API error: {response.status_code} - {response.text}")
                return None
            
            response_data = response.json()
            
            # Decode and save audio
            audio_data = base64.b64decode(response_data["audio_base64"])
            audio_path = os.path.join(self.temp_dir, f"{session_id}_elevenlabs_http.mp3")
            
            with open(audio_path, 'wb') as f:
                f.write(audio_data)
            
            logger.info(f"Audio saved to: {audio_path}")
            
            # Extract timing information
            alignment = response_data.get("alignment", {})
            character_timings = []
            
            if alignment and alignment.get("characters"):
                characters = alignment["characters"]
                start_times = alignment.get("character_start_times_seconds", [])
                end_times = alignment.get("character_end_times_seconds", [])
                
                for i, char in enumerate(characters):
                    start_time = start_times[i] if i < len(start_times) else 0
                    end_time = end_times[i] if i < len(end_times) else 0
                    
                    character_timings.append({
                        "character": char,
                        "start": start_time,
                        "end": end_time
                    })
            
            # Convert character timings to word timings
            word_timings = self._character_to_word_timings(character_timings, text)
            
            # Calculate total duration
            duration = max(ct["end"] for ct in character_timings) if character_timings else 15.0
            
            # Save timing data for debugging
            timing_data = {
                "word_timings": [
                    {"word": wt.word, "start": wt.start, "end": wt.end, "confidence": wt.confidence}
                    for wt in word_timings
                ],
                "character_timings": character_timings,
                "duration": duration,
                "transcript": text
            }
            
            timing_path = os.path.join(self.temp_dir, f"{session_id}_elevenlabs_http_timing.json")
            with open(timing_path, 'w') as f:
                json.dump(timing_data, f, indent=2)
            
            logger.info(f"⏱️ Generated {len(word_timings)} word timings, duration: {duration:.2f}s")
            
            return AudioResult(
                audio_path=audio_path,
                duration=duration,
                word_timings=word_timings,
                character_timings=character_timings,
                transcript=text
            )
            
        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP request failed: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"ElevenLabs HTTP timing generation failed: {str(e)}")
            return None
    
    def _character_to_word_timings(self, character_timings: List[Dict], text: str) -> List[WordTiming]:
        """Convert character-level timings to word-level timings"""
        try:
            if not character_timings:
                return []
            
            words = text.split()
            word_timings = []
            
            char_index = 0
            
            for word in words:
                # Skip spaces in character timings
                while (char_index < len(character_timings) and 
                       character_timings[char_index]["character"].isspace()):
                    char_index += 1
                
                if char_index >= len(character_timings):
                    break
                
                # Find character range for this word
                word_start_char = char_index
                word_end_char = min(char_index + len(word), len(character_timings))
                
                # Get timing for first and last character of the word
                start_time = character_timings[word_start_char]["start"]
                end_time = character_timings[word_end_char - 1]["end"] if word_end_char > word_start_char else start_time + 0.1
                
                word_timings.append(WordTiming(
                    word=word,
                    start=start_time,
                    end=end_time,
                    confidence=1.0  # Native ElevenLabs timing is high confidence
                ))
                
                # Move to next word
                char_index = word_end_char
            
            return word_timings
            
        except Exception as e:
            logger.error(f"Error converting character to word timings: {str(e)}")
            return []
    
    async def _generate_gtts_fallback(self, text: str, session_id: str, original_script: str) -> Optional[AudioResult]:
        """Fallback to gTTS with estimated timing"""
        try:
            logger.info("🔄 Using gTTS fallback with estimated timing")
            
            tts = gTTS(text=text, lang='en', slow=False, tld='com')
            audio_path = os.path.join(self.temp_dir, f"{session_id}_gtts_fallback.mp3")
            tts.save(audio_path)
            
            # Estimate word timings
            words = text.split()
            words_per_second = 2.5
            duration = len(words) / words_per_second
            
            word_timings = []
            current_time = 0
            
            for word in words:
                word_duration = len(word) * 0.08 + 0.2  # Rough estimate
                word_timings.append(WordTiming(
                    word=word,
                    start=current_time,
                    end=current_time + word_duration,
                    confidence=0.5  # Low confidence for estimates
                ))
                current_time += word_duration
            
            return AudioResult(
                audio_path=audio_path,
                duration=duration,
                word_timings=word_timings,
                character_timings=[],
                transcript=original_script
            )
            
        except Exception as e:
            logger.error(f"gTTS fallback failed: {str(e)}")
            return None
    
    def _create_full_script(self, ad_script: AdScript) -> str:
        """Create full script from ad components"""
        script_parts = [
            ad_script.hook,
            f"{ad_script.problem} {ad_script.solution}",
            " and ".join(ad_script.benefits[:2]) if ad_script.benefits else "",
            ad_script.call_to_action
        ]
        
        # Filter out empty parts
        script_parts = [part.strip() for part in script_parts if part.strip()]
        
        # Combine with natural pauses
        full_script = ". ".join(script_parts)
        return full_script
    
    def _clean_script_for_speech(self, script: str) -> str:
        """Clean script text for better speech synthesis"""
        # Remove excessive punctuation
        script = re.sub(r'[!]{2,}', '!', script)
        script = re.sub(r'[?]{2,}', '?', script)
        script = re.sub(r'[.]{2,}', '.', script)
        
        # Replace special characters
        replacements = {
            '&': 'and', '%': 'percent', '@': 'at', '#': 'number',
            '$': 'dollar', '+': 'plus', '=': 'equals',
            '<': 'less than', '>': 'greater than',
            '[': '', ']': '', '{': '', '}': '', '|': '',
            '\\': '', '/': ' or ', '_': ' ', '-': ' ',
            '*': '', '^': '', '~': '', '`': '',
        }
        
        for old, new in replacements.items():
            script = script.replace(old, new)
        
        # Clean up multiple spaces
        script = re.sub(r'\s+', ' ', script)
        
        # Ensure proper sentence endings
        script = re.sub(r'([.!?])\s*([A-Z])', r'\1 \2', script)
        
        return script.strip()
    
    def _get_voice_settings(self, voice_tone: str) -> Dict:
        """Get optimized voice settings for different tones with faster speech"""
        voice_settings = {
            "energetic": {
                "stability": 0.3,        # Lower stability for more expressive delivery
                "similarity_boost": 0.7, # Higher similarity for consistent voice
                "style": 0.8,           # More dynamic style
                "use_speaker_boost": True,
                "speed": 1.1           # FASTER speech speed for ads
            },
            "exciting": {
                "stability": 0.2,        # Even lower for maximum expressiveness  
                "similarity_boost": 0.8, # High similarity for clear voice
                "style": 0.9,           # Maximum dynamic style
                "use_speaker_boost": True,
                "speed": 1.1            # EVEN FASTER for exciting delivery
            },
            "announcer": {
                "stability": 0.4,        # Controlled but expressive
                "similarity_boost": 0.6, # Balanced
                "style": 0.7,           # TV announcer style
                "use_speaker_boost": True,
                "speed": 1.1            # Slightly faster announcer pace
            },
            "professional": {
                "stability": 0.6,        # More stable for clarity
                "similarity_boost": 0.5, # Balanced
                "style": 0.4,           # Less dramatic
                "use_speaker_boost": False,
                "speed": 1.0            # Normal speed for professional
            },
            "warm": {
                "stability": 0.5,        # Balanced warmth
                "similarity_boost": 0.6, # Clear voice
                "style": 0.5,           # Moderate style
                "use_speaker_boost": False,
                "speed": 1.1            # Slightly faster warmth
            },
            "casual": {
                "stability": 0.4,        # Natural variation
                "similarity_boost": 0.6, # Clear but relaxed
                "style": 0.6,           # Casual style
                "use_speaker_boost": False,
                "speed": 1.1            # Natural fast casual pace
            }
        }
        
        # Get settings for the requested tone, fallback to energetic for ads
        settings = voice_settings.get(voice_tone, voice_settings["energetic"])
        
        # FIXED: Include speed setting for faster speech
        core_settings = {
            "stability": settings["stability"],
            "similarity_boost": settings["similarity_boost"],
            "speed": settings.get("speed", 1.2)  # Default to faster speech
        }
        
        return core_settings
    
    def get_available_voices(self) -> Dict[str, str]:
        """Get available voice profiles optimized for ad delivery"""
        return {
            "energetic": "🔥 Energetic, exciting female voice - PERFECT FOR ADS (Domi)",
            "exciting": "⚡ Maximum excitement & expressiveness - ULTIMATE AD VOICE (Domi)",
            "announcer": "📺 TV announcer style - Professional but dynamic (Antoni)",
            "professional": "💼 Clear, professional female voice (Rachel)",
            "warm": "❤️ Warm, engaging female voice (Bella)",
            "casual": "😊 Casual, friendly female voice (Elli)"
        }
    
    def is_available(self) -> bool:
        """Check if ElevenLabs is properly configured"""
        return self.api_key is not None
    
    async def test_connection(self) -> bool:
        """Test ElevenLabs API connection"""
        try:
            if not self.api_key:
                return False
            
            # Test with a simple voices endpoint
            url = f"{self.base_url}/voices"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                logger.info("ElevenLabs API connection successful")
                return True
            else:
                logger.error(f"ElevenLabs API test failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"ElevenLabs API connection test failed: {str(e)}")
            return False
    
    async def generate_voiceover(self, ad_script: AdScript, session_id: str, 
                               voice_tone: str = "energetic") -> Optional[AudioResult]:
        """
        Compatibility method for generate_voiceover that wraps generate_audio_with_timing.
        
        Args:
            ad_script: The advertisement script to convert to speech
            session_id: Unique session identifier  
            voice_tone: Voice tone (professional, energetic, warm, etc.)
            
        Returns:
            AudioResult with audio path, duration, and precise timing
        """
        return await self.generate_audio_with_timing(ad_script, session_id, voice_tone) 