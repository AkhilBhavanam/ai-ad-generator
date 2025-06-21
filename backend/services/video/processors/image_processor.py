import os
import logging
from typing import List, Optional, Tuple
from PIL import Image, ImageEnhance, ImageFilter
import numpy as np
import math
from moviepy.editor import ImageClip, ColorClip, CompositeVideoClip, VideoClip

logger = logging.getLogger(__name__)

class ImageProcessor:
    """Handles image downloading, processing, and background creation"""
    
    def __init__(self, temp_dir: str = "temp_assets"):
        self.temp_dir = temp_dir
        os.makedirs(self.temp_dir, exist_ok=True)
    
    async def download_images(self, image_urls: List[str], session_id: str, video_dimensions: tuple = None) -> List[str]:
        """Download product images with error handling and optional pre-sizing"""
        try:
            image_paths = []
            
            for i, url in enumerate(image_urls[:5]):  # Limit to 5 images
                try:
                    logger.info(f"Downloading image {i+1}: {url}")
                    
                    # Download image
                    response = requests.get(url, timeout=10)
                    response.raise_for_status()
                    
                    # Save image
                    image_path = os.path.join(self.temp_dir, f"{session_id}_image_{i}.jpg")
                    with open(image_path, 'wb') as f:
                        f.write(response.content)
                    
                    # Process and validate image with optional target size
                    processed_path = await self._process_image(image_path, session_id, i, video_dimensions)
                    if processed_path:
                        image_paths.append(processed_path)
                    
                except Exception as e:
                    logger.warning(f"Failed to download image {i+1}: {str(e)}")
                    continue
            
            # If no images downloaded, create placeholder
            if not image_paths:
                placeholder_path = self._create_placeholder_image(session_id)
                image_paths.append(placeholder_path)
            
            logger.info(f"Successfully processed {len(image_paths)} images")
            return image_paths
            
        except Exception as e:
            logger.error(f"Error downloading images: {str(e)}")
            # Return placeholder image
            return [self._create_placeholder_image(session_id)]
    
    async def _process_image(self, image_path: str, session_id: str, index: int, target_size: tuple = None) -> str:
        """Process and optimize image for video use with enhanced clarity and maximum quality preservation"""
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Get original size for better quality decisions
                orig_width, orig_height = img.size
                logger.debug(f"Original image size: {orig_width}x{orig_height}")
                
                # QUALITY PRESERVATION: Use higher resolution for better video quality
                # Target 4K resolution for maximum quality, even if video is smaller
                max_quality_size = (3840, 2160)  # 4K resolution
                
                # Use target video size if provided, otherwise use high resolution
                if target_size:
                    target_width, target_height = target_size
                    logger.debug(f"Target size: {target_width}x{target_height}")
                    
                    # Calculate the best fit maintaining aspect ratio
                    img_ratio = orig_width / orig_height
                    target_ratio = target_width / target_height
                    
                    if img_ratio > target_ratio:
                        # Image is wider - fit to width
                        new_width = target_width
                        new_height = int(target_width / img_ratio)
                    else:
                        # Image is taller - fit to height  
                        new_height = target_height
                        new_width = int(target_height * img_ratio)
                    
                    # FIXED: Don't scale up unnecessarily - use target size directly
                    # Only scale up if the image is much smaller than target
                    if orig_width < target_width * 0.8 or orig_height < target_height * 0.8:
                        # Image is significantly smaller, scale up for quality
                        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                        logger.debug(f"Scaled up image to: {new_width}x{new_height}")
                    else:
                        # Image is already close to target size, use as is
                        logger.debug(f"Using image at original size: {img.size}")
                    
                else:
                    # QUALITY PRESERVATION: Use maximum resolution for best quality
                    # Only resize if image is MUCH larger than target to preserve quality
                    if orig_width > max_quality_size[0] * 1.5 or orig_height > max_quality_size[1] * 1.5:
                        # Use LANCZOS resampling for best quality
                        img.thumbnail(max_quality_size, Image.Resampling.LANCZOS)
                        logger.debug(f"Minimal resize to max quality size: {img.size}")
                    else:
                        logger.debug(f"Preserving original size for maximum quality: {img.size}")
                
                # QUALITY ENHANCEMENT: Enhanced sharpening and clarity
                if img.size[0] > 300 and img.size[1] > 300:
                    try:
                        # Enhanced sharpening with better parameters
                        img = img.filter(ImageFilter.UnsharpMask(radius=1.0, percent=120, threshold=2))
                        
                        # Slight contrast enhancement for better visual quality
                        enhancer = ImageEnhance.Contrast(img)
                        img = enhancer.enhance(1.05)  # 5% contrast boost for clarity
                        
                        # Slight brightness adjustment for better visibility
                        brightness_enhancer = ImageEnhance.Brightness(img)
                        img = brightness_enhancer.enhance(1.02)  # 2% brightness boost
                        
                        logger.debug("Applied enhanced sharpening, contrast, and brightness")
                    except Exception as e:
                        logger.debug(f"Enhancement failed: {str(e)}")
                
                # QUALITY PRESERVATION: Save with MAXIMUM quality settings
                processed_path = os.path.join(
                    self.temp_dir, 
                    f"{session_id}_image_{index}_processed.jpg"
                )
                
                # Use maximum quality settings
                img.save(processed_path, 'JPEG', 
                        quality=100,           # Maximum quality (lossless-like)
                        optimize=True,         # File size optimization
                        progressive=True,      # Progressive JPEG for better quality
                        subsampling=0,         # No chroma subsampling for max quality
                        dpi=(300, 300))        # High DPI for better quality
                
                logger.debug(f"Saved MAXIMUM quality image: {processed_path}")
                
                # QUALITY VALIDATION: Verify the saved image quality
                try:
                    with Image.open(processed_path) as verify_img:
                        verify_size = verify_img.size
                        if verify_size[0] < 100 or verify_size[1] < 100:
                            logger.warning(f"Processed image seems too small: {verify_size}")
                        else:
                            logger.debug(f"Quality validation passed: {verify_size}")
                        
                        # Log quality metrics
                        self._log_quality_metrics(processed_path, "processed")
                        
                        # Validate overall quality
                        if not self._validate_image_quality(processed_path):
                            logger.warning(f"Processed image failed quality validation: {processed_path}")
                        else:
                            logger.debug(f"Processed image quality validation passed: {processed_path}")
                            
                except Exception as e:
                    logger.warning(f"Quality validation failed: {str(e)}")
                
                return processed_path
                
        except Exception as e:
            logger.warning(f"Error processing image {image_path}: {str(e)}")
            return None
    
    def _create_placeholder_image(self, session_id: str) -> str:
        """Create a placeholder image when product images aren't available"""
        try:
            # Create a simple gradient placeholder
            width, height = 1920, 1080
            img = Image.new('RGB', (width, height), '#4ECDC4')
            
            draw = ImageDraw.Draw(img)
            
            # Draw a simple pattern
            for i in range(0, width, 100):
                draw.line([(i, 0), (i + height//2, height)], fill='#FF6B6B', width=3)
            
            # Add text
            try:
                from PIL import ImageFont
                font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 60)
                text = "Product Image"
                
                # Get text dimensions
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                
                # Center text
                x = (width - text_width) // 2
                y = (height - text_height) // 2
                
                # Draw text with shadow
                draw.text((x+2, y+2), text, font=font, fill='#000000')
                draw.text((x, y), text, font=font, fill='#FFFFFF')
                
            except:
                # Fallback without custom font
                draw.text((width//2 - 100, height//2), "Product Image", fill='#FFFFFF')
            
            # Save placeholder
            placeholder_path = os.path.join(self.temp_dir, f"{session_id}_placeholder.jpg")
            img.save(placeholder_path, 'JPEG')
            
            return placeholder_path
            
        except Exception as e:
            logger.error(f"Error creating placeholder image: {str(e)}")
            # Return empty string if even placeholder creation fails
            return ""
    
    def _create_letterboxed_image(self, image_path: str, target_width: int, target_height: int, session_id: str, index: int) -> str:
        """Create a letterboxed version of the image with black bars (NO CROPPING) - Maximum Quality"""
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                orig_width, orig_height = img.size
                logger.debug(f"Creating letterbox: {orig_width}x{orig_height} -> {target_width}x{target_height}")
                
                # FIXED: Don't scale up unnecessarily - use target size directly
                # Calculate scale factor to fit image inside target (no cropping)
                scale_x = target_width / orig_width
                scale_y = target_height / orig_height
                scale = min(scale_x, scale_y)  # Use smaller scale to fit completely
                
                # Calculate new dimensions
                new_width = int(orig_width * scale)
                new_height = int(orig_height * scale)
                
                # QUALITY ENHANCEMENT: Resize with maximum quality
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Create letterboxed image with black background
                letterboxed = Image.new('RGB', (target_width, target_height), (0, 0, 0))
                
                # Center the image
                x_offset = (target_width - new_width) // 2
                y_offset = (target_height - new_height) // 2
                letterboxed.paste(img, (x_offset, y_offset))
                
                # QUALITY PRESERVATION: Save with maximum quality settings
                letterboxed_path = os.path.join(
                    self.temp_dir, 
                    f"{session_id}_letterbox_{index}.jpg"
                )
                
                letterboxed.save(letterboxed_path, 'JPEG',
                               quality=100,           # Maximum quality
                               optimize=True,         # File optimization
                               progressive=True,      # Progressive JPEG
                               subsampling=0,         # No chroma subsampling
                               dpi=(300, 300))        # High DPI
                
                logger.debug(f"Created high-quality letterboxed image: {target_width}x{target_height}")
                return letterboxed_path
                
        except Exception as e:
            logger.warning(f"Error creating letterboxed image: {str(e)}")
            return None
    
    def create_image_background(self, image_path: str, width: int, height: int, duration: float) -> VideoClip:
        """Create a video background from an image with maximum quality preservation (NO CROPPING)"""
        try:
            if not os.path.exists(image_path):
                logger.warning(f"Image path does not exist: {image_path}")
                # Return solid color background
                from moviepy.editor import ColorClip
                return ColorClip(size=(width, height), color=(76, 205, 196), duration=duration)
            
            # QUALITY PRESERVATION: Create image clip with maximum quality settings
            image = Image.open(image_path)
            
            # Ensure RGB format for MoviePy compatibility
            if image.mode != "RGB":
                image = image.convert("RGB")
            
            # Verify RGB array shape before MoviePy
            image_array = np.array(image)
            if len(image_array.shape) != 3 or image_array.shape[2] != 3:
                logger.warning(f"Invalid image array shape: {image_array.shape}, forcing RGB conversion")
                # Force RGB format
                image = Image.new('RGB', image.size, (255, 255, 255))
                image_array = np.array(image)
            
            # QUALITY ENHANCEMENT: Create clip with maximum quality
            clip = ImageClip(image_array, duration=duration)
            
            # Get current clip dimensions
            clip_width, clip_height = clip.size
            logger.debug(f"Original clip size: {clip_width}x{clip_height}, Target: {width}x{height}")
            
            # QUALITY PRESERVATION: Create letterboxed image with maximum quality
            # Extract session info from image path
            filename = os.path.basename(image_path)
            if '_image_' in filename:
                parts = filename.split('_image_')
                session_id = parts[0]
                index = parts[1].split('_')[0]
            else:
                session_id = "letterbox"
                index = "0"
            
            letterboxed_path = self._create_letterboxed_image(image_path, width, height, session_id, index)
            
            if letterboxed_path:
                # QUALITY PRESERVATION: Ensure ImageClip loads RGB format correctly
                try:
                    # Pre-load and verify image format before creating clip
                    from PIL import Image as PILImage
                    test_img = PILImage.open(letterboxed_path)
                    if test_img.mode != 'RGB':
                        # Convert to RGB and save again with maximum quality
                        test_img = test_img.convert('RGB')
                        test_img.save(letterboxed_path, 'JPEG', 
                                    quality=100, optimize=True, progressive=True, subsampling=0)
                    test_img.close()
                    
                    # Create clip from verified high-quality RGB image
                    clip = ImageClip(letterboxed_path, duration=duration)
                    logger.debug(f"Created high-quality letterboxed clip: {width}x{height}, no cropping")
                except Exception as clip_error:
                    logger.warning(f"Letterbox clip creation failed: {str(clip_error)}")
                    # Fallback to high-quality resize
                    clip = clip.resize((width, height), resample='lanczos')
                    logger.debug(f"Fallback high-quality resize: {width}x{height}")
            else:
                # Fallback: high-quality resize (may cause slight distortion but no cropping)
                clip = clip.resize((width, height), resample='lanczos')
                logger.debug(f"Fallback high-quality resize: {width}x{height}")
            
            # QUALITY PRESERVATION: Apply Ken Burns effect for engaging content
            clip = self._apply_animation(clip, "ken_burns")
            
            return clip
            
        except Exception as e:
            logger.warning(f"Error creating image background: {str(e)}")
            # Return solid color background as fallback
            from moviepy.editor import ColorClip
            return ColorClip(size=(width, height), color=(76, 205, 196), duration=duration)
    
    def _apply_animation(self, clip: VideoClip, animation_type: str) -> VideoClip:
        """Apply professional animation effects including Ken Burns, zoom, and camera motion"""
        try:
            if animation_type == "ken_burns":
                # 🎬 KEN BURNS EFFECT: Slow zoom + pan for cinematic feel
                return self._apply_ken_burns_effect(clip)
            elif animation_type == "zoom_in":
                # 🔍 SLOW ZOOM IN: Gradual zoom for product focus
                return self._apply_zoom_in_effect(clip)
            elif animation_type == "zoom_out":
                # 🔍 ZOOM OUT: Start close, reveal full product
                return self._apply_zoom_out_effect(clip)
            elif animation_type == "pan_left":
                # ➡️ PAN LEFT: Horizontal movement
                return self._apply_pan_effect(clip, "left")
            elif animation_type == "pan_right":
                # ⬅️ PAN RIGHT: Horizontal movement
                return self._apply_pan_effect(clip, "right")
            elif animation_type == "subtle_motion":
                # 🎭 SUBTLE MOTION: Slight movement for depth
                return self._apply_subtle_motion(clip)
            elif animation_type == "fade":
                # ✨ CLASSIC FADE: Subtle fade in/out effect - no quality loss
                fade_duration = min(0.5, clip.duration / 4)
                return clip.fadein(fade_duration).fadeout(fade_duration)
            elif animation_type == "none":
                # 🚫 NO ANIMATION: Preserve original quality
                return clip
            else:
                # 🎲 DEFAULT: Use Ken Burns for engaging content
                return self._apply_ken_burns_effect(clip)
        except Exception as e:
            logger.warning(f"Error applying animation: {str(e)}")
            return clip

    def _apply_ken_burns_effect(self, clip: VideoClip) -> VideoClip:
        """Apply professional Ken Burns effect: very subtle zoom + pan"""
        try:
            duration = clip.duration
            
            # FIXED: Much more subtle Ken Burns parameters
            zoom_start = 1.0      # Start at normal size
            zoom_end = 1.05       # End very slightly zoomed (5% larger - much more subtle)
            
            # FIXED: Minimal pan movement for natural feel
            import random
            pan_x_start = random.uniform(-5, 5)      # Very small start position offset
            pan_x_end = random.uniform(-5, 5)        # Very small end position offset  
            pan_y_start = random.uniform(-3, 3)      # Very small vertical movement
            pan_y_end = random.uniform(-3, 3)
            
            def ken_burns_transform(t):
                # Calculate progress (0 to 1)
                progress = t / duration
                
                # Smooth easing function (ease-in-out)
                eased_progress = 0.5 * (1 - math.cos(math.pi * progress))
                
                # Calculate current zoom level
                current_zoom = zoom_start + (zoom_end - zoom_start) * eased_progress
                
                # Calculate current pan position
                current_x = pan_x_start + (pan_x_end - pan_x_start) * eased_progress
                current_y = pan_y_start + (pan_y_end - pan_y_start) * eased_progress
                
                return current_zoom, (current_x, current_y)
            
            # Apply Ken Burns transformation
            animated_clip = clip.resize(lambda t: ken_burns_transform(t)[0])
            animated_clip = animated_clip.set_position(lambda t: ken_burns_transform(t)[1])
            
            # Add very subtle fade for polish
            fade_duration = min(0.2, duration / 8)
            animated_clip = animated_clip.fadein(fade_duration).fadeout(fade_duration)
            
            logger.debug(f"Applied subtle Ken Burns effect: zoom {zoom_start}->{zoom_end}, pan ({pan_x_start:.1f},{pan_y_start:.1f})->({pan_x_end:.1f},{pan_y_end:.1f})")
            return animated_clip
            
        except Exception as e:
            logger.warning(f"Ken Burns effect failed: {str(e)}")
            return clip

    def _apply_zoom_in_effect(self, clip: VideoClip) -> VideoClip:
        """Apply slow zoom-in effect for product focus"""
        try:
            duration = clip.duration
            zoom_start = 1.0      # Start normal
            zoom_end = 1.25       # End 25% larger
            
            def zoom_function(t):
                progress = t / duration
                # Smooth acceleration (ease-out)
                eased_progress = 1 - (1 - progress) ** 2
                return zoom_start + (zoom_end - zoom_start) * eased_progress
            
            animated_clip = clip.resize(zoom_function)
            
            # Add fade for smooth start/end
            fade_duration = min(0.4, duration / 5)
            animated_clip = animated_clip.fadein(fade_duration).fadeout(fade_duration)
            
            logger.debug(f"Applied zoom-in effect: {zoom_start} -> {zoom_end}")
            return animated_clip
            
        except Exception as e:
            logger.warning(f"Zoom-in effect failed: {str(e)}")
            return clip

    def _apply_zoom_out_effect(self, clip: VideoClip) -> VideoClip:
        """Apply zoom-out effect to reveal full product"""
        try:
            duration = clip.duration
            zoom_start = 1.3      # Start zoomed in
            zoom_end = 1.0        # End at normal size
            
            def zoom_function(t):
                progress = t / duration
                # Smooth deceleration (ease-in)
                eased_progress = progress ** 2
                return zoom_start + (zoom_end - zoom_start) * eased_progress
            
            animated_clip = clip.resize(zoom_function)
            
            # Add fade
            fade_duration = min(0.4, duration / 5)
            animated_clip = animated_clip.fadein(fade_duration).fadeout(fade_duration)
            
            logger.debug(f"Applied zoom-out effect: {zoom_start} -> {zoom_end}")
            return animated_clip
            
        except Exception as e:
            logger.warning(f"Zoom-out effect failed: {str(e)}")
            return clip

    def _apply_pan_effect(self, clip: VideoClip, direction: str) -> VideoClip:
        """Apply horizontal or vertical pan effect"""
        try:
            duration = clip.duration
            
            if direction == "left":
                start_pos = (30, 0)    # Start right
                end_pos = (-30, 0)     # End left
            elif direction == "right": 
                start_pos = (-30, 0)   # Start left
                end_pos = (30, 0)      # End right
            elif direction == "up":
                start_pos = (0, 20)    # Start down
                end_pos = (0, -20)     # End up
            elif direction == "down":
                start_pos = (0, -20)   # Start up
                end_pos = (0, 20)      # End down
            else:
                start_pos = (0, 0)
                end_pos = (0, 0)
            
            def pan_function(t):
                progress = t / duration
                # Smooth motion (ease-in-out)
                eased_progress = 0.5 * (1 - math.cos(math.pi * progress))
                
                current_x = start_pos[0] + (end_pos[0] - start_pos[0]) * eased_progress
                current_y = start_pos[1] + (end_pos[1] - start_pos[1]) * eased_progress
                
                return (current_x, current_y)
            
            animated_clip = clip.set_position(pan_function)
            
            # Add fade
            fade_duration = min(0.3, duration / 6)
            animated_clip = animated_clip.fadein(fade_duration).fadeout(fade_duration)
            
            logger.debug(f"Applied pan effect: {direction} from {start_pos} to {end_pos}")
            return animated_clip
            
        except Exception as e:
            logger.warning(f"Pan effect failed: {str(e)}")
            return clip

    def _apply_subtle_motion(self, clip: VideoClip) -> VideoClip:
        """Apply very subtle camera motion for depth and engagement"""
        try:
            duration = clip.duration
            
            # Very subtle motion parameters
            zoom_amplitude = 0.02    # ±2% zoom variation
            pan_amplitude = 5        # ±5px movement
            
            def subtle_motion(t):
                # Use sine waves for smooth, organic motion
                time_factor = 2 * math.pi * t / duration
                
                # Subtle zoom breathing effect
                zoom_variation = 1 + zoom_amplitude * math.sin(time_factor * 0.7)
                
                # Gentle drift motion
                x_drift = pan_amplitude * math.sin(time_factor * 0.5)
                y_drift = pan_amplitude * math.cos(time_factor * 0.3) * 0.6
                
                return zoom_variation, (x_drift, y_drift)
            
            # Apply subtle transformations
            animated_clip = clip.resize(lambda t: subtle_motion(t)[0])
            animated_clip = animated_clip.set_position(lambda t: subtle_motion(t)[1])
            
            # Very gentle fade
            fade_duration = min(0.2, duration / 8)
            animated_clip = animated_clip.fadein(fade_duration).fadeout(fade_duration)
            
            logger.debug("Applied subtle motion effect for depth")
            return animated_clip
            
        except Exception as e:
            logger.warning(f"Subtle motion effect failed: {str(e)}")
            return clip

    def _validate_image_quality(self, image_path: str, min_width: int = 300, min_height: int = 300) -> bool:
        """Validate image quality and return True if quality standards are met"""
        try:
            with Image.open(image_path) as img:
                width, height = img.size
                
                # Check minimum size requirements
                if width < min_width or height < min_height:
                    logger.warning(f"Image quality check failed: {width}x{height} below minimum {min_width}x{min_height}")
                    return False
                
                # Check file size (should be reasonable for quality)
                file_size = os.path.getsize(image_path)
                if file_size < 10000:  # Less than 10KB might indicate poor quality
                    logger.warning(f"Image file size too small: {file_size} bytes")
                    return False
                
                # Check if image is not completely blank or single color
                img_array = np.array(img)
                if len(img_array.shape) == 3:
                    # Check color variance
                    color_variance = np.var(img_array)
                    if color_variance < 100:  # Very low variance might indicate poor quality
                        logger.warning(f"Image has very low color variance: {color_variance}")
                        return False
                
                logger.debug(f"Image quality validation passed: {width}x{height}, {file_size} bytes")
                return True
                
        except Exception as e:
            logger.warning(f"Image quality validation failed: {str(e)}")
            return False
    
    def _log_quality_metrics(self, image_path: str, stage: str):
        """Log quality metrics for monitoring"""
        try:
            with Image.open(image_path) as img:
                width, height = img.size
                file_size = os.path.getsize(image_path)
                logger.debug(f"Quality metrics [{stage}]: {width}x{height}, {file_size} bytes")
        except Exception as e:
            logger.debug(f"Could not log quality metrics: {str(e)}") 