import os
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from moviepy.editor import ImageClip, VideoClip, CompositeVideoClip

logger = logging.getLogger(__name__)

class TextRenderer:
    """Handles text rendering and overlay creation for videos"""
    
    def __init__(self, temp_dir: str = "temp_assets"):
        self.temp_dir = temp_dir
        os.makedirs(self.temp_dir, exist_ok=True)
    
    def create_subtitle_clip(self, text: str, width: int, height: int, 
                           duration: float, colors: Dict[str, str]) -> VideoClip:
        """Create a subtitle clip with professional styling"""
        try:
            # FIXED: Much smaller, responsive font size
            if width >= 1920:  # 4K/Full HD
                font_size = 36
            elif width >= 1280:  # HD
                font_size = 28
            elif width >= 854:   # SD
                font_size = 24
            else:  # Very small
                font_size = 20
            
            # FIXED: Larger canvas to prevent cropping 
            img_width = int(width * 0.95)  # Wider canvas
            img_height = int(height * 0.3)  # Taller canvas for multi-line text
            
            # Create image with transparent background
            img = Image.new('RGBA', (img_width, img_height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            # Load font
            font = self._load_font(font_size)
            
            # IMPROVED: Better word wrapping with more space
            wrapped_text = self._wrap_text(text, font, img_width - 60)
            
            # Calculate text position (center vertically in canvas)
            bbox = draw.multiline_textbbox((0, 0), wrapped_text, font=font, spacing=4)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            x = (img_width - text_width) // 2
            y = (img_height - text_height) // 2
            
            # IMPROVED: Subtle background with better styling
            padding = 15
            box_coords = [
                x - padding,
                y - padding,
                x + text_width + padding,
                y + text_height + padding
            ]
            # More subtle background
            draw.rounded_rectangle(box_coords, radius=8, fill=(0, 0, 0, 140))
            
            # IMPROVED: More stylish text with thinner outline
            self._draw_text_with_outline(draw, (x, y), wrapped_text, font)
            
            # FIXED: Ensure RGB format before saving for MoviePy compatibility
            if img.mode != 'RGB':
                # Convert RGBA to RGB with white background
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = rgb_img
            
            # Save temporary image
            temp_path = os.path.join(self.temp_dir, f"subtitle_{int(datetime.now().timestamp() * 1000)}.png")
            img.save(temp_path, 'PNG')
            
            # Create video clip from image
            text_clip = ImageClip(temp_path, duration=duration)
            
            # FIXED: Position higher to prevent bottom cutoff
            text_clip = text_clip.set_position(('center', height * 0.75))
            
            # IMPROVED: Smoother fade transitions  
            fade_duration = min(0.15, duration / 5)
            text_clip = text_clip.fadein(fade_duration).fadeout(fade_duration)
            
            return text_clip
            
        except Exception as e:
            logger.warning(f"Error creating subtitle clip: {str(e)}")
            # Return transparent clip as fallback
            from moviepy.editor import ColorClip
            return ColorClip(size=(width, height), color=(0,0,0), duration=duration).set_opacity(0)
    
    def create_text_overlay(self, text: str, width: int, height: int, 
                          duration: float, colors: Dict[str, str], position: str = "center") -> VideoClip:
        """Create a text overlay clip with customizable positioning and styling"""
        try:
            # Determine font size based on video dimensions
            if width >= 1920:  # 4K/Full HD
                font_size = 72
            elif width >= 1280:  # HD
                font_size = 56
            else:  # SD
                font_size = 40
            
            # Create image canvas
            img_width = int(width * 0.8)
            img_height = int(height * 0.6)
            
            img = Image.new('RGBA', (img_width, img_height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            # Load font
            font = self._load_font(font_size)
            
            # Word wrap text
            wrapped_text = self._wrap_text(text, font, img_width - 80)
            
            # Calculate text dimensions and position
            bbox = draw.multiline_textbbox((0, 0), wrapped_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Position text based on parameter
            if position == "top":
                x = (img_width - text_width) // 2
                y = 40
            elif position == "bottom":
                x = (img_width - text_width) // 2
                y = img_height - text_height - 40
            else:  # center
                x = (img_width - text_width) // 2
                y = (img_height - text_height) // 2
            
            # Create background for better readability
            padding = 30
            bg_coords = [
                x - padding,
                y - padding,
                x + text_width + padding,
                y + text_height + padding
            ]
            
            # Use colors from scheme
            bg_color = colors.get("background", "#2C3E50")
            bg_rgba = self._hex_to_rgba(bg_color, alpha=200)
            draw.rounded_rectangle(bg_coords, radius=15, fill=bg_rgba)
            
            # Draw text with outline
            self._draw_text_with_outline(draw, (x, y), wrapped_text, font, 
                                       text_color=colors.get("text", "#FFFFFF"))
            
            # FIXED: Ensure RGB format before saving for MoviePy compatibility
            if img.mode != 'RGB':
                # Convert RGBA to RGB with white background
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = rgb_img
            
            # Save temporary image
            temp_path = os.path.join(self.temp_dir, f"text_overlay_{int(datetime.now().timestamp() * 1000)}.png")
            img.save(temp_path, 'PNG')
            
            # Create video clip
            text_clip = ImageClip(temp_path, duration=duration)
            
            # Position on video
            if position == "top":
                text_clip = text_clip.set_position(('center', 'top'))
            elif position == "bottom":
                text_clip = text_clip.set_position(('center', 'bottom'))
            else:
                text_clip = text_clip.set_position('center')
            
            # Add fade effects
            fade_duration = min(0.3, duration / 3)
            text_clip = text_clip.fadein(fade_duration).fadeout(fade_duration)
            
            return text_clip
            
        except Exception as e:
            logger.warning(f"Error creating text overlay: {str(e)}")
            from moviepy.editor import ColorClip
            return ColorClip(size=(width, height), color=(0,0,0), duration=duration).set_opacity(0)
    
    def _load_font(self, font_size: int) -> ImageFont.FreeTypeFont:
        """Load the best available font"""
        font_paths = [
            "/System/Library/Fonts/Arial.ttf",  # macOS
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",  # Linux
            "C:/Windows/Fonts/arial.ttf",  # Windows
        ]
        
        for font_path in font_paths:
            try:
                return ImageFont.truetype(font_path, font_size)
            except:
                continue
        
        # Fallback to default font
        return ImageFont.load_default()
    
    def _wrap_text(self, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> str:
        """Wrap text to fit within specified width"""
        try:
            words = text.split()
            lines = []
            current_line = []
            
            for word in words:
                test_line = ' '.join(current_line + [word])
                
                # Use textbbox for accurate measurement
                bbox = font.getbbox(test_line)
                text_width = bbox[2] - bbox[0]
                
                if text_width <= max_width:
                    current_line.append(word)
                else:
                    if current_line:
                        lines.append(' '.join(current_line))
                        current_line = [word]
                    else:
                        # Word too long, add it anyway
                        lines.append(word)
            
            if current_line:
                lines.append(' '.join(current_line))
            
            return '\n'.join(lines)
            
        except Exception as e:
            logger.warning(f"Error wrapping text: {str(e)}")
            return text
    
    def _draw_text_with_outline(self, draw: ImageDraw.Draw, position: tuple, 
                              text: str, font: ImageFont.FreeTypeFont, 
                              text_color: str = "#FFFFFF", outline_color: str = "#000000"):
        """Draw text with subtle outline for better visibility"""
        x, y = position
        
        # Convert colors
        if isinstance(text_color, str):
            text_color = self._hex_to_rgba(text_color, 255)
        if isinstance(outline_color, str):
            outline_color = self._hex_to_rgba(outline_color, 180)  # More transparent outline
        
        # IMPROVED: Thinner, more subtle outline (only 1px instead of 2px)
        for adj in range(1):
            draw.multiline_text((x-1, y-1), text, font=font, fill=outline_color, align='center', spacing=4)
            draw.multiline_text((x+1, y-1), text, font=font, fill=outline_color, align='center', spacing=4)
            draw.multiline_text((x-1, y+1), text, font=font, fill=outline_color, align='center', spacing=4)
            draw.multiline_text((x+1, y+1), text, font=font, fill=outline_color, align='center', spacing=4)
        
        # Draw main text with better spacing
        draw.multiline_text((x, y), text, font=font, fill=text_color, align='center', spacing=4)
    
    def _hex_to_rgba(self, hex_color: str, alpha: int = 255) -> tuple:
        """Convert hex color to RGBA tuple"""
        try:
            hex_color = hex_color.lstrip('#')
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            return (r, g, b, alpha)
        except:
            return (255, 255, 255, alpha)  # Default to white 