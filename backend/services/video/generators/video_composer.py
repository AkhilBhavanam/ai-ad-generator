import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from moviepy.editor import VideoClip, CompositeVideoClip, ColorClip, ImageClip
from moviepy.video.fx import resize, fadein, fadeout

from backend.core.models import ProductData, AdScript, VideoScene
from backend.services.video.generators.subtitle_generator import SubtitleSegment
from backend.services.video.processors.image_processor import ImageProcessor
from backend.services.video.renderers.text_renderer import TextRenderer

logger = logging.getLogger(__name__)

class VideoComposer:
    """Handles the main video composition and assembly logic"""
    
    def __init__(self, temp_dir: str = "temp_assets"):
        self.temp_dir = temp_dir
        self.image_processor = ImageProcessor(temp_dir)
        self.text_renderer = TextRenderer(temp_dir)
        
        # Video settings
        self.fps = 30
        
        # Color schemes
        self.color_schemes = {
            "modern": {
                "primary": "#FF6B6B",
                "secondary": "#4ECDC4", 
                "background": "#2C3E50",
                "text": "#FFFFFF"
            },
            "minimalist": {
                "primary": "#000000",
                "secondary": "#888888",
                "background": "#FFFFFF", 
                "text": "#000000"
            },
            "dynamic": {
                "primary": "#FF4081",
                "secondary": "#00BCD4",
                "background": "#1A1A1A",
                "text": "#FFFFFF"
            }
        }
    
    async def create_video_with_srt_timing(self, subtitle_segments: List[SubtitleSegment], 
                                         image_paths: List[str], width: int, height: int, 
                                         template: str, total_duration: float) -> VideoClip:
        """Create video using SRT timing for precise subtitle synchronization"""
        try:
            colors = self.color_schemes[template]
            
            # Create background video with image slideshow
            background_clips = []
            images_per_duration = total_duration / len(image_paths) if image_paths else total_duration
            
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
            
            # Create subtitle clips with precise timing
            subtitle_clips = []
            for segment in subtitle_segments:
                duration = segment.end_time - segment.start_time
                
                if duration > 0.1:  # Only create clip if duration is meaningful
                    text_clip = self.text_renderer.create_subtitle_clip(
                        segment.text, width, height, duration, colors
                    )
                    text_clip = text_clip.set_start(segment.start_time)
                    subtitle_clips.append(text_clip)
            
            # Combine all clips
            all_clips = background_clips + subtitle_clips
            final_video = CompositeVideoClip(all_clips, size=(width, height))
            final_video = final_video.set_duration(total_duration)
            
            logger.info(f"Created video with {len(subtitle_clips)} subtitle segments and {len(background_clips)} background clips")
            
            return final_video
            
        except Exception as e:
            logger.error(f"Error creating video with SRT timing: {str(e)}")
            # Fallback to simple background
            return ColorClip(size=(width, height), color=(76, 205, 196), duration=total_duration)
    
    async def create_video_with_scenes(self, scenes: List[VideoScene], 
                                     width: int, height: int, template: str) -> VideoClip:
        """Create video using traditional scene-based approach"""
        try:
            clips = []
            colors = self.color_schemes[template]
            
            for scene in scenes:
                clip = await self._create_scene_clip(scene, width, height, colors)
                clips.append(clip)
            
            final_video = concatenate_videoclips(clips)
            return final_video
            
        except Exception as e:
            logger.error(f"Error creating video with scenes: {str(e)}")
            # Fallback video
            return ColorClip(size=(width, height), color=(76, 205, 196), duration=15)
    
    async def _create_scene_clip(self, scene: VideoScene, width: int, height: int, colors: Dict[str, str]) -> VideoClip:
        """Create a single scene clip"""
        try:
            scene_duration = scene.end_time - scene.start_time
            
            # Create background
            if scene.image_url and os.path.exists(scene.image_url):
                background = self.image_processor.create_image_background(
                    scene.image_url, width, height, scene_duration
                )
            else:
                # Solid color background
                background = ColorClip(
                    size=(width, height), 
                    color=(76, 205, 196), 
                    duration=scene_duration
                )
            
            clips = [background]
            
            # Add text overlay if present
            if scene.text:
                text_position = "center"
                if "call" in scene.text.lower() or "action" in scene.text.lower():
                    text_position = "bottom"
                elif len(scene.text) < 30:
                    text_position = "top"
                
                text_clip = self.text_renderer.create_text_overlay(
                    scene.text, width, height, scene_duration, colors, text_position
                )
                clips.append(text_clip)
            
            # Composite all clips
            final_clip = CompositeVideoClip(clips, size=(width, height))
            return final_clip
            
        except Exception as e:
            logger.warning(f"Error creating scene clip: {str(e)}")
            # Return simple background as fallback
            scene_duration = scene.end_time - scene.start_time
            return ColorClip(size=(width, height), color=(76, 205, 196), duration=scene_duration)
    
    def create_scenes_with_timing(self, ad_script: AdScript, image_paths: List[str], total_duration: float) -> List[VideoScene]:
        """Create scenes from ad script with timing calculations"""
        try:
            scenes = []
            
            # Define scene content and relative durations
            scene_configs = [
                {"text": ad_script.hook, "weight": 0.25},
                {"text": f"{ad_script.problem} {ad_script.solution}", "weight": 0.35},
                {"text": " and ".join(ad_script.benefits[:2]) if ad_script.benefits else "", "weight": 0.25},
                {"text": ad_script.call_to_action, "weight": 0.15}
            ]
            
            # Filter out empty scenes
            scene_configs = [config for config in scene_configs if config["text"].strip()]
            
            # Calculate durations and timing
            total_weight = sum(config["weight"] for config in scene_configs)
            current_time = 0.0
            
            for i, config in enumerate(scene_configs):
                duration = (config["weight"] / total_weight) * total_duration
                image_path = image_paths[i % len(image_paths)] if image_paths else None
                
                scene = VideoScene(
                    start_time=current_time,
                    end_time=current_time + duration,
                    text=config["text"],
                    image_url=image_path,
                    animation_type="fade"
                )
                scenes.append(scene)
                current_time += duration
            
            logger.info(f"Created {len(scenes)} scenes with total duration {total_duration:.2f}s")
            return scenes
            
        except Exception as e:
            logger.error(f"Error creating scenes with timing: {str(e)}")
            # Return single fallback scene
            return [VideoScene(
                start_time=0.0,
                end_time=total_duration,
                text="Amazing Product Available Now!",
                image_url=image_paths[0] if image_paths else None,
                animation_type="fade"
            )]
    
    def get_dimensions(self, aspect_ratio: str) -> Tuple[int, int]:
        """Get video dimensions based on aspect ratio"""
        aspect_ratios = {
            "16:9": (1920, 1080),  # Landscape/YouTube
            "9:16": (1080, 1920),  # Portrait/TikTok/Instagram Stories  
            "1:1": (1080, 1080),   # Square/Instagram
            "4:3": (1440, 1080),   # Traditional TV
        }
        
        return aspect_ratios.get(aspect_ratio, (1920, 1080))
    
    async def create_fallback_video(self, session_id: str, aspect_ratio: str) -> str:
        """Create a simple fallback video when main generation fails"""
        try:
            width, height = self.get_dimensions(aspect_ratio)
            
            # Create simple animated background
            background = ColorClip(size=(width, height), color=(76, 205, 196), duration=10)
            
            # Add fallback text
            text_clip = self.text_renderer.create_text_overlay(
                "Video generation in progress...\nCheck back soon!", 
                width, height, 10, 
                self.color_schemes["modern"], 
                "center"
            )
            
            # Combine clips
            final_video = CompositeVideoClip([background, text_clip], size=(width, height))
            
            # Export
            output_path = os.path.join("generated_videos", f"{session_id}_fallback_video.mp4")
            final_video.write_videofile(
                output_path,
                fps=self.fps,
                codec='libx264',
                verbose=False,
                logger=None
            )
            
            final_video.close()
            
            logger.info(f"Created fallback video: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error creating fallback video: {str(e)}")
            return "" 