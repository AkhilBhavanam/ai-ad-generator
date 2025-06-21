import os
import logging
from typing import Optional, Dict, Any
from moviepy.editor import AudioFileClip, CompositeAudioClip
from backend.config.settings import Settings

logger = logging.getLogger(__name__)

class BackgroundMusicGenerator:
    """Handles background music selection and processing for videos"""
    
    def __init__(self, temp_dir: str = "temp_assets"):
        self.temp_dir = temp_dir
        self.music_dir = "static/music"
        self.settings = Settings()
        
        # Ensure directories exist
        os.makedirs(self.temp_dir, exist_ok=True)
        os.makedirs(self.music_dir, exist_ok=True)
        
        # Music file mappings
        self.music_files = {
            "corporate": "corporate-background-music.mp3",
            "energetic": "energetic-upbeat-background-music-330148.mp3",
            "relaxed": "relaxed-background-music.mp3",
            "modern": "modern-background-music.mp3"
        }
        
        logger.info("BackgroundMusicGenerator initialized")
    
    def get_available_music_styles(self) -> Dict[str, Dict[str, str]]:
        """Get available background music styles"""
        return self.settings.BACKGROUND_MUSIC
    
    def get_music_file_path(self, style: str) -> Optional[str]:
        """Get the file path for a specific music style"""
        if style not in self.music_files:
            logger.warning(f"Music style '{style}' not found, using 'corporate' as fallback")
            style = "corporate"
        
        filename = self.music_files[style]
        file_path = os.path.join(self.music_dir, filename)
        
        if not os.path.exists(file_path):
            logger.warning(f"Music file not found: {file_path}")
            return None
        
        return file_path
    
    def create_background_music_clip(self, 
                                   style: str, 
                                   duration: float, 
                                   volume: float = 0.3,
                                   fade_in: float = 1.0,
                                   fade_out: float = 1.0) -> Optional[AudioFileClip]:
        """
        Create a background music clip with specified parameters
        
        Args:
            style: Music style (corporate, energetic, relaxed, modern)
            duration: Duration of the music clip
            volume: Volume level (0.0 to 1.0)
            fade_in: Fade in duration in seconds
            fade_out: Fade out duration in seconds
            
        Returns:
            AudioFileClip or None if failed
        """
        try:
            music_file_path = self.get_music_file_path(style)
            if not music_file_path:
                logger.warning(f"No music file available for style: {style}")
                return None
            
            logger.info(f"Loading background music: {music_file_path}")
            
            # Load the music file
            music_clip = AudioFileClip(music_file_path)
            
            # Loop the music if it's shorter than the required duration
            if music_clip.duration < duration:
                # Calculate how many times we need to loop
                loops_needed = int(duration / music_clip.duration) + 1
                logger.info(f"Music duration ({music_clip.duration:.2f}s) is shorter than required ({duration:.2f}s), looping {loops_needed} times")
                
                # Create a list of the same clip repeated
                looped_clips = [music_clip] * loops_needed
                
                # Concatenate all clips
                from moviepy.editor import concatenate_audioclips
                music_clip = concatenate_audioclips(looped_clips)
            
            # Trim to exact duration
            if music_clip.duration > duration:
                music_clip = music_clip.subclip(0, duration)
            
            # Apply volume
            music_clip = music_clip.volumex(volume)
            
            # Apply fade in/out effects
            if fade_in > 0:
                music_clip = music_clip.audio_fadein(fade_in)
            if fade_out > 0:
                music_clip = music_clip.audio_fadeout(fade_out)
            
            logger.info(f"Created background music clip: {duration:.2f}s, volume: {volume}")
            return music_clip
            
        except Exception as e:
            logger.error(f"Error creating background music clip: {str(e)}")
            return None
    
    def mix_audio_with_background_music(self, 
                                      voice_audio_path: str, 
                                      music_style: str,
                                      music_volume: float = 0.3,
                                      output_path: str = None) -> Optional[str]:
        """
        Mix voice audio with background music
        
        Args:
            voice_audio_path: Path to the voice audio file
            music_style: Background music style
            music_volume: Background music volume (0.0 to 1.0)
            output_path: Output path for mixed audio (optional)
            
        Returns:
            Path to the mixed audio file or None if failed
        """
        try:
            if not os.path.exists(voice_audio_path):
                logger.error(f"Voice audio file not found: {voice_audio_path}")
                return None
            
            # Load voice audio
            voice_clip = AudioFileClip(voice_audio_path)
            duration = voice_clip.duration
            
            # Create background music
            music_clip = self.create_background_music_clip(
                music_style, duration, music_volume
            )
            
            if not music_clip:
                logger.warning("Failed to create background music, returning voice only")
                return voice_audio_path
            
            # Mix the audio
            mixed_audio = CompositeAudioClip([voice_clip, music_clip])
            
            # Generate output path if not provided
            if not output_path:
                base_name = os.path.splitext(os.path.basename(voice_audio_path))[0]
                output_path = os.path.join(self.temp_dir, f"{base_name}_with_music.mp3")
            
            # Export mixed audio
            mixed_audio.write_audiofile(
                output_path,
                verbose=False,
                logger=None,
                audio_bitrate='192k'
            )
            
            # Clean up
            voice_clip.close()
            music_clip.close()
            mixed_audio.close()
            
            logger.info(f"Mixed audio exported to: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error mixing audio with background music: {str(e)}")
            return None
    
    def add_background_music_to_video(self, 
                                    video_clip, 
                                    music_style: str,
                                    music_volume: float = 0.3) -> Optional[AudioFileClip]:
        """
        Add background music to a video clip
        
        Args:
            video_clip: The video clip to add music to
            music_style: Background music style
            music_volume: Background music volume (0.0 to 1.0)
            
        Returns:
            Video clip with background music or None if failed
        """
        try:
            duration = video_clip.duration
            
            # Create background music
            music_clip = self.create_background_music_clip(
                music_style, duration, music_volume
            )
            
            if not music_clip:
                logger.warning("Failed to create background music")
                return video_clip
            
            # If video already has audio, mix it with background music
            if video_clip.audio:
                # Mix existing audio with background music
                mixed_audio = CompositeAudioClip([video_clip.audio, music_clip])
                video_with_music = video_clip.set_audio(mixed_audio)
            else:
                # Just add background music
                video_with_music = video_clip.set_audio(music_clip)
            
            logger.info(f"Added background music to video: {duration:.2f}s")
            return video_with_music
            
        except Exception as e:
            logger.error(f"Error adding background music to video: {str(e)}")
            return video_clip 