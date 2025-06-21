import os
import logging
from typing import Optional
from moviepy.editor import AudioFileClip

from backend.core.models import ProductData, AdScript
from backend.services.video.processors.image_processor import ImageProcessor
from backend.services.video.generators.video_composer import VideoComposer
from backend.services.video.generators.audio_generator import ElevenLabsAudioGenerator
from backend.services.video.generators.background_music_generator import BackgroundMusicGenerator
from backend.services.video.renderers.karaoke_renderer import KaraokeTextRenderer

logger = logging.getLogger(__name__)

class VideoGenerator:
    """
    Main video generator service that orchestrates all video generation components.
    
    Features:
    - ElevenLabs TTS with native word-level timing
    - Karaoke-style subtitle highlighting
    - Professional video composition
    - Multiple voice tones and styles
    - Background music support
    """
    
    def __init__(self):
        self.temp_dir = "temp_assets"
        self.output_dir = "generated_videos"
        
        # Ensure directories exist
        os.makedirs(self.temp_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Initialize components
        self.audio_generator = ElevenLabsAudioGenerator(self.temp_dir)
        self.karaoke_renderer = KaraokeTextRenderer(self.temp_dir)
        self.background_music_generator = BackgroundMusicGenerator(self.temp_dir)
        
        # Standard components
        self.image_processor = ImageProcessor(self.temp_dir)
        self.video_composer = VideoComposer(self.temp_dir)
        
        # Enhanced components for karaoke
        from backend.services.video.renderers.text_renderer import TextRenderer
        self.text_renderer = TextRenderer(self.temp_dir)
        
        # Settings
        self.fps = 30
        self.default_duration = 15
        self.max_duration = 30  # Maximum video duration in seconds
        
        logger.info("VideoGenerator service initialized")
    
    async def create_video(self, 
                          product_data: ProductData, 
                          ad_script: AdScript, 
                          session_id: str,
                          aspect_ratio: str = "16:9",
                          template: str = "modern",
                          voice_tone: str = "professional",
                          karaoke_style: str = "default",
                          include_voice: bool = True,
                          enable_karaoke: bool = True,
                          background_music: str = "corporate",
                          include_music: bool = False) -> str:
        """
        Create a complete video advertisement from product data and script.
        
        Args:
            product_data: Scraped product information
            ad_script: Generated advertisement script
            session_id: Unique session identifier
            aspect_ratio: Video aspect ratio (16:9, 9:16, 1:1)
            template: Visual template style
            voice_tone: Voice tone for narration
            karaoke_style: Karaoke subtitle style
            include_voice: Whether to include voiceover
            enable_karaoke: Whether to enable karaoke subtitles
            background_music: Background music style
            include_music: Whether to include background music
            
        Returns:
            Path to the generated video file
        """
        try:
            logger.info(f"Starting video generation for session: {session_id}")
            logger.info(f"Product: {product_data.title}")
            logger.info(f"Settings: {aspect_ratio}, {template}, voice: {voice_tone}, karaoke: {enable_karaoke}")
            
            # Get video dimensions
            width, height = self.video_composer.get_dimensions(aspect_ratio)
            
            # Calculate actual duration based on script
            actual_duration = ad_script.duration_seconds
            
            # Generate audio if requested
            audio_result = None
            if include_voice and self.audio_generator.is_available():
                try:
                    logger.info(f"Generating voiceover with {voice_tone} tone...")
                    audio_result = await self.audio_generator.generate_voiceover(
                        ad_script, session_id, voice_tone
                    )
                    if audio_result:
                        actual_duration = audio_result.duration
                        logger.info(f"Voiceover generated: {actual_duration:.2f}s")
                    else:
                        logger.warning("Voiceover generation failed, using script duration")
                        audio_result = None
                        
                except Exception as e:
                    logger.warning(f"Audio generation failed: {str(e)}")
                    audio_result = None
            
            # Ensure we have a valid duration
            if actual_duration <= 0:
                actual_duration = 15.0  # Default fallback duration
                logger.warning(f"Invalid duration detected, using fallback: {actual_duration}s")
            
            # Enforce maximum duration limit
            if actual_duration > self.max_duration:
                logger.warning(f"Duration {actual_duration:.2f}s exceeds maximum {self.max_duration}s, trimming to {self.max_duration}s")
                actual_duration = self.max_duration
                
                # If we have audio, we need to trim it as well
                if audio_result and audio_result.audio_path and os.path.exists(audio_result.audio_path):
                    try:
                        original_audio = AudioFileClip(audio_result.audio_path)
                        if original_audio.duration > self.max_duration:
                            # Trim audio to max duration
                            trimmed_audio_path = os.path.join(self.temp_dir, f"{session_id}_trimmed_audio.mp3")
                            trimmed_audio = original_audio.subclip(0, self.max_duration)
                            trimmed_audio.write_audiofile(trimmed_audio_path, verbose=False, logger=None)
                            original_audio.close()
                            trimmed_audio.close()
                            
                            # Update audio result
                            audio_result.audio_path = trimmed_audio_path
                            audio_result.duration = self.max_duration
                            
                            # Trim word timings if available
                            if audio_result.word_timings:
                                audio_result.word_timings = [
                                    wt for wt in audio_result.word_timings 
                                    if wt.start < self.max_duration
                                ]
                                logger.info(f"Trimmed audio and word timings to {self.max_duration}s")
                    except Exception as e:
                        logger.warning(f"Failed to trim audio: {str(e)}")
            
            # Create video composition
            logger.info(f"Composing video with duration: {actual_duration:.2f}s")
            
            # Get downloaded images from product data
            image_paths = product_data.downloaded_images if product_data.downloaded_images else []
            logger.info(f"Using {len(image_paths)} downloaded images for video background")
            
            if enable_karaoke and audio_result:
                # Simple karaoke with basic timing
                main_video = await self._create_simple_karaoke_video(
                    ad_script, image_paths, width, height, 
                    template, karaoke_style, actual_duration, audio_result
                )
            else:
                # Standard video composition without karaoke
                if enable_karaoke:
                    # Karaoke enabled but no audio timing - create basic subtitles at bottom
                    main_video = await self._create_basic_subtitle_video(
                        ad_script, image_paths, width, height, 
                        template, actual_duration, audio_result
                    )
                else:
                    # Karaoke disabled - create video without subtitles
                    main_video = await self._create_video_without_subtitles(
                        ad_script, image_paths, width, height, 
                        template, actual_duration
                    )
            
            # Ensure main video duration matches audio duration exactly
            if audio_result and audio_result.duration > 0:
                main_video = main_video.set_duration(audio_result.duration)
                actual_duration = audio_result.duration
                logger.info(f"Adjusted video duration to match audio: {actual_duration:.2f}s")
            
            # Final duration validation
            if actual_duration <= 0:
                actual_duration = 15.0
                logger.warning(f"Invalid duration, using fallback: {actual_duration}s")
            
            # Enforce maximum duration limit before export
            if actual_duration > self.max_duration:
                logger.warning(f"Final video duration {actual_duration:.2f}s exceeds maximum {self.max_duration}s, trimming")
                actual_duration = self.max_duration
                main_video = main_video.subclip(0, self.max_duration)
            
            # Ensure final video has correct duration
            main_video = main_video.set_duration(actual_duration)

            # Attach audio if available
            from moviepy.editor import AudioFileClip, concatenate_videoclips
            if audio_result and audio_result.audio_path and os.path.exists(audio_result.audio_path):
                audio_clip = AudioFileClip(audio_result.audio_path)
                
                # First, attach voice audio to the video
                main_video = main_video.set_audio(audio_clip)
                
                # Then add background music if requested (this will mix with existing voice audio)
                if include_music:
                    logger.info(f"Adding background music: {background_music}")
                    main_video = self.background_music_generator.add_background_music_to_video(
                        main_video, background_music, music_volume=0.15
                    )
                
                # If video is shorter than audio, pad with freeze frame
                if main_video.duration < audio_clip.duration:
                    pad_duration = audio_clip.duration - main_video.duration
                    last_frame = main_video.to_ImageClip(t=main_video.duration-0.05).set_duration(pad_duration)
                    main_video = concatenate_videoclips([main_video, last_frame])
                # Ensure video duration matches audio duration exactly
                main_video = main_video.set_duration(audio_clip.duration)
            elif include_music:
                # No voice audio but background music requested
                logger.info(f"Adding background music only: {background_music}")
                main_video = self.background_music_generator.add_background_music_to_video(
                    main_video, background_music, music_volume=0.5
                )

            # Export final video with maximum quality settings
            output_path = os.path.join(self.output_dir, f"{session_id}_ad_video.mp4")
            
            logger.info(f"Exporting video with duration: {actual_duration:.2f}s")
            logger.info(f"Using high-quality export settings for maximum image clarity")
            
            main_video.write_videofile(
                output_path,
                fps=self.fps,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile='temp-audio.m4a',
                remove_temp=True,
                verbose=False,
                logger=None,
                # High-quality video settings
                bitrate='8000k',           # High bitrate for better quality
                threads=4,                 # Multi-threading for faster processing
                # Audio quality settings
                audio_bitrate='192k',      # High audio bitrate
                # Additional quality parameters via ffmpeg_params
                ffmpeg_params=[
                    '-pix_fmt', 'yuv420p',     # Standard pixel format for compatibility
                    '-movflags', '+faststart',  # Optimize for web streaming
                    '-profile:v', 'high',       # High profile for better quality
                    '-level', '4.1',            # Compatibility level
                    '-tune', 'film',            # Optimize for film-like content
                    '-crf', '18',               # Constant Rate Factor (18 = high quality)
                    '-preset', 'slow',          # Better compression quality
                    '-x264opts', 'ref=6:deblock=1,1:me=umh:subme=9:chroma-qp-offset=-2:bframes=8:b-adapt=2'
                ]
            )
            
            # Clean up
            main_video.close()
            self._cleanup_temp_files(session_id)
            
            logger.info(f"Video generated successfully!")
            logger.info(f"Duration: {actual_duration:.2f}s")
            logger.info(f"Output: {output_path}")
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error in video generation: {str(e)}")
            # Throw exception instead of creating fallback video
            raise Exception(f"Video generation failed: {str(e)}")
    
    async def _create_simple_karaoke_video(self, ad_script: AdScript, image_paths, 
                                         width: int, height: int, template: str, 
                                         karaoke_style: str, total_duration: float, 
                                         audio_result=None):
        """Create video with proper karaoke-style subtitles using word-level timing"""
        try:
            # Validate duration
            if total_duration <= 0:
                total_duration = 15.0
                logger.warning(f"Invalid duration in karaoke video, using fallback: {total_duration}s")
            
            # Enforce maximum duration
            if total_duration > self.max_duration:
                logger.warning(f"Karaoke video duration {total_duration:.2f}s exceeds maximum {self.max_duration}s, trimming")
                total_duration = self.max_duration
            
            colors = self.video_composer.color_schemes.get(template, self.video_composer.color_schemes["modern"])
            
            # Create background video with image slideshow
            background_clips = []
            
            if image_paths:
                images_per_duration = total_duration / len(image_paths)
                
                current_time = 0.0
                for i, image_path in enumerate(image_paths):
                    if current_time >= total_duration:
                        break
                        
                    duration = min(images_per_duration, total_duration - current_time)
                    bg_clip = self.image_processor.create_image_background(image_path, width, height, duration)
                    bg_clip = bg_clip.set_start(current_time)
                    background_clips.append(bg_clip)
                    current_time += duration
                
                # If we need more background, repeat images
                while current_time < total_duration:
                    for image_path in image_paths:
                        if current_time >= total_duration:
                            break
                        duration = min(images_per_duration, total_duration - current_time)
                        bg_clip = self.image_processor.create_image_background(image_path, width, height, duration)
                        bg_clip = bg_clip.set_start(current_time)
                        background_clips.append(bg_clip)
                        current_time += duration
            else:
                # Create a simple colored background if no images provided
                from moviepy.editor import ColorClip
                bg_clip = ColorClip(size=(width, height), color=(76, 205, 196), duration=total_duration)
                background_clips.append(bg_clip)
            
            # Create karaoke subtitle clips if we have audio with word timings
            subtitle_clips = []
            
            if audio_result and audio_result.word_timings and len(audio_result.word_timings) > 0:
                logger.info(f"Creating karaoke subtitles with {len(audio_result.word_timings)} word timings")
                
                # Convert word timings to karaoke segments
                from backend.services.video.renderers.karaoke_renderer import KaraokeSegment, WordTiming
                
                # Create script segments from ad script
                script_parts = [
                    ad_script.hook,
                    f"{ad_script.problem} {ad_script.solution}",
                    " and ".join(ad_script.benefits[:2]) if ad_script.benefits else "",
                    ad_script.call_to_action
                ]
                full_script = ". ".join([part.strip() for part in script_parts if part.strip()])
                
                # Convert AudioResult word timings to KaraokeSegment format
                karaoke_word_timings = []
                for word_timing in audio_result.word_timings:
                    karaoke_word_timings.append(WordTiming(
                        word=word_timing.word,
                        start=word_timing.start,
                        end=word_timing.end
                    ))
                
                # Create a single karaoke segment for the entire script
                karaoke_segment = KaraokeSegment(
                    full_text=full_script,
                    start_time=0.0,
                    end_time=total_duration,
                    words=karaoke_word_timings
                )
                
                # Use the karaoke text renderer to create subtitle clips
                karaoke_clips = self.karaoke_renderer.create_karaoke_subtitle_clips(
                    [karaoke_segment], width, height, colors, karaoke_style
                )
                
                subtitle_clips.extend(karaoke_clips)
                logger.info(f"Created {len(karaoke_clips)} karaoke subtitle clips")
                
            else:
                logger.info(f"Creating basic text overlay (no word timings available)")
                # Fallback to basic text overlay if no word timings
                script_text = f"{ad_script.hook} {ad_script.problem} {ad_script.solution} {ad_script.call_to_action}"
                
                text_clip = self.text_renderer.create_text_overlay(
                    script_text, width, height, total_duration, colors, "bottom"
                )
                if text_clip:
                    subtitle_clips.append(text_clip)
            
            # Composite all clips
            from moviepy.editor import CompositeVideoClip
            all_clips = background_clips + subtitle_clips
            final_video = CompositeVideoClip(all_clips, size=(width, height))
            final_video = final_video.set_duration(total_duration)
            
            # Ensure the final video has the exact duration
            if abs(final_video.duration - total_duration) > 0.1:
                final_video = final_video.set_duration(total_duration)
                logger.info(f"Adjusted final video duration to {total_duration:.2f}s")
            
            logger.info(f"Created karaoke video with {len(subtitle_clips)} subtitle clips and {len(background_clips)} background clips")
            logger.info(f"Final video duration: {final_video.duration:.2f}s")
            return final_video
            
        except Exception as e:
            logger.error(f"Error creating karaoke video: {str(e)}")
            # Throw exception instead of fallback
            raise Exception(f"Karaoke video creation failed: {str(e)}")
    
    async def _create_basic_subtitle_video(self, ad_script: AdScript, image_paths, 
                                         width: int, height: int, template: str, 
                                         total_duration: float, audio_result=None):
        """Create video with basic subtitles positioned at the bottom (no karaoke)"""
        try:
            # Validate duration
            if total_duration <= 0:
                total_duration = 15.0
                logger.warning(f"Invalid duration in basic subtitle video, using fallback: {total_duration}s")
            
            # Enforce maximum duration
            if total_duration > self.max_duration:
                logger.warning(f"Basic subtitle video duration {total_duration:.2f}s exceeds maximum {self.max_duration}s, trimming")
                total_duration = self.max_duration
            
            colors = self.video_composer.color_schemes.get(template, self.video_composer.color_schemes["modern"])
            
            # Create background video with image slideshow
            background_clips = []
            
            if image_paths:
                images_per_duration = total_duration / len(image_paths)
                
                current_time = 0.0
                for i, image_path in enumerate(image_paths):
                    if current_time >= total_duration:
                        break
                        
                    duration = min(images_per_duration, total_duration - current_time)
                    bg_clip = self.image_processor.create_image_background(image_path, width, height, duration)
                    bg_clip = bg_clip.set_start(current_time)
                    background_clips.append(bg_clip)
                    current_time += duration
                
                # If we need more background, repeat images
                while current_time < total_duration:
                    for image_path in image_paths:
                        if current_time >= total_duration:
                            break
                        duration = min(images_per_duration, total_duration - current_time)
                        bg_clip = self.image_processor.create_image_background(image_path, width, height, duration)
                        bg_clip = bg_clip.set_start(current_time)
                        background_clips.append(bg_clip)
                        current_time += duration
            else:
                # Create a simple colored background if no images provided
                from moviepy.editor import ColorClip
                bg_clip = ColorClip(size=(width, height), color=(76, 205, 196), duration=total_duration)
                background_clips.append(bg_clip)
            
            # Create basic subtitle clips positioned at bottom
            subtitle_clips = []
            
            if audio_result and audio_result.audio_path:
                logger.info("Creating basic subtitles at bottom of screen")
                
                # Create script text for subtitles
                script_parts = [
                    ad_script.hook,
                    f"{ad_script.problem} {ad_script.solution}",
                    " and ".join(ad_script.benefits[:2]) if ad_script.benefits else "",
                    ad_script.call_to_action
                ]
                full_script = ". ".join([part.strip() for part in script_parts if part.strip()])
                
                # Create subtitle clip positioned at bottom
                text_clip = self.text_renderer.create_text_overlay(
                    full_script, width, height, total_duration, colors, "bottom"
                )
                if text_clip:
                    subtitle_clips.append(text_clip)
                    logger.info("Created basic subtitle clip at bottom")
            
            # Composite all clips
            from moviepy.editor import CompositeVideoClip
            all_clips = background_clips + subtitle_clips
            final_video = CompositeVideoClip(all_clips, size=(width, height))
            final_video = final_video.set_duration(total_duration)
            
            # Ensure the final video has the exact duration
            if abs(final_video.duration - total_duration) > 0.1:
                final_video = final_video.set_duration(total_duration)
                logger.info(f"Adjusted final video duration to {total_duration:.2f}s")
            
            logger.info(f"Created basic subtitle video with {len(subtitle_clips)} subtitle clips and {len(background_clips)} background clips")
            logger.info(f"Final video duration: {final_video.duration:.2f}s")
            return final_video
            
        except Exception as e:
            logger.error(f"Error creating basic subtitle video: {str(e)}")
            # Throw exception instead of fallback
            raise Exception(f"Basic subtitle video creation failed: {str(e)}")
    
    async def _create_video_without_subtitles(self, ad_script: AdScript, image_paths, 
                                            width: int, height: int, template: str, 
                                            total_duration: float):
        """Create video without any subtitles (clean background only)"""
        try:
            # Validate duration
            if total_duration <= 0:
                total_duration = 15.0
                logger.warning(f"Invalid duration in video without subtitles, using fallback: {total_duration}s")
            
            # Enforce maximum duration
            if total_duration > self.max_duration:
                logger.warning(f"Video without subtitles duration {total_duration:.2f}s exceeds maximum {self.max_duration}s, trimming")
                total_duration = self.max_duration
            
            # Create background video with image slideshow
            background_clips = []
            
            if image_paths:
                images_per_duration = total_duration / len(image_paths)
                
                current_time = 0.0
                for i, image_path in enumerate(image_paths):
                    if current_time >= total_duration:
                        break
                        
                    duration = min(images_per_duration, total_duration - current_time)
                    bg_clip = self.image_processor.create_image_background(image_path, width, height, duration)
                    bg_clip = bg_clip.set_start(current_time)
                    background_clips.append(bg_clip)
                    current_time += duration
                
                # If we need more background, repeat images
                while current_time < total_duration:
                    for image_path in image_paths:
                        if current_time >= total_duration:
                            break
                        duration = min(images_per_duration, total_duration - current_time)
                        bg_clip = self.image_processor.create_image_background(image_path, width, height, duration)
                        bg_clip = bg_clip.set_start(current_time)
                        background_clips.append(bg_clip)
                        current_time += duration
            else:
                # Create a simple colored background if no images provided
                from moviepy.editor import ColorClip
                bg_clip = ColorClip(size=(width, height), color=(76, 205, 196), duration=total_duration)
                background_clips.append(bg_clip)
            
            # Composite all clips
            from moviepy.editor import CompositeVideoClip
            final_video = CompositeVideoClip(background_clips, size=(width, height))
            final_video = final_video.set_duration(total_duration)
            
            # Ensure the final video has the exact duration
            if abs(final_video.duration - total_duration) > 0.1:
                final_video = final_video.set_duration(total_duration)
                logger.info(f"Adjusted final video duration to {total_duration:.2f}s")
            
            logger.info(f"Created video without subtitles with {len(background_clips)} background clips")
            logger.info(f"Final video duration: {final_video.duration:.2f}s")
            return final_video
            
        except Exception as e:
            logger.error(f"Error creating video without subtitles: {str(e)}")
            # Throw exception instead of fallback
            raise Exception(f"Video without subtitles creation failed: {str(e)}")
    
    def _cleanup_temp_files(self, session_id: str):
        """Clean up temporary files for a session"""
        try:
            import glob
            import os
            
            # Find all temp files for this session
            pattern = os.path.join(self.temp_dir, f"{session_id}_*")
            temp_files = glob.glob(pattern)
            
            # Remove temp files
            for file_path in temp_files:
                try:
                    os.remove(file_path)
                    logger.debug(f"Removed temp file: {file_path}")
                except Exception as e:
                    logger.debug(f"Failed to remove temp file {file_path}: {str(e)}")
            
            logger.info(f"Cleaned up {len(temp_files)} temp files for session {session_id}")
            
        except Exception as e:
            logger.warning(f"Error cleaning up temp files: {str(e)}")
    
    def get_available_voice_tones(self):
        """Get available voice tones"""
        return self.audio_generator.get_available_voices()
    
    def get_karaoke_styles(self):
        """Get available karaoke styles"""
        return ["default", "modern", "minimalist", "dynamic"]
    
    def get_background_music_styles(self):
        """Get available background music styles"""
        return self.background_music_generator.get_available_music_styles()
    
    def get_max_duration(self) -> int:
        """Get maximum video duration in seconds"""
        return self.max_duration
    
    def is_elevenlabs_available(self) -> bool:
        """Check if ElevenLabs is available"""
        return self.audio_generator.is_available() 